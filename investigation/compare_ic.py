"""Convert the paper's mean_DJF.h5 to our Pangu State npz, and compare field-by-field
against our self-built ic/u0_paperDJF_pangu.npz to validate the initial condition.

Paper h5 (mean_DJF.h5): mean_pl (5,13,721,1440)=[z,q,t,u,v], mean_sfc (4,721,1440)=
[msl,u10,v10,t2m], lat 90->-90, lon 0->359.75, levels 1000->50 -- identical layout to
ours. Outputs ic/u0_paperHM_pangu.npz + a difference report and maps in investigation/figs/ic/.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H5 = os.path.join(ROOT, "investigation/ref/ERA5_means/mean_DJF.h5")
OURS = os.path.join(ROOT, "ic/u0_paperDJF_pangu.npz")
OUT_NPZ = os.path.join(ROOT, "ic/u0_paperHM_pangu.npz")
FIGDIR = os.path.join(ROOT, "investigation/figs/ic")
os.makedirs(FIGDIR, exist_ok=True)

LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50]
UVARS = ["z", "q", "t", "u", "v"]
SVARS = ["msl", "u10", "v10", "t2m"]
LAT = np.linspace(90, -90, 721)
LON = np.linspace(0, 360, 1440, endpoint=False)

# --- load paper IC ---
with h5py.File(H5, "r") as f:
    p_pl = np.asarray(f["mean_pl"], dtype=np.float32)    # (5,13,721,1440)
    p_sfc = np.asarray(f["mean_sfc"], dtype=np.float32)  # (4,721,1440)

# save as our npz format
np.savez_compressed(OUT_NPZ, surface=p_sfc, upper=p_pl)
print(f"[ic] wrote {OUT_NPZ}  upper{p_pl.shape} surface{p_sfc.shape}")

# --- load ours ---
with np.load(OURS) as d:
    o_pl = d["upper"].astype(np.float32)
    o_sfc = d["surface"].astype(np.float32)

print("\n=== UPPER fields: ours vs paper (per variable, over all 13 levels) ===")
print(f"{'var':4s} {'our_mean':>12s} {'paper_mean':>12s} {'RMSE':>12s} {'maxabs':>12s} {'field_std':>12s}")
for vi, v in enumerate(UVARS):
    o = o_pl[vi]; p = p_pl[vi]
    diff = o - p
    print(f"{v:4s} {o.mean():12.4g} {p.mean():12.4g} {np.sqrt((diff**2).mean()):12.4g} "
          f"{np.abs(diff).max():12.4g} {o.std():12.4g}")

print("\n=== SURFACE fields ===")
print(f"{'var':4s} {'our_mean':>12s} {'paper_mean':>12s} {'RMSE':>12s} {'maxabs':>12s} {'field_std':>12s}")
for vi, v in enumerate(SVARS):
    o = o_sfc[vi]; p = p_sfc[vi]
    diff = o - p
    print(f"{v:4s} {o.mean():12.4g} {p.mean():12.4g} {np.sqrt((diff**2).mean()):12.4g} "
          f"{np.abs(diff).max():12.4g} {o.std():12.4g}")

# --- difference maps for key fields ---
def lev(p): return LEVELS.index(p)
panels = [("z@500hPa", o_pl[0, lev(500)], p_pl[0, lev(500)]),
          ("t@850hPa", o_pl[2, lev(850)], p_pl[2, lev(850)]),
          ("u@850hPa", o_pl[3, lev(850)], p_pl[3, lev(850)]),
          ("q@850hPa", o_pl[1, lev(850)], p_pl[1, lev(850)]),
          ("msl",      o_sfc[0],          p_sfc[0])]
fig, axes = plt.subplots(len(panels), 3, figsize=(15, 2.6 * len(panels)))
for r, (name, o, p) in enumerate(panels):
    d = o - p
    for c, (title, fld, cmap) in enumerate([(f"{name} ours", o, "viridis"),
                                            (f"{name} paper", p, "viridis"),
                                            (f"{name} diff (ours-paper)", d, "RdBu_r")]):
        ax = axes[r, c]
        vmax = np.abs(d).max() if c == 2 else None
        im = ax.pcolormesh(LON, LAT, fld, cmap=cmap, shading="auto",
                           vmin=(-vmax if c == 2 else None), vmax=(vmax if c == 2 else None))
        ax.set_title(title, fontsize=8); ax.set_xticks([]); ax.set_yticks([])
        plt.colorbar(im, ax=ax, shrink=0.8)
fig.tight_layout()
out = os.path.join(FIGDIR, "ic_ours_vs_paper.png")
fig.savefig(out, dpi=110); plt.close(fig)
print(f"\n[ic] difference maps -> {out}")
