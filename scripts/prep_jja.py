"""Build the JJA (Jun/Jul/Aug) multi-decadal background u0 (headline run).

    python scripts/prep_jja.py [--y0 1991 --y1 2020]
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
    print(f"[JJA] averaging Jun/Jul/Aug over {args.y0}-{args.y1}")
    fields = prep.season_fields(cfg, range(args.y0, args.y1 + 1), months=[6, 7, 8])
    prep.save_ic(cfg, fields, "JJA")
    prep.summarize_ic(cfg, "JJA", "pangu")
    prep.summarize_ic(cfg, "JJA", "fcnv2")
