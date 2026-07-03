"""Appendix snapshot montages (Figs. B1d, B3, D1), paper-styled.

Reuses make_panels() from plot_fig3_panels.py so these inherit exactly the same
styling knobs (SIGMA_MULT, ELLIPSE_COLOR, DAYS, NCOL). B1c and D2 are the same
run as Fig. 3, so they simply reference pic/fig3_panels_vort.png in appendix.md.

Run with pangu_env python (from anywhere):
    /home/pc/.conda/envs/pangu_env/bin/python paper/pic/plot_appendix_panels.py
"""
import os

from plot_fig3_panels import ROOT, make_panels

PIC = os.path.dirname(os.path.abspath(__file__))

RUNS = {
    "figB1d_panels_vort.png": "outputs/paperJAS/step1_pangu_paperJAS_Deep_2.5Kday",  # cosine-lobe
    "figB3_panels_vort.png":  "outputs/DJF/step1_pangu_DJF_Deep_2.5Kday",            # DJF background
    "figD1_panels_vort.png":  "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday_6h_sustained",  # 6-h operator
}

for out_name, run_rel in RUNS.items():
    make_panels(os.path.join(ROOT, run_rel), os.path.join(PIC, out_name))
