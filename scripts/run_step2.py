"""Step 2 -- moisture locking (no moisture evolution).

Identical to Step 1 but the moisture perturbation is zeroed every step, pinning
humidity at the background.  Expected: vorticity growth suppressed (PDF p.5).

    python scripts/run_step2.py [--model pangu --background JJA --amp_K 10]
"""
import argparse

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.experiment import driver
from itcz.plotting import tracker


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--background", default=None)
    ap.add_argument("--amp_K", type=float, default=None)
    ap.add_argument("--heat_type", default=None)
    ap.add_argument("--n_days", type=int, default=None)
    ap.add_argument("--no_plot", action="store_true")
    args = ap.parse_args()

    over = {}
    if args.model: over["model"] = args.model
    if args.background: over["background"] = args.background
    if args.amp_K is not None: over.setdefault("forcing", {})["amp_K_per_day"] = args.amp_K
    if args.heat_type: over.setdefault("forcing", {})["heat_type"] = args.heat_type
    if args.n_days is not None: over.setdefault("driver", {})["n_days"] = args.n_days
    cfg = cfgmod.load_config(over)

    amp, ht = cfg["forcing"]["amp_K_per_day"], cfg["forcing"]["heat_type"]
    cfg["experiment"] = {
        "name": f"step2_{cfg['model']}_{cfg['background']}_{ht}_{amp:g}Kday_moistlock",
        "forcing_type": "heating", "persistent": False, "lock": "moisture", "seed_npz": None,
    }
    run_dir = driver.run(cfg)
    if not args.no_plot:
        tracker.plot_field_panels(run_dir, cfg, "vort")
        tracker.plot_field_panels(run_dir, cfg, "tcwv")
        tracker.plot_timeseries([run_dir], [cfg["experiment"]["name"]], cfg)


if __name__ == "__main__":
    main()
