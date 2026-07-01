"""Forcing-refinement experiment: test how the paper-vs-ours forcing differences
affect the reproducible statistics (TCWV magnitude, vorticity timeseries shape).
Does NOT touch the main code -- replicates driver math with toggles.

Toggles (vs our current pipeline):
  inject : 'pre'  (current: heating into the INPUT, passes through M)
           'post' (paper:   heating added to the model OUTPUT perturbation, post-M)
  clip   : True (current: clip_moisture on the state fed to M) | False (paper: no clip)
  vert   : 'sin'     (current: Deep sin vertical profile)
           'uniform' (paper:   uniform over levels 1000-250 hPa, i.e. first 9 pangu levels)

Heating stays ON for the first forcing_days (7 d) then OFF (the ITCZ-breakdown design).
Runs each variant (pangu by default), records band-max vorticity & TCWV per step + raw
2-D snapshot fields, and writes comparison figures to investigation/figs/refine/.

    python investigation/refine_forcing.py [--amp 3] [--n_days 16] [--model pangu]
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
from itcz.plotting.tracker import (LAT, LON, vort850, tcwv_anom, _make_ax, _discrete, track_max)
from itcz.experiment.forcing import ellipse_boundary, horizontal_ellipse, sigmas

SNAP_DAYS = [0, 1, 4, 6, 9, 12, 15]
DOMAIN = [100, 290, 0, 45]
# (name, inject, clip, vert) -- default-mode variant list. Currently set to the single
# best (theory-correct) recipe so it can be run on an alternative IC via --background
# (e.g. the smoothed IC paperDJFsm2) and compared to the raw-IC result.
VARIANTS = [
    ("preM_noclip_uniform_smIC2", "pre", False, "uniform"),
]


def build_heating(layout, cfg, vert):
    """Per-step temperature-only heating State with chosen vertical structure."""
    fcfg = cfg["forcing"]
    amp_per_step = fcfg["amp_K_per_day"] * cfg["step_hours"] / 24.0
    slat, slon = sigmas(fcfg)
    h = horizontal_ellipse(fcfg["center_lat"], fcfg["center_lon"], slat, slon)
    lev = np.asarray(layout.levels, dtype=float)
    if vert == "uniform":
        v = np.where((lev >= 250) & (lev <= 1000), 1.0, 0.0)  # paper: uniform levels 1000-250
    else:  # vert is a heat_type: Deep | Stratiform | Shallow (sin-based profiles)
        v = forcing_mod.vertical_profile(vert, lev)
    field = (v[:, None, None] * h[None, :, :]).astype(np.float32)
    f = forcing_mod.zero_state(layout)
    layout.add_temperature(f, amp_per_step * field)
    return f


def run_variant(cfg, op, layout, inject, clip, vert):
    u0 = State.from_npz(cfgmod.ic_path(cfg, cfg["background"], cfg["model"]), cfg["model"])
    f = build_heating(layout, cfg, vert)
    fz = f.zeros_like()
    N, Nf = cfgmod.n_steps(cfg), cfgmod.forcing_steps(cfg)
    sh = cfg["step_hours"]; band = cfg["plot"]["track_band"]
    snap_steps = {int(round(d * 24 / sh)): d for d in SNAP_DAYS}
    B1 = op.step(u0)
    u_prev = u0.zeros_like()
    days, vmax, tmax, snaps = [0.0], [0.0], [0.0], {}
    if 0 in snap_steps:
        snaps[0] = vort850(u_prev, layout) * 1e5
    for n in range(1, N + 1):
        active = n <= Nf
        f_n = f if active else fz
        if inject == "pre":
            A = u0 + u_prev + f_n
            if clip:
                layout.clip_moisture(A)
            u_n = op.step(A) - B1
        else:  # post-M: heating added to the OUTPUT perturbation (temperature)
            A = u0 + u_prev
            if clip:
                layout.clip_moisture(A)
            u_n = op.step(A) - B1 + f_n
        z = vort850(u_n, layout); w = tcwv_anom(u_n, layout)
        days.append(n * sh / 24.0)
        vmax.append(track_max(z, band)[0] * 1e5)
        tmax.append(track_max(w, band)[0])
        if n in snap_steps:
            snaps[n] = z * 1e5
        u_prev = u_n
    return np.array(days), np.array(vmax), np.array(tmax), snaps


def plot_snaps(snaps, cfg, name, figdir):
    cmap, norm, levels = _discrete("seismic", cfg["plot"]["vort_clim"], cfg["plot"].get("vort_step", 1.0))
    lonb, latb = ellipse_boundary(cfg["forcing"])
    steps = sorted(snaps); sh = cfg["step_hours"]
    fig = plt.figure(figsize=(11, 2.2 * len(steps)))
    for k, st in enumerate(steps):
        ax = _make_ax(fig, (len(steps), 1, k + 1), DOMAIN)
        ax.plot(lonb, latb, "--", color="orange", lw=1.0, transform=ccrs.PlateCarree())
        mesh = ax.pcolormesh(LON, LAT, snaps[st], cmap=cmap, norm=norm, shading="auto", transform=ccrs.PlateCarree())
        ax.set_title(f"{name}  day {st*sh/24:g}", fontsize=9)
        plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02, extend="both", ticks=levels[::2])
    fig.tight_layout()
    out = os.path.join(figdir, f"snaps_{name}.png")
    fig.savefig(out, dpi=120); plt.close(fig); print(f"[refine] {out}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amp", type=float, default=3.0)
    ap.add_argument("--paper_amps", nargs="+", type=float, default=None,
                    help="if set, sweep these amps with the paper-faithful variant (post/noclip/uniform)")
    ap.add_argument("--vert_sweep", action="store_true",
                    help="compare 4 vertical heating profiles (Deep/Stratiform/Shallow/uniform), pre-M + no-clip")
    ap.add_argument("--n_days", type=int, default=16)
    ap.add_argument("--model", default="pangu")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--background", default="paperDJF")
    args = ap.parse_args()
    figdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs", "refine")
    os.makedirs(figdir, exist_ok=True)

    # variant list: default 3-toggle comparison, or paper-faithful amplitude sweep
    if args.vert_sweep:
        variants = [(f"preM_noclip_{v}", "pre", False, v, args.amp)
                    for v in ("Deep", "Stratiform", "Shallow", "uniform")]
    elif args.paper_amps:
        variants = [(f"paper_amp{a:g}", "post", False, "uniform", a) for a in args.paper_amps]
    else:
        variants = [(n, i, c, v, args.amp) for (n, i, c, v) in VARIANTS]

    base = cfgmod.load_config({"model": args.model, "device": args.device, "background": args.background,
                               "driver": {"n_days": args.n_days}, "forcing": {"amp_K_per_day": args.amp}})
    layout = get_layout(args.model)
    print(f"[refine] loading {args.model} ...", flush=True)
    op = load_operator(base)

    res = {}
    for name, inject, clip, vert, amp in variants:
        cfg = cfgmod.load_config({"model": args.model, "device": args.device, "background": args.background,
                                  "driver": {"n_days": args.n_days}, "forcing": {"amp_K_per_day": amp}})
        t0 = time.time()
        print(f"\n[refine] === {name} (inject={inject}, clip={clip}, vert={vert}, amp={amp:g}) ===", flush=True)
        d, v, t, snaps = run_variant(cfg, op, layout, inject, clip, vert)
        res[name] = (d, v, t)
        plot_snaps(snaps, cfg, name, figdir)
        print(f"[refine] {name}: vort_peak={v.max():.1f}e-5  tcwv_peak={t.max():.1f}  ({(time.time()-t0)/60:.1f} min)", flush=True)

    # comparison timeseries
    fig, (axv, axt) = plt.subplots(1, 2, figsize=(13, 4.6))
    for name in res:
        d, v, t = res[name]
        axv.plot(d, v, "-o", ms=2.5, label=name)
        axt.plot(d, t, "-o", ms=2.5, label=name)
    axv.axhline(47, color="k", ls="--", lw=1, label="AI-Forum ~47")
    axt.axhline(45, color="k", ls="--", lw=1, label="AI-Forum ~45")
    axv.set(title="band-max 850hPa vorticity", xlabel="day", ylabel=r"max $\zeta'$ (10$^{-5}$ s$^{-1}$)")
    axt.set(title="band-max TCWV anomaly", xlabel="day", ylabel=r"max TCWV (kg m$^{-2}$)")
    for ax in (axv, axt):
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout()
    out = os.path.join(figdir, "compare_refine.png")
    fig.savefig(out, dpi=130); plt.close(fig); print(f"[refine] {out}", flush=True)


if __name__ == "__main__":
    main()
