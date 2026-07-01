"""Make comparison figures to judge how much of the AI-Forum mismatch is just the
0.25-deg finite-difference diagnostic noise vs genuine dynamics.

Outputs (into investigation/figs/):
  * dayN_sigma_compare.png  -- 850hPa anomaly vorticity at one day, side-by-side for
    several Gaussian-smoothing sigmas (0 = raw FD).
  * timeseries_sigma_compare.png -- band-max vorticity vs day for each sigma, with the
    AI-Forum ~47e-5 peak drawn for reference.

    python investigation/compare_smoothing.py <run_dir> [--model pangu] [--day 12]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter
import cartopy.crs as ccrs

from itcz.plotting.tracker import (LAT, LON, vort850, _make_ax, _discrete,
                                   _domain_extent, load_pert, list_steps, track_max)
from itcz.experiment.forcing import ellipse_boundary
from itcz.models.layout import get_layout

SIGMAS = [0, 1, 2, 3, 6]


def smooth(z, s):
    return z if s <= 0 else gaussian_filter(z, sigma=(s, s), mode=("nearest", "wrap"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--model", default="pangu")
    ap.add_argument("--day", type=int, default=12)
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    pcfg = cfg["plot"]
    layout = get_layout(args.model)
    extent = _domain_extent(pcfg)
    sh = cfg["step_hours"]; band = pcfg["track_band"]
    lonb, latb = ellipse_boundary(cfg["forcing"])
    cmap, norm, levels = _discrete("seismic", pcfg["vort_clim"], pcfg.get("vort_step", 1.0))
    figdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
    os.makedirs(figdir, exist_ok=True)

    # ---- timeseries band-max for each sigma (load each step once) ----
    steps = sorted(list_steps(args.run_dir))
    dd = [s * sh / 24.0 for s in steps]
    series = {s: [] for s in SIGMAS}
    day_vort = None
    day_step = int(round(args.day * 24 / sh))
    for st in steps:
        z = vort850(load_pert(args.run_dir, st, args.model), layout)
        for s in SIGMAS:
            series[s].append(track_max(smooth(z, s), band)[0] * 1e5)
        if st == day_step:
            day_vort = z

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for s in SIGMAS:
        ax.plot(dd, series[s], "-o", ms=2.5, label=("raw FD" if s == 0 else f"smooth sigma={s} (~{s*0.25:.2f} deg)"))
    ax.axhline(47, color="k", ls="--", lw=1.2, label="AI-Forum peak ~47")
    ax.set(title=f"{os.path.basename(args.run_dir)}\nband-max 850hPa vorticity vs smoothing",
           xlabel="day", ylabel=r"max $\zeta'$ (10$^{-5}$ s$^{-1}$)")
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout()
    p_ts = os.path.join(figdir, "timeseries_sigma_compare.png")
    fig.savefig(p_ts, dpi=130); plt.close(fig)
    print(f"[compare] {p_ts}")
    print("[compare] peak by sigma: " + ", ".join(f"s{s}={max(series[s]):.1f}" for s in SIGMAS))

    # ---- day-N panels side by side for each sigma ----
    if day_vort is not None:
        n = len(SIGMAS)
        fig = plt.figure(figsize=(7 * 1, 2.4 * n))
        for k, s in enumerate(SIGMAS):
            ax = _make_ax(fig, (n, 1, k + 1), extent)
            ax.set_title(f"day {args.day}  {'raw FD' if s==0 else f'smoothed sigma={s} (~{s*0.25:.2f} deg)'}", fontsize=9)
            ax.plot(lonb, latb, "--", color="orange", lw=1.0, transform=ccrs.PlateCarree())
            z = smooth(day_vort, s) * 1e5
            mesh = ax.pcolormesh(LON, LAT, z, cmap=cmap, norm=norm, shading="auto", transform=ccrs.PlateCarree())
            cb = fig.colorbar(mesh, ax=ax, ticks=levels[::2], shrink=0.85, pad=0.02, extend="both")
            cb.ax.tick_params(labelsize=7)
        fig.tight_layout()
        p_pan = os.path.join(figdir, f"day{args.day}_sigma_compare.png")
        fig.savefig(p_pan, dpi=120); plt.close(fig)
        print(f"[compare] {p_pan}")


if __name__ == "__main__":
    main()
