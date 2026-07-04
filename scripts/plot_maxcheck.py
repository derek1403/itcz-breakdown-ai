"""QC montage: per-timestep 850-hPa zeta' with the SEEDED TRACKER's chosen vortex
centres marked, so the tracking can be eyeballed. NOT a paper figure.

Every available step gets its own Fig.3-style map panel:
  - coloured stars = tracked vortex centres present that day (colour = branch id,
    consistent across days so you can follow a vortex)
  - lime triangle  = the single band-wide absolute max (track_max), for reference
  - title          = day, number of tracked centres that day

Output -> <run_dir>/tracking/maxcheck_montage.png

    python scripts/plot_maxcheck.py [run_dir] [--band ..] [--peak_min ..]
        [--nbhd_deg ..] [--ow_fact ..] [--d_min ..] [--search_radius ..]
        [--min_len ..] [--keep_zeta ..] [--start_day ..] [--land_buffer ..]
"""
import argparse
import json
import os

import _bootstrap  # noqa: F401  (puts src/ on sys.path)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import track_vortices as TV
from itcz.plotting import tracker as T
from itcz.plotting.tracker import _discrete, _domain_extent, _make_ax
from itcz.models.layout import get_layout

DEFAULT_RUN = "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default=DEFAULT_RUN)
    ap.add_argument("--band", nargs=4, type=float, default=None,
                    metavar=("LATMIN", "LATMAX", "LONMIN", "LONMAX"))
    ap.add_argument("--peak_min", type=float, default=4.0)
    ap.add_argument("--nbhd_deg", type=float, default=6.0)
    ap.add_argument("--ow_fact", type=float, default=0.2)
    ap.add_argument("--d_min", type=float, default=15.0, help="merge cores closer than this (deg)")
    ap.add_argument("--search_radius", type=float, default=12.0)
    ap.add_argument("--min_len", type=int, default=3)
    ap.add_argument("--keep_zeta", type=float, default=6.0)
    ap.add_argument("--start_day", type=float, default=4.0)
    ap.add_argument("--land_buffer", type=float, default=1.5)
    ap.add_argument("--ncol", type=int, default=4)
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    pcfg = cfg["plot"]
    layout = get_layout(cfg["model"])  # noqa: F841 (kept for parity/debug)
    band = args.band or pcfg["track_band"]
    extent = _domain_extent(pcfg)
    cmap, norm, levels = _discrete("seismic", pcfg["vort_clim"], pcfg.get("vort_step", 1.0))

    days, leaves, frames = TV.track_run(
        args.run_dir, cfg, band, peak_min=args.peak_min, nbhd_deg=args.nbhd_deg,
        ow_fact=args.ow_fact, d_min=args.d_min, search_radius=args.search_radius,
        min_len=args.min_len, keep_zeta=args.keep_zeta, start_day=args.start_day,
        land_buffer=args.land_buffer)
    print(f"[qc] {len(leaves)} branches kept")

    # points present on each day, coloured by branch index
    colors = plt.get_cmap("tab10")(np.linspace(0, 1, 10))
    by_day = {}
    for k, tr in enumerate(leaves):
        for p in tr["points"]:
            by_day.setdefault(round(p["day"], 3), []).append((p["lon"], p["lat"], k))

    ncol = args.ncol
    nrow = int(np.ceil(len(frames) / ncol))
    fig = plt.figure(figsize=(5.0 * ncol, 2.3 * nrow))
    axes, mesh = [], None
    for k, fr in enumerate(frames):
        ax = _make_ax(fig, (nrow, ncol, k + 1), extent)
        axes.append(ax)
        mesh = ax.pcolormesh(T.LON, T.LAT, fr["zeta"], cmap=cmap, norm=norm,
                             shading="auto", transform=ccrs.PlateCarree())
        pts = by_day.get(round(fr["day"], 3), [])
        for lon, lat, cid in pts:
            ax.scatter([lon], [lat], marker="*", s=130, c=[colors[cid % 10]],
                       edgecolor="k", linewidths=0.6, zorder=6, transform=ccrs.PlateCarree())
        mlon, mlat, mval = fr["bandmax"]
        ax.plot(mlon, mlat, marker="^", ms=10, mfc="none", mec="lime", mew=1.8,
                zorder=7, transform=ccrs.PlateCarree())
        ax.set_title(f"day {fr['day']:.1f}   tracked={len(pts)}   bandmax={mval:.0f}",
                     fontsize=10)

    fig.subplots_adjust(left=0.03, right=0.92, top=0.95, bottom=0.03, hspace=0.35, wspace=0.10)
    fig.canvas.draw()
    top = axes[ncol - 1].get_position() if len(axes) >= ncol else axes[0].get_position()
    bot = axes[-1].get_position()
    cax = fig.add_axes([0.935, bot.y0, 0.008, top.y1 - bot.y0])
    cb = fig.colorbar(mesh, cax=cax, extend="both", ticks=levels[::2])
    cb.set_label(r"$\zeta'\times10^{5}$ (s$^{-1}$)")

    outdir = os.path.join(args.run_dir, "tracking")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "maxcheck_montage.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[qc] saved {out}  (stars=tracked centres by branch, triangle=band max; "
          f"d_min={args.d_min}, search_radius={args.search_radius}, "
          f"min_len={args.min_len}, ow_fact={args.ow_fact})")


if __name__ == "__main__":
    main()
