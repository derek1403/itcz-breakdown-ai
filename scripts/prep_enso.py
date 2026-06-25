"""Build ENSO-phase DJF composite background states u0.

Downloads only the small NOAA/CPC ONI index text, classifies DJF seasons, and
composites matching DJF months from local ERA5 monthly data into:
    enso_pos (strong El Nino), enso_neg (strong La Nina), enso_neutral (|ONI|<neutral).

    python scripts/prep_enso.py [--thr 1.5 --neutral 0.5 --n_neutral 6 --y0 1981 --y1 2025]
"""
import argparse
import os
import urllib.request

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.data import prep

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


def fetch_oni(cfg):
    cache = os.path.join(cfg["paths"]["ic_dir"], "oni.ascii.txt")
    os.makedirs(cfg["paths"]["ic_dir"], exist_ok=True)
    if not os.path.exists(cache):
        print(f"[enso] downloading ONI -> {cache}")
        urllib.request.urlretrieve(ONI_URL, cache)
    djf = []
    with open(cache) as fh:
        next(fh)
        for line in fh:
            p = line.split()
            if len(p) >= 4 and p[0] == "DJF":
                djf.append((int(p[1]), float(p[3])))
    return djf


def _composite(cfg, name, djf_years):
    pairs = prep.djf_pairs(djf_years)
    print(f"[enso] {name}: DJF years {sorted(djf_years)} ({len(pairs)} months)")
    fields = prep.season_fields_pairs(cfg, pairs)
    prep.save_ic(cfg, fields, name)
    prep.summarize_ic(cfg, name, "pangu")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thr", type=float, default=1.5)
    ap.add_argument("--neutral", type=float, default=0.5)
    ap.add_argument("--n_neutral", type=int, default=6)
    ap.add_argument("--y0", type=int, default=1981)
    ap.add_argument("--y1", type=int, default=2025)
    args = ap.parse_args()

    cfg = cfgmod.load_config()
    djf = [(yr, a) for yr, a in fetch_oni(cfg) if args.y0 <= yr <= args.y1]
    pos = [yr for yr, a in djf if a >= args.thr]
    neg = [yr for yr, a in djf if a <= -args.thr]
    neutral = sorted([(abs(a), yr) for yr, a in djf if abs(a) < args.neutral])
    neutral_years = [yr for _, yr in neutral[: args.n_neutral]]
    print(f"[enso] pos={pos}\n[enso] neg={neg}\n[enso] neutral={neutral_years}")
    _composite(cfg, "enso_pos", pos)
    _composite(cfg, "enso_neg", neg)
    _composite(cfg, "enso_neutral", neutral_years)
