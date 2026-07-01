"""Per-day single large 2-D anomaly-vorticity maps (same style as ic_vort_pangu.png:
domain 100E-70W, 0-45N, full-res seismic, zeta x 1e5) for visual comparison with the
AI-Forum reference panels. Writes one PNG per (day, sigma) into investigation/figs/2d_maps/.

    python investigation/plot_2d_maps.py <run_dir> [--model pangu] [--days 0 1 4 6 9 12 15] [--sigmas 0 1.5]
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

from itcz.plotting.tracker import LAT, LON, vort850, _make_ax, _discrete, load_pert, list_steps
from itcz.experiment.forcing import ellipse_boundary
from itcz.models.layout import get_layout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--model", default="pangu")
    ap.add_argument("--days", nargs="+", type=float, default=[0, 1, 4, 6, 9, 12, 15])
    ap.add_argument("--sigmas", nargs="+", type=float, default=[0, 1.5])
    ap.add_argument("--domain", nargs=4, type=float, default=[100, 290, 0, 45])
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    layout = get_layout(args.model)
    sh = cfg["step_hours"]
    vclim = cfg["plot"]["vort_clim"]; vstep = cfg["plot"].get("vort_step", 1.0)
    cmap, norm, levels = _discrete("seismic", vclim, vstep)
    lonb, latb = ellipse_boundary(cfg["forcing"])
    avail = set(list_steps(args.run_dir))
    figdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs", "2d_maps")
    os.makedirs(figdir, exist_ok=True)
    tag = os.path.basename(args.run_dir)

    for day in args.days:
        step = int(round(day * 24 / sh))
        if step not in avail:
            print(f"[2d] day {day}: step {step} missing, skip"); continue
        z0 = vort850(load_pert(args.run_dir, step, args.model), layout)
        for s in args.sigmas:
            z = (z0 if s <= 0 else gaussian_filter(z0, sigma=(s, s), mode=("nearest", "wrap"))) * 1e5
            fig = plt.figure(figsize=(11, 4.0))
            ax = _make_ax(fig, (1, 1, 1), list(args.domain))
            ax.plot(lonb, latb, "--", color="orange", lw=1.0, transform=ccrs.PlateCarree())
            mesh = ax.pcolormesh(LON, LAT, z, cmap=cmap, norm=norm, shading="auto",
                                 transform=ccrs.PlateCarree())
            stxt = "raw" if s <= 0 else f"smoothed sigma={s:g} (~{s*0.25:.2f} deg)"
            ax.set_title(f"{tag}\n850 hPa anomaly vorticity  day {day:g}  [{stxt}]", fontsize=10)
            plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02, extend="both", ticks=levels[::2],
                         label=r"$\zeta'\times10^{5}$ (s$^{-1}$)")
            fig.tight_layout()
            out = os.path.join(figdir, f"{tag}_day{day:02g}_s{s:g}.png")
            fig.savefig(out, dpi=130); plt.close(fig)
            print(f"[2d] {out}")


if __name__ == "__main__":
    main()
