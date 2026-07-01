"""Re-plot diagnostics for a finished run directory.

Uses the run's OWN config_used.json (so step_hours / forcing_days / etc. match how
the run was actually made) — falls back to the current config.yaml if it is absent.

    python scripts/plot_run.py outputs/<run_name> [--model pangu]
"""
import argparse
import json
import os

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.plotting import tracker

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    used = os.path.join(args.run_dir, "config_used.json")
    if os.path.exists(used):
        with open(used) as fh:
            cfg = json.load(fh)          # faithful to how the run was made
        if args.model:
            cfg["model"] = args.model
    else:
        cfg = cfgmod.load_config({"model": args.model} if args.model else None)
    tracker.plot_field_panels(args.run_dir, cfg, "vort")
    tracker.plot_field_panels(args.run_dir, cfg, "tcwv")
    tracker.plot_timeseries([args.run_dir], [os.path.basename(args.run_dir)], cfg)
