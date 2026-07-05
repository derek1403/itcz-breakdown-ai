"""Resume / extend an existing run to more days via full-state warm-start.

Reads a finished run's own ``config_used.json`` (so step_hours, forcing geometry,
locks, etc. exactly match how it was made -- no dependence on the mutable root
``config.yaml``), auto-detects the last saved ``pert_NNN.npz``, and continues the
driver from there up to ``--n_days``.  Model- and step-agnostic: works for any
Step 1-4 run on Pangu or FCNv2.

    python scripts/resume_run.py outputs/JAS/step1_pangu_JAS_Deep_2.5Kday \
        --n_days 20 --forcing_days 20
"""
import argparse
import json
import os

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.experiment import driver
from itcz.plotting import tracker


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="existing run directory (contains config_used.json + pert_*.npz)")
    ap.add_argument("--n_days", type=int, required=True, help="new total integration length (days)")
    ap.add_argument("--forcing_days", type=int, default=None,
                    help="override forcing_days (e.g. keep heating on through the extension)")
    ap.add_argument("--no_plot", action="store_true")
    args = ap.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    cfg_path = os.path.join(run_dir, "config_used.json")
    if not os.path.exists(cfg_path):
        raise SystemExit(f"no config_used.json in {run_dir}")
    with open(cfg_path) as fh:
        cfg = json.load(fh)

    # last completed step = highest existing pert_NNN.npz (same discovery contract as plotting)
    steps = tracker.list_steps(run_dir)
    if not steps:
        raise SystemExit(f"no pert_*.npz in {run_dir}")
    start_step = max(steps)

    cfg["driver"]["n_days"] = args.n_days
    if args.forcing_days is not None:
        cfg["driver"]["forcing_days"] = args.forcing_days

    N = cfgmod.n_steps(cfg)
    if N <= start_step:
        raise SystemExit(f"nothing to do: target N={N} <= last completed step {start_step}")

    cfg["experiment"]["resume_from"] = os.path.join(run_dir, f"pert_{start_step:03d}.npz")
    cfg["experiment"]["start_step"] = start_step
    cfg["experiment"]["out_dir"] = run_dir      # write back exactly where we read from
                                                # (robust to the outputs/<bg>/<spec>/stepN layout)

    print(f"[resume] {os.path.basename(run_dir)}: warm-start from step {start_step} "
          f"-> N={N} ({args.n_days}d), forcing_days={cfg['driver']['forcing_days']}")

    out = driver.run(cfg)
    if not args.no_plot:
        tracker.plot_field_panels(out, cfg, "vort")
        tracker.plot_field_panels(out, cfg, "tcwv")
        tracker.plot_timeseries([out], [cfg["experiment"]["name"]], cfg)


if __name__ == "__main__":
    main()
