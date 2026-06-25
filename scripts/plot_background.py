"""Plot the initial background field (u0) 850-hPa vorticity and TCWV.

Saved at the ``outputs/<background>/`` level (same level as the step run dirs), as
``ic_vort_<model>.png`` and ``ic_tcwv_<model>.png``.  Needs the IC built first
(scripts/prep_*.py).

    python scripts/plot_background.py --backgrounds JJA DJF annual ragasa \
        enso_pos enso_neg enso_neutral --model pangu
"""
import argparse

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.plotting import tracker

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backgrounds", nargs="+", default=["JJA"])
    ap.add_argument("--model", default="pangu", help="pangu|fcnv2 (winds identical; "
                    "TCWV uses that model's diagnostic)")
    args = ap.parse_args()
    for bg in args.backgrounds:
        cfg = cfgmod.load_config({"model": args.model, "background": bg})
        print(f"[ic-plot] {bg} ({args.model})")
        tracker.plot_background_fields(cfg)
