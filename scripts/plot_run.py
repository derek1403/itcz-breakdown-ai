"""Re-plot diagnostics for a finished run directory.

    python scripts/plot_run.py outputs/<run_name> [--model pangu]
"""
import argparse
import os

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.plotting import tracker

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    cfg = cfgmod.load_config({"model": args.model} if args.model else None)
    tracker.plot_field_panels(args.run_dir, cfg, "vort")
    tracker.plot_field_panels(args.run_dir, cfg, "tcwv")
    tracker.plot_timeseries([args.run_dir], [os.path.basename(args.run_dir)], cfg)
