"""Paper Fig. 1 generator (restored from a prior session's scratchpad).

Builds the main-pipeline heating distribution + JAS IC panel montage straight
from the ACTUAL src/itcz forcing.py + config.yaml + ic/u0_JAS_pangu.npz that the
run used. Saves the paper's bold-styled Fig. 2 into the HEADLINE spec folder
outputs/JAS/pangu24_Deep_2.5Kday_gauss/heating_dist_check.png (referenced by
methodology.md), plus outputs/JAS/ic_JAS_check.png (Appendix A IC figure).

This is the AUTHORITATIVE (paper-styled) generator for the headline spec's figure.
The OTHER spec folders get an equivalent figure from the reusable, cfg-driven
tracker.plot_heating_dist via `scripts/plot_heating.py --all JAS`.

Run with pangu_env python; paths are anchored to the repo root so cwd does not
matter:
    /home/pc/.conda/envs/pangu_env/bin/python paper/pic/plot_heating_fig1.py

Panel order (Fig. 1): (a) JAS IC TCWV, (b) MAIN heating, (c) Deep vertical,
(d) Meridional cut. All text is bold + enlarged EXCEPT the colorbar text.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from itcz import config as cfgmod
from itcz.experiment import forcing
from itcz.models.layout import get_layout, State

# --- bold + enlarged fonts everywhere (colorbar text is reset to plain below) ---
plt.rcParams.update({
    "font.size": 12,
    "font.weight": "bold",
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "axes.labelweight": "bold",
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
})

cfg = cfgmod.load_config()
fcfg = cfg["forcing"]
amp = fcfg["amp_K_per_day"]
ht = fcfg["heat_type"]
lay = get_layout("pangu")
levels = np.asarray(lay.levels, dtype=float)
LAT, LON = forcing.LAT, forcing.LON

# --- horizontal shape + vertical profile straight from src/itcz/forcing.py ---
slat, slon = forcing.sigmas(fcfg)
shape2d = forcing.horizontal_ellipse(fcfg["center_lat"], fcfg["center_lon"], slat, slon)
vprof = forcing.vertical_profile(ht, levels)
ylat, xlon = fcfg["center_lat"], fcfg["center_lon"]
jlat = int(np.argmin(np.abs(LAT - ylat)))
ilon = int(np.argmin(np.abs(LON - xlon)))

# --- JAS IC fields ---
st = State.from_npz(os.path.join(ROOT, "ic/u0_JAS_pangu.npz"), "pangu")
tcwv_ic = np.asarray(lay.tcwv(st))
i850 = list(lay.levels).index(850)
u850 = st.arrays["upper"][lay.U, i850]
v850 = st.arrays["upper"][lay.V, i850]

PROJ = ccrs.PlateCarree(central_longitude=180)
DATA = ccrs.PlateCarree()
tlev = np.arange(0, 75, 5)
_tc = plt.get_cmap("turbo")(np.linspace(0, 1, len(tlev) - 1)); _tc[0] = (1, 1, 1, 1)
CMAP_T = ListedColormap(_tc); CMAP_T.set_over(plt.get_cmap("turbo")(1.0))
NORM_T = BoundaryNorm(tlev, CMAP_T.N)


def add_map(ax):
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6); ax.set_global()
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="0.5", alpha=0.5)
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = {"weight": "bold", "size": 11}
    gl.ylabel_style = {"weight": "bold", "size": 11}


def map_cbar(im, ax, label, **kw):
    """Horizontal colorbar as long as the map, with PLAIN (non-bold) text."""
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", shrink=1.0, pad=0.08, **kw)
    cb.set_label(label, fontweight="normal", fontsize=10)
    for t in cb.ax.get_xticklabels():
        t.set_fontweight("bold"); t.set_fontsize(9) # 把 "normal" 改成 "bold"
    return cb


os.makedirs(os.path.join(ROOT, "outputs/JAS"), exist_ok=True)

# =============== Fig 1: heating distribution ===============
fig = plt.figure(figsize=(16, 9))

# (a) JAS IC TCWV  (with heating extent overlaid)
ax1 = fig.add_subplot(2, 2, 1, projection=PROJ)
im1 = ax1.pcolormesh(LON, LAT, tcwv_ic, cmap=CMAP_T, norm=NORM_T, shading="auto", transform=DATA)
ax1.contour(LON, LAT, shape2d, levels=[0.25, 0.6], colors="k", linewidths=0.8, transform=DATA)
add_map(ax1)
ax1.set_title("(a) JAS IC: TCWV (black = heating 0.25/0.6 contour)", fontsize=12)
map_cbar(im1, ax1, "TCWV (kg m$^{-2}$)", ticks=tlev, extend="max", aspect=40)

# (b) MAIN-pipeline heating
ax2 = fig.add_subplot(2, 2, 2, projection=PROJ)
hlev = np.arange(0, amp + 0.25, 0.25)
hnorm = BoundaryNorm(hlev, plt.get_cmap("Reds").N, clip=False, extend="max")
im2 = ax2.pcolormesh(LON, LAT, amp * shape2d, cmap="Reds", norm=hnorm, shading="auto", transform=DATA)
add_map(ax2)
ax2.set_title(f"(b) MAIN-pipeline heating ({amp} K/day, center {ylat:.0f}N/{xlon:.0f}E, "
              f"sig {slat:.1f}/{slon:.1f} deg)", fontsize=12)
map_cbar(im2, ax2, "heating (K/day)", ticks=hlev , aspect=40)

# (c) Deep vertical profile
ax3 = fig.add_subplot(2, 2, 3)
ax3.plot(vprof, levels, "o-"); ax3.invert_yaxis()
ax3.set_title(f"(c) {ht} vertical profile"); ax3.set_xlabel("unit heating")
ax3.set_ylabel("pressure (hPa)"); ax3.grid(True, alpha=0.3)

# (d) Meridional cut
ax4 = fig.add_subplot(2, 2, 4)
ax4.plot(LAT, shape2d[:, ilon], "-")
ax4.axvline(ylat, color="g", ls=":", lw=1); ax4.axvline(0, color="0.6", lw=0.6)
ax4.set_xlim(-20, 40)
ax4.set_title(f"(d) Meridional cut @ {xlon:.0f}E (sig_lat={slat:.1f} deg, center {ylat:.0f}N)")
ax4.set_xlabel("lat (deg)"); ax4.set_ylabel("unit heating"); ax4.grid(True, alpha=0.3)

fig.tight_layout()
_fig2 = "outputs/JAS/pangu24_Deep_2.5Kday_gauss/heating_dist_check.png"   # headline spec folder
os.makedirs(os.path.dirname(os.path.join(ROOT, _fig2)), exist_ok=True)
fig.savefig(os.path.join(ROOT, _fig2), dpi=120)
print(f"saved {_fig2}")

# =============== Fig 2: JAS IC (TCWV + 850 wind) — unchanged ===============
fig2 = plt.figure(figsize=(11, 6))
axi = fig2.add_subplot(1, 1, 1, projection=PROJ)
imi = axi.pcolormesh(LON, LAT, tcwv_ic, cmap=CMAP_T, norm=NORM_T, shading="auto", transform=DATA)
stq = 22
q = axi.quiver(LON[::stq], LAT[::stq], u850[::stq, ::stq], v850[::stq, ::stq],
               transform=DATA, scale=400, width=0.0015, color="k")
axi.quiverkey(q, 0.9, 1.03, 10, "10 m/s", labelpos="E")
add_map(axi)
axi.set_title("JAS climatology mean state (TCWV + 850 hPa wind) — main pipeline IC")
cb2 = fig2.colorbar(imi, ax=axi, shrink=0.7, ticks=tlev, extend="max")
cb2.set_label("TCWV (kg m$^{-2}$)", fontweight="normal", fontsize=10)
for t in cb2.ax.get_yticklabels():
    t.set_fontweight("normal"); t.set_fontsize(9)
fig2.tight_layout()
fig2.savefig(os.path.join(ROOT, "outputs/JAS/ic_JAS_check.png"), dpi=130)
print("saved outputs/JAS/ic_JAS_check.png")

# --- text checks ---
nz = shape2d[:, ilon] > 1e-3
print("lat extent shape>1e-3:", float(LAT[nz].min()), "to", float(LAT[nz].max()), "N")
nzl = shape2d[jlat, :] > 1e-3
print("lon extent shape>1e-3:", float(LON[nzl].min()), "to", float(LON[nzl].max()), "E")
print(f"IC TCWV @({ylat:.0f}N,{xlon:.0f}E) = {tcwv_ic[jlat, ilon]:.1f} kg/m2")
print(f"sigma_lat={slat}, sigma_lon={slon}, amp={amp}, heat_type={ht}, background={cfg['background']}")
