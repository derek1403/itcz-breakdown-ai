"""QC montage: per-timestep 850-hPa zeta' with the detected regional maxima
marked, so the vortex detection/tracking can be eyeballed. NOT a paper figure.

Every available step gets its own Fig.3-style map panel:
  - yellow stars  = detected local maxima (the candidates detect() feeds to the
    linker in scripts/track_vortices.py), using the SAME parameters
  - lime triangle = the single band-wide absolute maximum (track_max)
  - title         = day, number of detections, peak zeta' (x1e-5)

Output -> <run_dir>/tracking/maxcheck_montage.png

    python scripts/plot_maxcheck.py [run_dir] [--band ..] [--peak_min ..] [--nbhd_deg ..]
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

import track_vortices as TV  # same dir: reuse detect() for consistency
from itcz.plotting import tracker as T
from itcz.plotting.tracker import _discrete, _domain_extent, _make_ax
from itcz.models.layout import get_layout

DEFAULT_RUN = "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default=DEFAULT_RUN)
    ap.add_argument("--band", nargs=4, type=float, default=None,
                    metavar=("LATMIN", "LATMAX", "LONMIN", "LONMAX"))
    ap.add_argument("--peak_min", type=float, default=4.0, help="zeta' threshold (x1e-5)")
    ap.add_argument("--nbhd_deg", type=float, default=6.0, help="min peak separation (deg)")
    ap.add_argument("--ncol", type=int, default=4)
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    pcfg = cfg["plot"]
    model = cfg["model"]
    layout = get_layout(model)
    band = args.band or pcfg["track_band"]
    extent = _domain_extent(pcfg)
    cmap, norm, levels = _discrete("seismic", pcfg["vort_clim"], pcfg.get("vort_step", 1.0))

    steps = T.list_steps(args.run_dir)
    ncol = args.ncol
    nrow = int(np.ceil(len(steps) / ncol))
    fig = plt.figure(figsize=(5.0 * ncol, 2.3 * nrow))
    axes, mesh = [], None
    for k, s in enumerate(steps):
        day = s * cfg["step_hours"] / 24.0
        st = T.load_pert(args.run_dir, s, model)
        zeta = T.vort850(st, layout) * 1e5
        tcwv = np.asarray(T.tcwv_anom(st, layout))
        dets = TV.detect(zeta, tcwv, band, args.peak_min, args.nbhd_deg)
        val, mlat, mlon = T.track_max(T.vort850(st, layout), band)

        ax = _make_ax(fig, (nrow, ncol, k + 1), extent)
        axes.append(ax)
        mesh = ax.pcolormesh(T.LON, T.LAT, zeta, cmap=cmap, norm=norm,
                             shading="auto", transform=ccrs.PlateCarree())
        if dets:
            ax.scatter([d["lon"] for d in dets], [d["lat"] for d in dets], marker="*",
                       s=90, c="yellow", edgecolor="k", linewidths=0.5, zorder=6,
                       transform=ccrs.PlateCarree())
        ax.plot(mlon, mlat, marker="^", ms=10, mfc="none", mec="lime", mew=1.8,
                zorder=7, transform=ccrs.PlateCarree())
        ax.set_title(f"day {day:.1f}   n={len(dets)}   max={val * 1e5:.0f}", fontsize=10)

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
    print(f"[qc] saved {out}  (stars=detected maxima, triangle=band max; "
          f"band={band}, peak_min={args.peak_min}, nbhd_deg={args.nbhd_deg})")


if __name__ == "__main__":
    main()
