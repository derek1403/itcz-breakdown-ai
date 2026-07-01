"""fcnv2 (GPU) heating-amplitude sweep for paperDJF Step1.

Keeps the current pipeline/forcing mechanism; only varies amp_K_per_day to find the
value that reproduces the AI-Forum clean ITCZ vortex rollup (peak ~47e-5, discrete
vortices, quiet mid-latitudes). The fcnv2 operator is loaded ONCE on cuda and reused
across all amplitudes. No in-loop plotting (use replot_smoothed.py afterwards).

    python investigation/sweep_fcnv2_amp.py [--amps 0.1 0.5 1 2] [--n_days 16]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from itcz import config as cfgmod
from itcz.experiment import driver
from itcz.models.operators import load_operator


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amps", nargs="+", type=float, default=[0.1, 0.5, 1.0, 2.0])
    ap.add_argument("--n_days", type=int, default=16)
    ap.add_argument("--background", default="paperDJF")
    ap.add_argument("--heat_type", default="Deep")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    base = cfgmod.load_config({
        "model": "fcnv2", "device": args.device, "background": args.background,
        "driver": {"n_days": args.n_days},
        "forcing": {"heat_type": args.heat_type},
    })
    print(f"[sweep] loading fcnv2 operator on {args.device} ...", flush=True)
    op = load_operator(base)   # one GPU load, reused for every amplitude

    for amp in args.amps:
        cfg = cfgmod.load_config({
            "model": "fcnv2", "device": args.device, "background": args.background,
            "driver": {"n_days": args.n_days},
            "forcing": {"amp_K_per_day": amp, "heat_type": args.heat_type},
        })
        cfg["experiment"] = {
            "name": f"step1_fcnv2_{args.background}_{args.heat_type}_{amp:g}Kday",
            "forcing_type": "heating", "persistent": False, "lock": "none", "seed_npz": None,
        }
        t0 = time.time()
        print(f"\n[sweep] === amp={amp:g} K/day -> {cfg['experiment']['name']} ===", flush=True)
        rd = driver.run(cfg, operator=op)
        print(f"[sweep] amp={amp:g} done in {(time.time()-t0)/60:.1f} min -> {rd}", flush=True)


if __name__ == "__main__":
    main()
