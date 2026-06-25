"""Build the RAGASA typhoon-day background u0 (single day, 00Z).

    python scripts/prep_ragasa.py [--date 2025-09-17 --hour 0]
"""
import argparse

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.data import prep

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2025-09-17")
    ap.add_argument("--hour", type=int, default=0)
    args = ap.parse_args()
    y, m, d = (int(x) for x in args.date.split("-"))
    cfg = cfgmod.load_config()
    print(f"[ragasa] single day {args.date} @ {args.hour:02d}Z")
    fields = prep.day_fields(cfg, y, m, d, hour=args.hour)
    prep.save_ic(cfg, fields, "ragasa")
    prep.summarize_ic(cfg, "ragasa", "pangu")
    prep.summarize_ic(cfg, "ragasa", "fcnv2")
