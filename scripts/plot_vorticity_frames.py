"""Per-step 850-hPa vorticity frames, saved into each run's own folder.

Spec: domain 100E-70W (=290E), 0-45N; zeta x 1e5; seismic, discrete 1-unit bins,
double-ended (extend both), vmin/vmax = -10/10 (positive vorticity = red).

Frames are written to ``<run_dir>/vort_frames/vort_dDD.DD_sNNN.png``.

Preview (default = 2 evenly-spaced frames, to check the style):
    python scripts/plot_vorticity_frames.py --run_dir outputs/step1_pangu_JJA_Deep_10Kday

Make ALL 64 frames:
    python scripts/plot_vorticity_frames.py --run_dir outputs/step1_pangu_JJA_Deep_10Kday --all

Every run (auto-detects model from the dir name):
    python scripts/plot_vorticity_frames.py --all_runs --all
"""
import argparse
import glob
import os

import _bootstrap  # noqa: F401
import numpy as np

from itcz import config as cfgmod
from itcz.plotting import tracker


def model_from_name(run_dir):
    base = os.path.basename(os.path.normpath(run_dir))
    return "fcnv2" if "fcnv2" in base else "pangu"


def frames_for(run_dir, args):
    steps = tracker.list_steps(run_dir)
    if not steps:
        print(f"[skip] no pert_*.npz in {run_dir}")
        return
    if args.all:
        sel = steps
    elif args.steps:
        sel = [int(s) for s in args.steps.split(",")]
    else:  # preview: n_frames evenly spaced (incl. first & last)
        idx = np.linspace(0, len(steps) - 1, args.n_frames).round().astype(int)
        sel = [steps[i] for i in sorted(set(idx))]
    cfg = cfgmod.load_config({"model": model_from_name(run_dir)})
    print(f"[run] {run_dir} (model={cfg['model']}): {len(sel)} frame(s)")
    tracker.plot_vorticity_frames(
        run_dir, cfg, steps=sel,
        domain=(args.lon0, args.lon1, args.lat0, args.lat1),
        vmax=args.vmax, step_unit=args.step_unit, cmap=args.cmap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", default=None)
    ap.add_argument("--all_runs", action="store_true", help="all outputs/step*/ dirs")
    ap.add_argument("--all", action="store_true", help="every saved step (e.g. 64)")
    ap.add_argument("--n_frames", type=int, default=2, help="preview frame count")
    ap.add_argument("--steps", default=None, help="explicit comma list, e.g. 24,48")
    ap.add_argument("--lon0", type=float, default=100.0)
    ap.add_argument("--lon1", type=float, default=290.0)  # 70W
    ap.add_argument("--lat0", type=float, default=0.0)
    ap.add_argument("--lat1", type=float, default=45.0)
    ap.add_argument("--vmax", type=float, default=10.0)
    ap.add_argument("--step_unit", type=float, default=1.0, help="discrete bin size")
    ap.add_argument("--cmap", default="seismic", help="seismic=+red/-blue diverging")
    args = ap.parse_args()

    if args.all_runs:
        runs = sorted(glob.glob(os.path.join(cfgmod.PROJECT_ROOT, "outputs", "*", "step*")))
    elif args.run_dir:
        runs = [args.run_dir]
    else:
        ap.error("give --run_dir PATH or --all_runs")
    for rd in runs:
        frames_for(rd, args)


if __name__ == "__main__":
    main()
