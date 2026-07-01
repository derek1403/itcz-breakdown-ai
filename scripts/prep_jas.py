"""Build the JAS (Jul/Aug/Sep) multi-decadal background u0.

This is the *validated AI-Forum IC* (§7): with JAS the 10 N ITCZ is strong/moist
enough for Deep heating to roll up discrete vortices (DJF/JJA did not match).

    python scripts/prep_jas.py [--y0 1991 --y1 2020]
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
    print(f"[JAS] averaging Jul/Aug/Sep over {args.y0}-{args.y1}")
    fields = prep.season_fields(cfg, range(args.y0, args.y1 + 1), months=[7, 8, 9])
    prep.save_ic(cfg, fields, "JAS")
    prep.summarize_ic(cfg, "JAS", "pangu")
    prep.summarize_ic(cfg, "JAS", "fcnv2")
