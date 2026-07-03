"""Paper Fig. 4a generator: TCWV' snapshot montage for the headline run.

Reuses make_panels() from plot_fig3_panels.py with field="tcwv", so it inherits
the same layout/font styling and the SIGMA_MULT / DAYS / NCOL knobs. The dashed
heating-envelope ellipse is drawn in red here (Fig. 3 uses green).

Run with pangu_env python (from anywhere):
    /home/pc/.conda/envs/pangu_env/bin/python paper/pic/plot_fig4_panels.py
"""
import os

from plot_fig3_panels import ROOT, make_panels

PIC = os.path.dirname(os.path.abspath(__file__))
FIG4_RUN = os.path.join(ROOT, "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday")
FIG4_COLOR = "red"      # dashed heating-envelope colour for the TCWV figure

make_panels(FIG4_RUN, os.path.join(PIC, "fig4a_panels_tcwv.png"),
            field="tcwv", ellipse_color=FIG4_COLOR)
