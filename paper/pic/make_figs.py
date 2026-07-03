"""Paper composite figures. Run from repo root with pangu_env python:

    PY=/home/pc/.conda/envs/pangu_env/bin/python
    $PY paper/pic/make_figs.py fig5        # JAS vs DJF seasonal timeseries overlay
    $PY paper/pic/make_figs.py fig7        # Steps 1-4 overlay timeseries
    $PY paper/pic/make_figs.py fig8        # 6h vs 24h same-day side-by-side maps
    $PY paper/pic/make_figs.py fig9        # model-vs-obs montage (money figure)
    $PY paper/pic/make_figs.py schematic   # method schematic

Outputs land in paper/pic/. Each figure reads pert_NNN.npz through the
project's own tracker/layout code, honouring each run's config_used.json.
"""
import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
OUT = os.path.dirname(os.path.abspath(__file__))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from itcz.models.layout import get_layout
from itcz.plotting import tracker

RUN_24H = os.path.join(ROOT, "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday")
RUN_6H = os.path.join(ROOT, "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday_6h_sustained")
RUN_6H_FALLBACK = os.path.join(ROOT, "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday_6h_pulse7d")
RUN_DJF = os.path.join(ROOT, "outputs/DJF/step1_pangu_DJF_Deep_2.5Kday")
OBS_DIR = os.path.join(ROOT, "obs/2024-11_WPac_quad-typhoon/fulldisk")
CROP = (120, 280, 820, 575)  # tropical-WPac crop on the 1024^2 full disk (obs/README)


def run_cfg(run_dir):
    with open(os.path.join(run_dir, "config_used.json")) as fh:
        return json.load(fh)


def run_series(run_dir):
    """(days, vort_max, tcwv_max) using the run's OWN step_hours."""
    return tracker.timeseries(run_dir, run_cfg(run_dir))


def _vort_map(ax, run_dir, day, title):
    import cartopy.crs as ccrs
    cfg = run_cfg(run_dir)
    step = tracker.step_for_day(day, cfg["step_hours"])
    st = tracker.load_pert(run_dir, step, cfg["model"])
    z = tracker.vort850(st, get_layout(cfg["model"])) * 1e5
    im = ax.pcolormesh(tracker.LON, tracker.LAT, z, cmap="seismic",
                       vmin=-10, vmax=10, transform=ccrs.PlateCarree(), rasterized=True)
    ax.coastlines(linewidth=0.5)
    ax.set_extent([115, 205, 0, 35], crs=ccrs.PlateCarree())
    ax.set_title(title, fontsize=10)
    return im


# ---------------------------------------------------------------- fig5 / fig7
def overlay(run_dirs, labels, out, suptitle):
    fig, (axv, axt) = plt.subplots(1, 2, figsize=(11, 4.2))
    for rd, lab in zip(run_dirs, labels):
        if not os.path.isdir(rd):
            print(f"[skip] {rd} missing"); continue
        d, vm, tm = run_series(rd)
        axv.plot(d, vm * 1e5, "-o", ms=3, label=lab)
        axt.plot(d, tm, "-o", ms=3, label=lab)
    axv.set(xlabel="iteration n (nominal day)", ylabel=r"peak $\zeta'_{850}$ ($10^{-5}$ s$^{-1}$)")
    axt.set(xlabel="iteration n (nominal day)", ylabel=r"peak TCWV$'$ (kg m$^{-2}$)")
    for ax in (axv, axt):
        ax.grid(alpha=0.3); ax.legend(fontsize=9)
    fig.suptitle(suptitle, fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out, dpi=150); plt.close(fig)
    print(f"[fig] {out}")


def fig5():
    overlay([RUN_24H, RUN_DJF], ["JAS background", "DJF background"],
            os.path.join(OUT, "fig5_seasonal_timeseries.png"),
            "Seasonal control: identical Gaussian Deep 2.5 K/day forcing")


def fig7():
    runs = [RUN_24H,
            os.path.join(ROOT, "outputs/JAS/step2_pangu_JAS_Deep_2.5Kday_moistlock"),
            os.path.join(ROOT, "outputs/JAS/step3_pangu_JAS_moistinit_d7"),
            os.path.join(ROOT, "outputs/JAS/step4_pangu_JAS_windlock")]
    labels = ["Step 1: standard", "Step 2: moisture-locked",
              "Step 3: moisture-only init", "Step 4: wind-locked"]
    overlay(runs, labels, os.path.join(OUT, "fig7_steps_overlay.png"),
            "Mechanism denial: the four-step suite (Pangu, JAS, 24-h)")


# ---------------------------------------------------------------------- fig8
def fig8(day=12):
    import cartopy.crs as ccrs
    import matplotlib.ticker as mticker
    run6 = RUN_6H if os.path.isdir(RUN_6H) else RUN_6H_FALLBACK
    tag6 = "6-h operator" + ("" if run6 == RUN_6H else " (7-day pulse run)")
    fig = plt.figure(figsize=(13, 3.6))
    for i, (rd, tt) in enumerate([(RUN_24H, "24-h operator"), (run6, tag6)]):
        ax = fig.add_subplot(1, 2, i + 1, projection=ccrs.PlateCarree(central_longitude=180))
        im = _vort_map(ax, rd, day, f"{tt} — nominal day {day}")
        ax.set_title(f"{tt} — nominal day {day}", fontsize=10, fontweight="bold")
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="gray",
                          alpha=0.4, linestyle="--")
        gl.top_labels = gl.right_labels = False
        gl.xlocator = mticker.FixedLocator([120, 150, 180, 210])  # lon every 30 deg
        gl.ylocator = mticker.FixedLocator([0, 10, 20, 30])       # lat every 10 deg
        gl.xlabel_style = {"size": 8, "weight": "bold"}
        gl.ylabel_style = {"size": 8, "weight": "bold"}
    cb = fig.colorbar(im, ax=fig.axes, shrink=0.85, pad=0.02, extend="both")
    cb.set_label(r"$\zeta'_{850}$ ($10^{-5}$ s$^{-1}$)")
    fig.savefig(os.path.join(OUT, "fig8_6h_vs_24h_day12.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] fig8_6h_vs_24h_day12.png  (6-h source: {run6})")


# Enhanced-IR brightness-temperature colour table (ref: paper/FTR/IR_colorbar.png),
# capped at -110 C. Equal-width segments between successive boundary temperatures.
IR_TEMPS = [28, 0, -20, -31, -42, -53, -63, -80, -110]  # warm -> cold, deg C
_IR_SEGS = [                       # (colour at warm edge, colour at cold edge) per bin
    ((0, 0, 0), (0, 0, 1)),        #  28 ..   0  black -> blue
    ((0, 0.7, 0), (0, 0.7, 0)),    #   0 .. -20  green
    ((1, 1, 0), (1, 1, 0)),        # -20 .. -31  yellow
    ((1, 0, 0), (1, 0, 0)),        # -31 .. -42  red
    ((1, 1, 1), (1, 1, 1)),        # -42 .. -53  white
    ((0, 0, 0), (0, 0, 0)),        # -53 .. -63  black
    ((1, 0, 1), (1, 1, 1)),        # -63 .. -80  magenta -> white
    ((1, 1, 1), (1, 1, 1)),        # -80 ..-110  white
]


def _ir_cmap(n=256):
    from matplotlib.colors import ListedColormap
    nb = len(_IR_SEGS)
    cols = []
    for i in range(n):
        p = i / (n - 1) * nb           # position in units of bins (0..nb)
        b = min(int(p), nb - 1)
        t = p - b                      # fraction within bin
        c0, c1 = _IR_SEGS[b]
        cols.append([c0[k] + (c1[k] - c0[k]) * t for k in range(3)])
    return ListedColormap(cols)


# ---------------------------------------------------------------------- fig9
def fig9():
    import cartopy.crs as ccrs
    from PIL import Image
    model_days = [6, 9, 12, 15]
    obs_dates = ["20241107", "20241109", "20241111", "20241113"]
    fig = plt.figure(figsize=(16, 4.0))
    im = None
    top_ax = None
    for i, day in enumerate(model_days):
        ax = fig.add_subplot(2, 4, i + 1, projection=ccrs.PlateCarree(central_longitude=180))
        im = _vort_map(ax, RUN_24H, day, f"model iteration {day} (nominal day)")
        ax.set_title(f"model iteration {day} (nominal day)", fontsize=10, fontweight="bold")
        top_ax = ax
    bot_ax = None
    for i, date in enumerate(obs_dates):
        ax = fig.add_subplot(2, 4, 5 + i)
        img = Image.open(os.path.join(OBS_DIR, f"{date}_00Z_ir.jpg")).crop(CROP)
        ax.imshow(img)
        ax.set_title(f"Himawari IR  {date[:4]}-{date[4:6]}-{date[6:]} 00Z",
                     fontsize=10, fontweight="bold")
        ax.axis("off")
        bot_ax = ax
    fig.subplots_adjust(left=0.02, right=0.90, top=0.89, bottom=0.02, hspace=0.20, wspace=0.08)
    # colorbars: thin and vertically aligned with their rows (need final axes bbox)
    fig.canvas.draw()
    pos1 = top_ax.get_position()
    cax = fig.add_axes([0.915, pos1.y0, 0.006, pos1.height])
    cb = fig.colorbar(im, cax=cax, extend="both")
    cb.set_label(r"$\zeta'_{850}$ ($10^{-5}$ s$^{-1}$)", fontsize=9, fontweight="bold")
    for t in cb.ax.get_yticklabels():
        t.set_fontweight("bold")
    # IR brightness-temperature colorbar for the Himawari row
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    nb = len(_IR_SEGS)
    pos2 = bot_ax.get_position()
    cax2 = fig.add_axes([0.915, pos2.y0, 0.006, pos2.height])
    sm = ScalarMappable(norm=Normalize(0, nb), cmap=_ir_cmap())
    cb2 = fig.colorbar(sm, cax=cax2)
    cb2.set_ticks(list(range(nb + 1)))
    cb2.set_ticklabels([str(t) for t in IR_TEMPS])
    cb2.set_label(r"IR brightness $T_b$ ($^\circ$C)", fontsize=9, fontweight="bold")
    for t in cb2.ax.get_yticklabels():
        t.set_fontweight("bold")
    fig.suptitle("Modeled mode extraction (top; frozen JAS background) vs. observed "
                 "November 2024 monsoon-trough breakdown (bottom; true time evolution)",
                 fontsize=12, fontweight="bold", y=0.98)
    fig.savefig(os.path.join(OUT, "fig9_model_vs_obs.png"), dpi=150)
    plt.close(fig)
    print("[fig] fig9_model_vs_obs.png")


# ----------------------------------------------------------------- schematic
def schematic():
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.axis("off")
    box = dict(boxstyle="round,pad=0.45", fc="#eef3fb", ec="#3b6ea5", lw=1.4)
    opb = dict(boxstyle="round,pad=0.45", fc="#fdf0e7", ec="#c96a2b", lw=1.4)
    ax.text(0.08, 0.78, "steady background\n$u_0$ (JAS climatology)", ha="center", bbox=box, fontsize=10)
    ax.text(0.08, 0.30, "forcing $f_n$\n(heating increment)", ha="center", bbox=box, fontsize=10)
    ax.text(0.38, 0.54, "assemble\n$A_n = u_0 + u'_{n-1} + f_n$", ha="center", bbox=box, fontsize=10)
    ax.text(0.63, 0.54, "model step\n$M(A_n)$", ha="center", bbox=opb, fontsize=11)
    ax.text(0.88, 0.54, "peel drift\n$u'_n = M(A_n) - B$\n$B \\equiv M(u_0)$", ha="center", bbox=box, fontsize=10)
    for xy, xytext in [((0.30, 0.60), (0.15, 0.75)), ((0.30, 0.49), (0.15, 0.33)),
                       ((0.55, 0.54), (0.46, 0.54)), ((0.79, 0.54), (0.70, 0.54))]:
        ax.annotate("", xy=xy, xytext=xytext, arrowprops=dict(arrowstyle="->", lw=1.4))
    ax.annotate("$u'_n$ fed back  (background re-anchored to $u_0$ every step)",
                xy=(0.38, 0.42), xytext=(0.88, 0.30), ha="center", fontsize=10,
                arrowprops=dict(arrowstyle="->", lw=1.4, connectionstyle="arc3,rad=0.35"))
    ax.text(0.5, 0.06,
            "background never leaves $t=0$  $\\Rightarrow$  forced power iteration: "
            "$n$ counts mode-extraction convergence, not physical time",
            ha="center", fontsize=10, style="italic")
    fig.savefig(os.path.join(OUT, "fig_method_schematic.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[fig] fig_method_schematic.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["fig5", "fig7", "fig8", "fig9", "schematic", "all"])
    args = ap.parse_args()
    todo = ["fig5", "fig7", "fig8", "fig9", "schematic"] if args.which == "all" else [args.which]
    for name in todo:
        try:
            globals()[name]()
        except Exception as e:
            print(f"[ERR] {name}: {e}")
