"""Step 3 -- moisture-perturbation initialization (no heating).

Uses the day-7 moisture anomaly from a Step-1 run as the only initial perturbation
(f = 0), testing whether a pure moisture anomaly can excite barotropic vortices.

    python scripts/run_step3.py --step1_dir outputs/step1_pangu_JJA_Deep_10Kday [--seed_day 7]
"""
import argparse
import os

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.experiment import driver
from itcz.plotting import tracker


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step1_dir", required=True)
    ap.add_argument("--seed_day", type=int, default=7)
    ap.add_argument("--model", default=None)
    ap.add_argument("--background", default=None)
    ap.add_argument("--n_days", type=int, default=None)
    ap.add_argument("--no_plot", action="store_true")
    args = ap.parse_args()

    over = {}
    if args.model: over["model"] = args.model
    if args.background: over["background"] = args.background
    if args.n_days is not None: over.setdefault("driver", {})["n_days"] = args.n_days
    cfg = cfgmod.load_config(over)

    seed_path = os.path.join(cfgmod.bg_output_dir(cfg),
                             f"seed_moisture_{cfg['model']}_day{args.seed_day}.npz")
    driver.make_moisture_seed(args.step1_dir, cfg["model"], args.seed_day, seed_path,
                              step_hours=cfg["step_hours"])
    cfg["experiment"] = {
        "name": f"step3_{cfg['model']}_{cfg['background']}_moistinit_d{args.seed_day}",
        "forcing_type": "none", "persistent": False, "lock": "none", "seed_npz": seed_path,
    }
    run_dir = driver.run(cfg)
    if not args.no_plot:
        tracker.plot_field_panels(run_dir, cfg, "vort")
        tracker.plot_field_panels(run_dir, cfg, "tcwv")
        tracker.plot_timeseries([run_dir], [cfg["experiment"]["name"]], cfg)


if __name__ == "__main__":
    main()
