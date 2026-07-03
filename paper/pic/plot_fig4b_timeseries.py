"""Paper Fig. 4b generator: per-vortex zeta' and TCWV' genealogy branches.

Redraw of the headline run's timeseries as MANY lines (one per tracked vortex
branch), like tracking/vortex_genealogy.png but in the 2-panel Fig.4b layout.
Uses the SAME detect()/link() as scripts/track_vortices.py (and the QC montage
scripts/plot_maxcheck.py), so tuning the knobs below keeps all three consistent.

The vorticity axis is in units of 1e-5 s^-1 (values ~0..90), not raw s^-1.

Run with pangu_env python:
    /home/pc/.conda/envs/pangu_env/bin/python paper/pic/plot_fig4b_timeseries.py
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import track_vortices as TV
from itcz.plotting import tracker as T
from itcz.models.layout import get_layout

# ----------------------------- knobs (kept in sync with the QC montage) -------
RUN = os.path.join(ROOT, "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig4b_timeseries.png")
BAND = None            # None -> use the run's plot.track_band
PEAK_MIN = 4.0         # zeta' detection threshold (x1e-5)
NBHD_DEG = 6.0         # min separation between peaks (deg)
MAX_JUMP = 10.0        # max day-to-day move when linking (deg)
MIN_LEN = 3            # keep a branch only with >= this many points
KEEP_ZETA = 6.0        # keep a branch only if its peak zeta' >= this (x1e-5)
START_DAY = 4.0        # ignore earlier (pre-vortex) days
# -----------------------------------------------------------------------------

plt.rcParams.update({
    "font.size": 12,
    "font.weight": "bold",
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "axes.labelweight": "bold",
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
})

with open(os.path.join(RUN, "config_used.json")) as fh:
    cfg = json.load(fh)
model = cfg["model"]
layout = get_layout(model)
band = BAND or cfg["plot"]["track_band"]

steps_dets, days = [], []
for s in T.list_steps(RUN):
    day = s * cfg["step_hours"] / 24.0
    if day < START_DAY:
        continue
    st = T.load_pert(RUN, s, model)
    zeta = T.vort850(st, layout) * 1e5
    tcwv = np.asarray(T.tcwv_anom(st, layout))
    steps_dets.append(TV.detect(zeta, tcwv, band, PEAK_MIN, NBHD_DEG))
    days.append(day)

tracks = TV.link(steps_dets, days, MAX_JUMP)
leaves = [tr for tr in tracks if not tr["split"]
          and len(tr["points"]) >= MIN_LEN
          and max(p["zeta"] for p in tr["points"]) >= KEEP_ZETA]
leaves.sort(key=lambda tr: tr["points"][0]["day"])
print(f"[fig4b] {len(tracks)} raw tracks -> {len(leaves)} branches kept")

colors = plt.get_cmap("tab10")(np.linspace(0, 1, 10))
fig, (axv, axt) = plt.subplots(1, 2, figsize=(12, 4.5))
for k, tr in enumerate(leaves):
    d = [p["day"] for p in tr["points"]]
    axv.plot(d, [p["zeta"] for p in tr["points"]], "-o", ms=3, lw=1.4, color=colors[k % 10])
    axt.plot(d, [p["tcwv"] for p in tr["points"]], "-o", ms=3, lw=1.4, color=colors[k % 10])
axv.set(title=r"$\zeta'_{850}$ at vortex centres", xlabel="iteration n (nominal day)",
        ylabel=r"$\zeta'_{850}$ ($10^{-5}$ s$^{-1}$)")
axt.set(title=r"TCWV$'$ at vortex centres", xlabel="iteration n (nominal day)",
        ylabel=r"TCWV$'$ (kg m$^{-2}$)")
for ax in (axv, axt):
    ax.grid(alpha=0.3)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontweight("bold")

fig.tight_layout()
fig.savefig(OUT, dpi=150)
plt.close(fig)
print(f"[fig] {OUT}")
