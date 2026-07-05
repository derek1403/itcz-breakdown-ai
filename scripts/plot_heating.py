"""Generate a spec folder's heating_dist_check.png (paper Fig. 2) from its manifest.

Each spec folder outputs/<bg>/<spec>/config.yaml fully describes its heating (model,
background, heat_type, amp, geometry via the root config); this writes the matching
4-panel figure into that folder so the heating is visualised where the data lives.

    python scripts/plot_heating.py outputs/JAS/pangu24_Deep_2.5Kday_gauss   # one spec
    python scripts/plot_heating.py --all JAS                                # every JAS spec
"""
import argparse
import glob
import os

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.plotting import tracker


def gen_for_spec(spec_dir):
    cfg = cfgmod.load_experiment(spec_dir)
    out = os.path.join(os.path.abspath(spec_dir), "heating_dist_check.png")
    tracker.plot_heating_dist(cfg, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_dir", nargs="?", default=None, help="a single spec folder")
    ap.add_argument("--all", metavar="BACKGROUND", default=None,
                    help="regenerate for every spec folder under outputs/<BACKGROUND>/")
    args = ap.parse_args()

    if args.all:
        base = os.path.join(cfgmod.load_config()["paths"]["output_dir"], args.all)
        specs = sorted(os.path.dirname(p) for p in glob.glob(os.path.join(base, "*", "config.yaml")))
        if not specs:
            raise SystemExit(f"no spec folders (with config.yaml) under {base}")
        for s in specs:
            gen_for_spec(s)
    elif args.spec_dir:
        gen_for_spec(args.spec_dir)
    else:
        ap.error("give a spec_dir or --all <background>")


if __name__ == "__main__":
    main()
