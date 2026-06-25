"""Build the annual-mean (all 12 months) background u0.

    python scripts/prep_annual.py [--y0 2000 --y1 2019]
"""
import argparse

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.data import prep

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--y0", type=int, default=2000)
    ap.add_argument("--y1", type=int, default=2019)
    args = ap.parse_args()
    cfg = cfgmod.load_config()
    print(f"[annual] averaging all months over {args.y0}-{args.y1}")
    fields = prep.season_fields(cfg, range(args.y0, args.y1 + 1), months=list(range(1, 13)))
    prep.save_ic(cfg, fields, "annual")
    prep.summarize_ic(cfg, "annual", "pangu")
    prep.summarize_ic(cfg, "annual", "fcnv2")
