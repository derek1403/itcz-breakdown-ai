"""Step 4 -- wind locking with persistent moisture forcing.

Starts from the day-7 moisture anomaly, keeps injecting moisture forcing, but zeroes
the wind perturbation each step -- moisture evolution without dynamical feedback.

    python scripts/run_step4.py --step1_dir outputs/step1_pangu_JJA_Deep_10Kday
"""
import argparse
import os

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.experiment import driver
from itcz.plotting import tracker


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step1_dir", default=None,
                    help="Step-1 run dir to seed from; defaults to <exp>/step1 when --exp is given")
    ap.add_argument("--seed_day", type=int, default=7)
    ap.add_argument("--model", default=None)
    ap.add_argument("--background", default=None)
    ap.add_argument("--moist_amp_qday", type=float, default=None)
    ap.add_argument("--n_days", type=int, default=None)
    ap.add_argument("--exp", default=None,
                    help="spec dir for the outputs/<bg>/<spec>/stepN layout (reads <spec>/config.yaml)")
    ap.add_argument("--no_plot", action="store_true")
    args = ap.parse_args()

    over = {}
    if args.model: over["model"] = args.model
    if args.background: over["background"] = args.background
    if args.moist_amp_qday is not None:
        over.setdefault("forcing", {})["moist_amp_qday"] = args.moist_amp_qday
    if args.n_days is not None: over.setdefault("driver", {})["n_days"] = args.n_days
    cfg = cfgmod.load_experiment(args.exp, over) if args.exp else cfgmod.load_config(over)

    step1_dir = args.step1_dir or (cfgmod.step_out_dir(args.exp, 1) if args.exp else None)
    if not step1_dir:
        ap.error("--step1_dir is required (or pass --exp to default to <exp>/step1)")
    seed_dir = os.path.abspath(args.exp) if args.exp else cfgmod.bg_output_dir(cfg)
    seed_path = os.path.join(seed_dir, f"seed_moisture_{cfg['model']}_day{args.seed_day}.npz")
    driver.make_moisture_seed(step1_dir, cfg["model"], args.seed_day, seed_path,
                              step_hours=cfg["step_hours"])
    cfg["experiment"] = {
        "name": f"step4_{cfg['model']}_{cfg['background']}_windlock",
        "forcing_type": "moisture", "persistent": True, "lock": "wind", "seed_npz": seed_path,
    }
    if args.exp:
        cfg["experiment"]["name"] = f"{os.path.basename(os.path.normpath(args.exp))}/step4"
        cfg["experiment"]["out_dir"] = cfgmod.step_out_dir(args.exp, 4)
    run_dir = driver.run(cfg)
    if not args.no_plot:
        tracker.plot_field_panels(run_dir, cfg, "vort")
        tracker.plot_field_panels(run_dir, cfg, "tcwv")
        tracker.plot_timeseries([run_dir], [cfg["experiment"]["name"]], cfg)


if __name__ == "__main__":
    main()
