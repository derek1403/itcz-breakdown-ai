"""Four vertical-heating-profile comparison of perturbation 850-hPa relative
vorticity -- the field §3.3/§3.4 actually orders (Deep > Shallow > uniform >>
Stratiform).  This is the correct companion to the low-level PV-source theory:
unlike 500-hPa geopotential height (which the deep-column `uniform`/external mode
projects onto most strongly), zeta'_850 shows the low-level vortex strip that the
theory predicts, so the panel ordering matches the table in §3.3.

Source: MAIN pipeline outputs/JAS/pangu24_<ht>_2.5Kday_gauss/step1.
Output -> investigation/figs/hakim/exbl_evolution_Deep_Sha_Uni_Str/
          profiles4_vort850_dayNN.png   (self-identifying; nothing overwritten).

Run:  PY=/home/pc/.conda/envs/pangu_env/bin/python
      $PY aux/investigation/figs/hakim/plot_profiles4_vort850.py
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import warnings
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from itcz import config as cfgmod
from itcz.models.layout import State, get_layout
from itcz.plotting.tracker import relative_vorticity
from itcz.experiment.forcing import LAT, LON, ellipse_boundary
from itcz.experiment.forcing import sigmas

PROFILES = [("Deep", "Deep"), ("Shallow", "Shallow"),
            ("uniform", "uniform (external-mode)"), ("Stratiform", "Stratiform")]
DAYS = range(1, 21)
CLIM = 40.0                      # colorbar limit, 1e-5 s^-1 (shared across panels)
STEP = 4.0
EXTENT = [100, 300, -10, 45]     # Pacific strip view
OUTDIR = os.path.join(HERE, "exbl_evolution_Deep_Sha_Uni_Str")
os.makedirs(OUTDIR, exist_ok=True)

cfg = cfgmod.load_config()
layout = get_layout("pangu")
#elon, elat = ellipse_boundary(cfg["forcing"])
SIGMA_MULT = 1.0        # heating-envelope dashed ellipse drawn at this many sigma
fcfg = cfg["forcing"]
slat, slon = sigmas(fcfg)
th = np.linspace(0.0, 2.0 * np.pi, 361)
elon = (fcfg["center_lon"] + SIGMA_MULT * slon * np.cos(th)) % 360.0
elat = fcfg["center_lat"] + SIGMA_MULT * slat * np.sin(th)


# subset the grid to the plotting domain -> pcolormesh is then fast
jm = (LAT >= EXTENT[2]) & (LAT <= EXTENT[3])
im_ = (LON >= EXTENT[0]) & (LON <= EXTENT[1])
lat_s, lon_s = LAT[jm], LON[im_]

levels = np.arange(-CLIM, CLIM + STEP / 2.0, STEP)
ticks = np.arange(-40, 41, 10)
cmap = plt.get_cmap("seismic")
norm = BoundaryNorm(levels, cmap.N, extend="both")


def vort850(ht, day):
    run = os.path.join(ROOT, "outputs", "JAS", f"pangu24_{ht}_2.5Kday_gauss", "step1")
    st = State.from_npz(os.path.join(run, f"pert_{day:03d}.npz"), "pangu")
    u, v = layout.get_uv(st, 850)
    return relative_vorticity(u, v) * 1e5      # -> units 1e-5 s^-1 (full grid)


proj = ccrs.PlateCarree(central_longitude=180)
for day in DAYS:
    fig, axes = plt.subplots(2, 2, figsize=(15, 7.2),
                             subplot_kw={"projection": proj}, layout="constrained")
    im = None
    for ax, (ht, label) in zip(axes.ravel(), PROFILES):
        z = vort850(ht, day)[np.ix_(jm, im_)]
        im = ax.pcolormesh(lon_s, lat_s, z, cmap=cmap, norm=norm,
                           shading="nearest", transform=ccrs.PlateCarree())
        ax.plot(elon, elat, "--", color='green', linewidth=1.8, transform=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, edgecolor="0.4", linewidth=0.4, facecolor="none", zorder=3)
        ax.coastlines(linewidth=0.5)
        ax.set_extent(EXTENT, crs=ccrs.PlateCarree())
        pk = float(np.nanmax(np.abs(z)))
        ax.set_title(f"{label}   (peak |ζ'| = {pk:.0f})", fontsize=18, fontweight="bold")
    cb = fig.colorbar(im, ax=axes, orientation="horizontal", fraction=0.05, pad=0.03,
                      aspect=65, extend="both", ticks=ticks)
    cb.set_label(r"$\zeta'_{850}$  ($10^{-5}\ \mathrm{s^{-1}}$)", fontweight="normal", fontsize=16)
    for t in cb.ax.get_xticklabels():
        t.set_fontweight("bold")
        t.set_fontsize(14)
    fig.suptitle(f"Perturbation 850-hPa relative vorticity at nominal day {day}"
                 f"   (Gaussian 2.5 K/day)", fontsize=20, fontweight="bold")
    out = os.path.join(OUTDIR, f"profiles4_vort850_day{day:02d}.png")
    fig.savefig(out, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print("saved", out)
print("done")

