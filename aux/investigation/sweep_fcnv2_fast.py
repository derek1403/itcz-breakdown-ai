"""FAST fcnv2(GPU) heating-amplitude sweep for diagnosis.

Replicates driver.run's math but does NOT save 182MB full-state npz each step (that
IO was the ~53s/step bottleneck). Instead it computes vort850 band-max every step and
stores only the 2-D vorticity field on the AI-Forum snapshot days. Produces, evaluated
RAW (no smoothing, per user's read that AI-Forum is unsmoothed):
  * figs/sweep/vort_panels_{amp}Kday.png  -- stacked raw 2-D vort maps (snapshot days)
  * figs/sweep/timeseries_amps.png        -- raw band-max vorticity vs day, all amps,
    with the AI-Forum ~47e-5 peak line.

    python investigation/sweep_fcnv2_fast.py [--amps 0.1 0.5 1 2] [--n_days 16]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs

from itcz import config as cfgmod
from itcz.experiment import forcing as forcing_mod
from itcz.models.layout import State, get_layout
from itcz.models.operators import load_operator
from itcz.plotting.tracker import (LAT, LON, vort850, _make_ax, _discrete, track_max)
from itcz.experiment.forcing import ellipse_boundary

SNAP_DAYS = [0, 1, 4, 6, 9, 12, 15]
DOMAIN = [100, 290, 0, 45]


def run_one(cfg, op, layout, amp):
    u0 = State.from_npz(cfgmod.ic_path(cfg, cfg["background"], cfg["model"]), cfg["model"])
    f_base = forcing_mod.heating_forcing(layout, cfg)
    N, Nf = cfgmod.n_steps(cfg), cfgmod.forcing_steps(cfg)
    sh = cfg["step_hours"]; band = cfg["plot"]["track_band"]
    snap_steps = {int(round(d * 24 / sh)): d for d in SNAP_DAYS}

    B1 = op.step(u0)
    u_prev = u0.zeros_like()
    days, vmax, snaps = [0.0], [0.0], {}
    if 0 in snap_steps:
        snaps[0] = vort850(u_prev, layout) * 1e5
    for n in range(1, N + 1):
        f_n = f_base if n <= Nf else f_base.zeros_like()
        A = u0 + u_prev + f_n
        layout.clip_moisture(A)
        u_n = op.step(A) - B1
        z = vort850(u_n, layout)
        days.append(n * sh / 24.0)
        vmax.append(track_max(z, band)[0] * 1e5)
        if n in snap_steps:
            snaps[n] = z * 1e5
        u_prev = u_n
    return np.array(days), np.array(vmax), snaps


def plot_panels(snaps, cfg, amp, figdir):
    cmap, norm, levels = _discrete("seismic", cfg["plot"]["vort_clim"], cfg["plot"].get("vort_step", 1.0))
    lonb, latb = ellipse_boundary(cfg["forcing"])
    steps = sorted(snaps)
    nrow = len(steps)
    fig = plt.figure(figsize=(11, 2.2 * nrow))
    sh = cfg["step_hours"]
    for k, st in enumerate(steps):
        ax = _make_ax(fig, (nrow, 1, k + 1), DOMAIN)
        ax.plot(lonb, latb, "--", color="orange", lw=1.0, transform=ccrs.PlateCarree())
        mesh = ax.pcolormesh(LON, LAT, snaps[st], cmap=cmap, norm=norm, shading="auto",
                             transform=ccrs.PlateCarree())
        ax.set_title(f"day {st*sh/24:g}  (amp={amp:g} K/day, raw)", fontsize=9)
        plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02, extend="both", ticks=levels[::2])
    fig.tight_layout()
    out = os.path.join(figdir, f"vort_panels_{amp:g}Kday.png")
    fig.savefig(out, dpi=120); plt.close(fig)
    print(f"[fast] {out}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amps", nargs="+", type=float, default=[0.1, 0.5, 1.0, 2.0])
    ap.add_argument("--n_days", type=int, default=16)
    ap.add_argument("--model", default="fcnv2")
    ap.add_argument("--background", default="paperDJF")
    ap.add_argument("--heat_type", default="Deep")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    figdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs", "sweep", args.model)
    os.makedirs(figdir, exist_ok=True)
    base = cfgmod.load_config({"model": args.model, "device": args.device, "background": args.background,
                               "driver": {"n_days": args.n_days}, "forcing": {"heat_type": args.heat_type}})
    layout = get_layout(args.model)
    print(f"[fast] loading {args.model} on {args.device} ...", flush=True)
    op = load_operator(base)

    ts = {}
    for amp in args.amps:
        cfg = cfgmod.load_config({"model": args.model, "device": args.device, "background": args.background,
                                  "driver": {"n_days": args.n_days},
                                  "forcing": {"amp_K_per_day": amp, "heat_type": args.heat_type}})
        cfg["experiment"] = {"name": f"fast_{args.model}_{args.background}_{args.heat_type}_{amp:g}Kday",
                             "forcing_type": "heating", "persistent": False, "lock": "none", "seed_npz": None}
        t0 = time.time()
        print(f"\n[fast] === amp={amp:g} K/day ===", flush=True)
        days, vmax, snaps = run_one(cfg, op, layout, amp)
        ts[amp] = (days, vmax)
        plot_panels(snaps, cfg, amp, figdir)
        print(f"[fast] amp={amp:g}: peak={vmax.max():.1f}e-5  ({(time.time()-t0)/60:.1f} min)", flush=True)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for amp in args.amps:
        d, v = ts[amp]
        ax.plot(d, v, "-o", ms=2.5, label=f"amp={amp:g} K/day")
    ax.axhline(47, color="k", ls="--", lw=1.2, label="AI-Forum peak ~47")
    ax.set(title="fcnv2 paperDJF Step1: raw band-max 850hPa vorticity vs heating amplitude",
           xlabel="day", ylabel=r"max $\zeta'$ (10$^{-5}$ s$^{-1}$)")
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout()
    out = os.path.join(figdir, "timeseries_amps.png")
    fig.savefig(out, dpi=130); plt.close(fig)
    print(f"[fast] {out}", flush=True)


if __name__ == "__main__":
    main()
