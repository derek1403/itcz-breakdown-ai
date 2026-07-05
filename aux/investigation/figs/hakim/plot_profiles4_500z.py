"""Four vertical-heating-profile comparison of perturbation 500-hPa geopotential
height, from the MAIN pipeline (outputs/JAS/pangu24_<ht>_2.5Kday_gauss/step1).

Replaces the old EX/BL Fig. 6 (kept, renamed exbl_evolution_EX_BL/) with the four
profiles that §3.3/§3.4 actually order:  Deep, Shallow, uniform(=external-mode /
boundary-only case), Stratiform.  One amplitude (2.5 K/day), one shared contour
interval across all four panels so the amplitude ordering is read directly.

Output -> investigation/figs/hakim/exbl_evolution_Deep_Sha_Uni_Str/
          profiles4_500z_dayNN.png   (self-identifying names; nothing overwritten).

Run:  PY=/home/pc/.conda/envs/pangu_env/bin/python
      $PY aux/investigation/figs/hakim/plot_profiles4_500z.py
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import warnings
warnings.filterwarnings("ignore")

# --- bootstrap the itcz package (repo_root/src) ----------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))   # -> itcz-breakdown-ai
sys.path.insert(0, os.path.join(ROOT, "src"))

from itcz import config as cfgmod
from itcz.models.layout import State, get_layout, G
from itcz.experiment.forcing import LAT, LON, ellipse_boundary
from itcz.experiment.forcing import sigmas

# 2x2 order: strong pair on top, boundary-only + cooling on the bottom.
PROFILES = [("Deep", "Deep"), ("Shallow", "Shallow"),
            ("uniform", "uniform (external-mode)"), ("Stratiform", "Stratiform")]
DAYS = range(1, 21)                      # 24-h operator -> pert_0NN.npz == day NN
REF_DAY = 12                             # day used to set the shared contour interval
OUTDIR = os.path.join(HERE, "exbl_evolution_Deep_Sha_Uni_Str")
os.makedirs(OUTDIR, exist_ok=True)

cfg = cfgmod.load_config()
layout = get_layout("pangu")
k500 = layout.level_index(500)

# base-state 500-hPa height for the grey background contours
u0 = State.from_npz(cfgmod.ic_path(cfg, "JAS", "pangu"), "pangu")
base500 = u0.arrays["upper"][layout.Z, k500] / G

# heating footprint (dashed ellipse) from the shared forcing geometry
#elon, elat = ellipse_boundary(cfg["forcing"])

SIGMA_MULT = 1.0        # heating-envelope dashed ellipse drawn at this many sigma
fcfg = cfg["forcing"]
slat, slon = sigmas(fcfg)
th = np.linspace(0.0, 2.0 * np.pi, 361)
elon = (fcfg["center_lon"] + SIGMA_MULT * slon * np.cos(th)) % 360.0
elat = fcfg["center_lat"] + SIGMA_MULT * slat * np.sin(th)


def z500_pert(ht, day):
    run = os.path.join(ROOT, "outputs", "JAS", f"pangu24_{ht}_2.5Kday_gauss", "step1")
    st = State.from_npz(os.path.join(run, f"pert_{day:03d}.npz"), "pangu")
    return st.arrays["upper"][layout.Z, k500] / G      # geopotential' -> height' [m]

# shared CI: max |Z500'| over the four profiles at the reference day, /6, nice-rounded
ref_max = max(np.nanmax(np.abs(z500_pert(ht, REF_DAY))) for ht, _ in PROFILES)
dc = max(round((ref_max / 6.0) / 5.0) * 5.0, 5.0)      # multiples of 5 m
print(f"[profiles4] ref-day {REF_DAY} max|Z500'|={ref_max:.1f} m -> CI={dc:.0f} m (shared)")

proj = ccrs.PlateCarree(central_longitude=180)
neg = list(np.arange(-6 * dc, -dc + 1e-6, dc))
pos = list(np.arange(dc, 6 * dc + 1e-6, dc))

for day in DAYS:
    fig, axes = plt.subplots(2, 2, figsize=(15, 7.6),
                             subplot_kw={"projection": proj}, layout="constrained")
    fig.get_layout_engine().set(w_pad=0.01, h_pad=0.01, wspace=0.01, hspace=0.02)
    for ax, (ht, label) in zip(axes.ravel(), PROFILES):
        pz = z500_pert(ht, day)
        ax.contour(LON, LAT, base500, levels=np.arange(4800, 6000, 60.), colors="0.6",
                   linewidths=0.5, transform=ccrs.PlateCarree())
        ax.contour(LON, LAT, pz, levels=neg, colors="b", linewidths=2, transform=ccrs.PlateCarree())
        ax.contour(LON, LAT, pz, levels=pos, colors="r", linewidths=2, transform=ccrs.PlateCarree())
        ax.plot(elon, elat, "--", color='green' , linewidth=2.5, transform=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, edgecolor="0.5", linewidth=0.4, facecolor="0.92", zorder=-1)
        ax.coastlines(linewidth=0.4)
        ax.set_extent([40, 300, -55, 70], crs=ccrs.PlateCarree())
        ax.set_title(label, fontsize=22, fontweight="bold")
    fig.suptitle(f"Perturbation 500-hPa geopotential height at nominal day {day}"
                 f"   (Gaussian 2.5 K/day, CI = {dc:.0f} m)", fontsize=20, fontweight="bold")
    out = os.path.join(OUTDIR, f"profiles4_500z_day{day:02d}.png")
    fig.savefig(out, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print("saved", out)
print("done")
