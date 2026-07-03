"""Paper Fig. 3 generator: zeta'_850 snapshot montage for the headline run.

Bespoke, paper-styled version of tracker.plot_field_panels:
  - days 1, 4, 6, 9, 12, 15 (no day 0) -> a clean 2 x 3 rectangle
  - a SINGLE tall, thin colorbar on the right (not one per panel)
  - a YELLOW dashed heating-envelope ellipse drawn at SIGMA_MULT sigma
    (tweak SIGMA_MULT below; the run's own dashed line is the 2-sigma contour)
  - bold + enlarged fonts everywhere EXCEPT the colorbar label
    (colorbar TICK labels are bold; the colorbar axis label stays plain)

Run with pangu_env python (paths anchored to repo root):
    /home/pc/.conda/envs/pangu_env/bin/python paper/pic/plot_fig3_panels.py
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from itcz.plotting import tracker
from itcz.plotting.tracker import (
    _discrete, _domain_extent, _make_ax, list_steps, load_pert, step_for_day,
    tcwv_anom, track_max, vort850,
)
from itcz.models.layout import get_layout
from itcz.experiment.forcing import sigmas

# ----------------------------- knobs -----------------------------
RUN = os.path.join(ROOT, "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday")
DAYS = [1, 4, 6, 9, 12, 15]
NCOL = 3
SIGMA_MULT = 1.0        # heating-envelope dashed ellipse drawn at this many sigma
ELLIPSE_COLOR = "green"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig3_panels_vort.png")
# -----------------------------------------------------------------

plt.rcParams.update({
    "font.size": 12,
    "font.weight": "bold",
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "axes.labelweight": "bold",
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
})

def make_panels(run_dir, out, field="vort", ellipse_color=None):
    """Render the paper-styled snapshot montage for one run.

    field: "vort" (850-hPa vorticity) or "tcwv" (column water vapor anomaly).
    ellipse_color: dashed-envelope colour; falls back to the module ELLIPSE_COLOR.
    """
    color = ellipse_color or ELLIPSE_COLOR
    with open(os.path.join(run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    pcfg = cfg["plot"]
    fcfg = cfg["forcing"]
    model = cfg["model"]
    layout = get_layout(model)
    extent = _domain_extent(pcfg)

    if field == "vort":
        title_prefix, cbar_label, scale = "850hPa vort anomaly", r"$\zeta'\times10^{5}$ (s$^{-1}$)", 1e5
        cmap, norm, levels = _discrete("seismic", pcfg["vort_clim"], pcfg.get("vort_step", 1.0))
        ticks = levels[::2]
    else:
        title_prefix, cbar_label, scale = "TCWV anomaly", r"TCWV (kg m$^{-2}$)", 1.0
        cmap, norm, levels = _discrete("BrBG", pcfg["tcwv_clim"], pcfg.get("tcwv_step", 10.0))
        ticks = levels

    # dashed heating-envelope ellipse at SIGMA_MULT sigma about the forcing center
    slat, slon = sigmas(fcfg)
    th = np.linspace(0.0, 2.0 * np.pi, 361)
    elon = (fcfg["center_lon"] + SIGMA_MULT * slon * np.cos(th)) % 360.0
    elat = fcfg["center_lat"] + SIGMA_MULT * slat * np.sin(th)

    nrow = int(np.ceil(len(DAYS) / NCOL))
    fig = plt.figure(figsize=(6.2 * NCOL, 2.0 * nrow))
    avail = set(list_steps(run_dir))
    axes, mesh = [], None
    for k, day in enumerate(DAYS):
        ax = _make_ax(fig, (nrow, NCOL, k + 1), extent)
        axes.append(ax)
        ax.set_title(f"{title_prefix}  day {day}", fontsize=15, fontweight="bold")
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontweight("bold")
        ax.plot(elon, elat, "--", color=color, lw=1.3, transform=ccrs.PlateCarree())
        step = step_for_day(day, cfg["step_hours"])
        if step not in avail:
            ax.text(0.5, 0.5, f"(step {step} missing)", transform=ax.transAxes, ha="center")
            continue
        st = load_pert(run_dir, step, model)
        data = (vort850(st, layout) if field == "vort" else tcwv_anom(st, layout)) * scale
        mesh = ax.pcolormesh(tracker.LON, tracker.LAT, data, cmap=cmap, norm=norm,
                             shading="auto", transform=ccrs.PlateCarree())
        if field == "vort":
            _, vlat, vlon = track_max(vort850(st, layout), pcfg["track_band"])
            ax.plot(vlon, vlat, "kx", ms=7, mew=2, transform=ccrs.PlateCarree())

    fig.subplots_adjust(left=0.04, right=0.90, top=0.90, bottom=0.06, hspace=0.30, wspace=0.10)

    # single tall, thin colorbar aligned to the panel block (needs final bboxes)
    fig.canvas.draw()
    top = axes[NCOL - 1].get_position()          # top-right panel
    bot = axes[-1].get_position()                # bottom-right panel
    cax = fig.add_axes([0.915, bot.y0, 0.008, top.y1 - bot.y0])
    cb = fig.colorbar(mesh, cax=cax, extend="both", ticks=ticks)
    cb.set_label(cbar_label, fontweight="normal", fontsize=11)
    for t in cb.ax.get_yticklabels():
        t.set_fontweight("bold")

    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"[fig] {out}  (SIGMA_MULT={SIGMA_MULT})")


if __name__ == "__main__":
    make_panels(RUN, OUT)
