"""Build the DJF (Dec/Jan/Feb) multi-decadal background u0.

    python scripts/prep_djf.py [--y0 1991 --y1 2020]
"""
import argparse

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.data import prep

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--y0", type=int, default=1991)
    ap.add_argument("--y1", type=int, default=2020)
    args = ap.parse_args()
    cfg = cfgmod.load_config()
    pairs = prep.djf_pairs(range(args.y0, args.y1 + 1))
    print(f"[DJF] averaging DJF over {args.y0}-{args.y1} ({len(pairs)} months)")
    fields = prep.season_fields_pairs(cfg, pairs)
    prep.save_ic(cfg, fields, "DJF")
    prep.summarize_ic(cfg, "DJF", "pangu")
    prep.summarize_ic(cfg, "DJF", "fcnv2")
