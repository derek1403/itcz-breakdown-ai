"""Paper Fig. 4b generator: per-vortex zeta' / TCWV' genealogy from HAND tracks.

The automatic tracker could not reproduce the observed 1->2->4 genealogy, so the
vortex centres are tracked by eye (tracking/track_eye.md), snapped to the nearby
zeta' maximum by scripts/plot_eyecheck.py -> tracking/eye_snapped.csv.  This
script draws the two-panel genealogy from that csv:

  * one coloured line per labelled segment (2b, 2a, 1, 3, 4, 2)
  * thin connectors at the split/merge events so the tree reads as a genealogy
  * colour = FINAL vortex number  (1 blue, 2 orange [=2a/2b], 3 green, 4 red)

Genealogy (from the md annotations):
  days 5-8 trunk 2b ; day9 trunk splits -> 2a,2b,3 ; day10 1 splits from 2a ;
  day13 4 splits from 3 ; day14 2a+2b merge -> 2.

The vorticity axis is in units of 1e-5 s^-1.

    /home/pc/.conda/envs/pangu_env/bin/python paper/pic/plot_fig4b_timeseries.py
"""
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUN = os.path.join(ROOT, "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday")
CSV = os.path.join(RUN, "tracking", "eye_snapped.csv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig4b_timeseries.png")

# colour by final vortex number; 2a/2b/2 share vortex 2's orange
COLOR = {"1": "tab:blue", "2": "tab:orange", "2a": "tab:orange", "2b": "tab:orange",
         "3": "tab:green", "4": "tab:red"}
LEGEND = [("vortex 1", "tab:blue"), ("vortex 2", "tab:orange"),
          ("vortex 3", "tab:green"), ("vortex 4", "tab:red")]

# (from_label, from_day) -> (to_label, to_day) genealogy links; drawn in child colour
CONNECTORS = [
    ("2b", 8, "2a", 9), ("2b", 8, "3", 9),   # day9: trunk splits into 2a, 3 (2b continues)
    ("2a", 9, "1", 10),                        # day10: 1 splits from 2a
    # (4 is NOT a clean split from 3 -> no connector; it just appears at day13)
    ("2a", 13, "2", 14), ("2b", 13, "2", 14),  # day14: 2a + 2b merge into 2
]

plt.rcParams.update({
    "font.size": 12, "font.weight": "bold",
    "axes.titlesize": 15, "axes.titleweight": "bold",
    "axes.labelsize": 13, "axes.labelweight": "bold",
    "xtick.labelsize": 11, "ytick.labelsize": 11,
})

# --- load eye_snapped.csv -> nodes[(label, day)] = (zeta, tcwv); segs[label]=[days] ---
nodes, segs = {}, {}
with open(CSV) as fh:
    for r in csv.DictReader(fh):
        lab, day = r["label"], float(r["day"])
        nodes[(lab, day)] = (float(r["zeta_1e5"]), float(r["tcwv"]))
        segs.setdefault(lab, []).append(day)
for lab in segs:
    segs[lab] = sorted(segs[lab])


def seg_xy(lab, field_idx):
    d = segs[lab]
    return d, [nodes[(lab, dd)][field_idx] for dd in d]


fig, (axv, axt) = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, fi in ((axv, 0), (axt, 1)):
    # connectors first (thin, dashed, child colour), so segments sit on top
    for pl, pd, cl, cd in CONNECTORS:
        if (pl, pd) in nodes and (cl, cd) in nodes:
            ax.plot([pd, cd], [nodes[(pl, pd)][fi], nodes[(cl, cd)][fi]],
                    "--", color=COLOR[cl], lw=1.0, alpha=0.6, zorder=2)
    # one solid line per labelled segment
    for lab in segs:
        x, y = seg_xy(lab, fi)
        ax.plot(x, y, "-o", ms=4, lw=2.0, color=COLOR[lab], zorder=3)

axv.set(title=r"$\zeta'_{850}$ at vortex centres", xlabel="iteration n (nominal day)",
        ylabel=r"$\zeta'_{850}$ ($10^{-5}$ s$^{-1}$)")
axt.set(title=r"TCWV$'$ at vortex centres", xlabel="iteration n (nominal day)",
        ylabel=r"TCWV$'$ (kg m$^{-2}$)")
for ax in (axv, axt):
    ax.grid(alpha=0.3)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontweight("bold")
axv.legend(handles=[Line2D([0], [0], color=c, lw=2.5, label=n) for n, c in LEGEND],
           fontsize=10, framealpha=0.9, loc="upper left")

fig.tight_layout()
fig.savefig(OUT, dpi=150)
plt.close(fig)
print(f"[fig4b] segments: {', '.join(f'{k}({len(v)})' for k, v in segs.items())}")
print(f"[fig] {OUT}")
