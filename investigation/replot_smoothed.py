"""Zero-compute diagnostic test (hypothesis #2): re-plot an EXISTING run's 850-hPa
anomaly vorticity with spatial smoothing, to see whether the mismatch vs the
AI-Forum reference is just grid-scale finite-difference noise (0.25 deg np.gradient
+ band-max) or genuine excess mid-latitude activity.

Loads pert_*.npz from a run dir, computes zeta' = vort850(u',v'), optionally
Gaussian-smooths it (lon-wrap aware), and writes:
  * panels_vort_smoothed_s{SIGMA}.png  -- snapshot-day panels (smoothed)
  * timeseries_smoothing_s{SIGMA}.png  -- band-max vorticity: raw vs smoothed,
    with the AI-Forum ~47e-5 peak drawn for reference.

    python investigation/replot_smoothed.py <run_dir> [--model pangu] [--sigma 6]
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
from itcz.plotting import tracker
from itcz.plotting.tracker import (LAT, LON, vort850, _make_ax, _discrete,
                                   _domain_extent, load_pert, list_steps, track_max)
from itcz.experiment.forcing import ellipse_boundary
from itcz.models.layout import get_layout


def smooth_lonwrap(field2d, sigma):
    """Gaussian smooth; wrap in longitude (axis=1), reflect in latitude (axis=0)."""
    if sigma <= 0:
        return field2d
    return gaussian_filter(field2d, sigma=(sigma, sigma), mode=("nearest", "wrap"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--model", default="pangu")
    ap.add_argument("--sigma", type=float, default=6.0, help="smoothing sigma in grid pts (~0.25 deg each)")
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    pcfg = cfg["plot"]
    layout = get_layout(args.model)
    extent = _domain_extent(pcfg)
    days = pcfg["snapshot_days"]
    step_hours = cfg["step_hours"]
    band = pcfg["track_band"]
    lonb, latb = ellipse_boundary(cfg["forcing"])
    cmap, norm, levels = _discrete("seismic", pcfg["vort_clim"], pcfg.get("vort_step", 1.0))
    ticks = levels[::2]

    # ---- panels (smoothed) ----
    ncol = 2
    nrow = int(np.ceil(len(days) / ncol))
    fig = plt.figure(figsize=(7 * ncol, 2.6 * nrow))
    avail = set(list_steps(args.run_dir))
    for k, day in enumerate(days):
        step = int(round(day * 24 / step_hours))
        ax = _make_ax(fig, (nrow, ncol, k + 1), extent)
        ax.set_title(f"850hPa vort anomaly (smoothed sigma={args.sigma:g})  day {day}", fontsize=9)
        ax.plot(lonb, latb, "--", color="orange", lw=1.0, transform=ccrs.PlateCarree())
        if step not in avail:
            ax.text(0.5, 0.5, f"(step {step} missing)", transform=ax.transAxes, ha="center"); continue
        st = load_pert(args.run_dir, step, args.model)
        z = smooth_lonwrap(vort850(st, layout), args.sigma) * 1e5
        mesh = ax.pcolormesh(LON, LAT, z, cmap=cmap, norm=norm, shading="auto", transform=ccrs.PlateCarree())
        cb = fig.colorbar(mesh, ax=ax, ticks=ticks, shrink=0.85, pad=0.02, extend="both")
        cb.ax.tick_params(labelsize=7)
    fig.tight_layout()
    p1 = os.path.join(args.run_dir, f"panels_vort_smoothed_s{args.sigma:g}.png")
    fig.savefig(p1, dpi=120); plt.close(fig)
    print(f"[replot] {p1}")

    # ---- timeseries: raw vs smoothed band-max ----
    steps = sorted(avail)
    dd, raw, smo = [], [], []
    for step in steps:
        st = load_pert(args.run_dir, step, args.model)
        z = vort850(st, layout)
        dd.append(step * step_hours / 24.0)
        raw.append(track_max(z, band)[0] * 1e5)
        smo.append(track_max(smooth_lonwrap(z, args.sigma), band)[0] * 1e5)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(dd, raw, "-o", ms=3, label="raw (0.25 deg FD)")
    ax.plot(dd, smo, "-o", ms=3, label=f"smoothed sigma={args.sigma:g}")
    ax.axhline(47, color="gray", ls="--", lw=1, label="AI-Forum peak ~47")
    ax.set(title=f"{os.path.basename(args.run_dir)}: band-max 850hPa vorticity",
           xlabel="day", ylabel=r"max $\zeta'$ (10$^{-5}$ s$^{-1}$)")
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout()
    p2 = os.path.join(args.run_dir, f"timeseries_smoothing_s{args.sigma:g}.png")
    fig.savefig(p2, dpi=130); plt.close(fig)
    print(f"[replot] {p2}")
    print(f"[replot] raw peak={max(raw):.1f}  smoothed peak={max(smo):.1f} (x1e-5 s^-1)")


if __name__ == "__main__":
    main()
