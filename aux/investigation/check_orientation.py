"""Sanity-check Pangu I/O orientation: is the state fed to the model in the right
lat/lon orientation, and is the heating placed over the right longitude?

Tests:
  1) continents in the right place: plot IC T850 + MSL with coastlines.
  2) Pangu accepts our orientation: one-step drift B1 = M(u0)-u0 should be SMALL and
     physical (a lat-flip / lon-roll would make M(u0) garbage and B1 huge).
  3) heating is over the N Pacific: plot the heating field with coastlines.
Writes investigation/figs/orientation_check.png + prints drift stats.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs

from itcz import config as cfgmod
from itcz.models.layout import State, get_layout
from itcz.models.operators import load_operator
from itcz.experiment import forcing as fmod
from itcz.plotting.tracker import LAT, LON

cfg = cfgmod.load_config({"model": "pangu", "background": "paperDJF"})
lay = get_layout("pangu")
u0 = State.from_npz(cfgmod.ic_path(cfg, "paperDJF", "pangu"), "pangu")

T850 = u0.arrays["upper"][lay.T, lay.level_index(850)]
MSL = u0.arrays["surface"][lay.MSL]
print(f"IC T850: equator(lat=0,lon=180) = {T850[360,720]:.1f} K, global mean = {T850.mean():.1f} K")
print(f"IC MSL: global mean = {MSL.mean()/100:.1f} hPa")

# one Pangu step
op = load_operator(cfg)
m = op.step(u0)
T850m = m.arrays["upper"][lay.T, lay.level_index(850)]
drift = T850m - T850
print(f"M(u0) T850: equator = {T850m[360,720]:.1f} K (should stay ~equator value)")
print(f"one-step drift T850: RMS = {np.sqrt((drift**2).mean()):.3f} K, max|.| = {np.abs(drift).max():.2f} K")
print(f"  (a lat-flip/lon-roll would give RMS of tens of K; a few K = orientation OK)")

# heating field
f = fmod.heating_forcing(lay, cfg)
heat = f.arrays["upper"][lay.T, lay.level_index(850)]  # per-step K at 850
jmax, imax = np.unravel_index(np.argmax(heat), heat.shape)
print(f"heating max at lat={LAT[jmax]:.1f}N, lon={LON[imax]:.1f}E (expect ~10N, ~195E=165W, N Pacific)")

# plot
fig = plt.figure(figsize=(13, 8))
def panel(pos, fld, title, cmap, vmin=None, vmax=None):
    ax = fig.add_subplot(*pos, projection=ccrs.PlateCarree(central_longitude=180))
    ax.coastlines(linewidth=0.6, color="k")
    ax.set_global()
    im = ax.pcolormesh(LON, LAT, fld, cmap=cmap, shading="auto",
                       vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
    ax.set_title(title, fontsize=10); plt.colorbar(im, ax=ax, shrink=0.6)
panel((2,2,1), T850, "IC T850 (continents should match coastlines)", "RdYlBu_r")
panel((2,2,2), MSL/100, "IC MSL (hPa)", "viridis")
panel((2,2,3), T850m, "M(u0) T850 after 1 Pangu step (should look ~same)", "RdYlBu_r")
panel((2,2,4), heat, "per-step heating @850 (should sit over N Pacific)", "Reds")
fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs", "orientation_check.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, dpi=120); print(f"[orient] {out}")
