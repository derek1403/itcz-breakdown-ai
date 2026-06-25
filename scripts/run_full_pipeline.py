"""Full ITCZ-breakdown pipeline: JJA climatology + Steps 1-4 for both models.

Runs end-to-end, parallelized (cpu_num = -1 -> all cores), robust to per-stage
failures, and writes a consolidated report + comparison figures to
``verification/full_run/`` for inspection.

    python scripts/run_full_pipeline.py [--models pangu fcnv2 --n_days 16 --amp_K 10]

Stages per model: Step 1 (heating) -> Step 2 (moisture lock) -> Step 3 (moisture
init, from Step 1 day-7 seed) -> Step 4 (wind lock + moisture forcing).
"""
import argparse
import os
import time
import traceback

import _bootstrap  # noqa: F401
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from itcz import config as cfgmod
from itcz.data import prep
from itcz.experiment import driver
from itcz.models.operators import load_operator
from itcz.plotting import tracker

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Per-background report dir (set in main once the background is known) so runs of
# different backgrounds don't overwrite each other's report/comparison figures.
REPORT_DIR = os.path.join(ROOT, "verification", "full_run")

STAGES = []   # (name, status, detail, seconds)


def stage(name, fn):
    t0 = time.time()
    print(f"\n########## STAGE: {name} ##########", flush=True)
    try:
        out = fn()
        STAGES.append((name, "OK", "", time.time() - t0))
        return out
    except Exception as e:  # keep going; record for the report
        tb = traceback.format_exc()
        print(f"!!!! STAGE FAILED: {name}: {e}\n{tb}", flush=True)
        STAGES.append((name, "FAIL", f"{e}", time.time() - t0))
        return None


def prep_jja(cfg, y0, y1):
    if (os.path.exists(cfgmod.ic_path(cfg, "JJA", "pangu"))
            and os.path.exists(cfgmod.ic_path(cfg, "JJA", "fcnv2"))):
        print("[pipeline] JJA IC already present; skipping prep")
        return
    fields = prep.season_fields(cfg, range(y0, y1 + 1), months=[6, 7, 8])
    prep.save_ic(cfg, fields, "JJA")
    prep.summarize_ic(cfg, "JJA", "pangu")
    prep.summarize_ic(cfg, "JJA", "fcnv2")


def _run_one(cfg, op, exp):
    cfg = dict(cfg)
    cfg["experiment"] = exp
    rd = driver.run(cfg, operator=op)
    tracker.plot_field_panels(rd, cfg, "vort")
    tracker.plot_field_panels(rd, cfg, "tcwv")
    return rd


def run_model(cfg, model, amp, ht):
    cfg = dict(cfg)
    cfg["model"] = model
    op = stage(f"load_operator[{model}]", lambda: load_operator(cfg))
    if op is None:
        return {}

    bg = cfg["background"]
    runs = {}
    runs["step1"] = stage(f"{model}/step1", lambda: _run_one(cfg, op, {
        "name": f"step1_{model}_{bg}_{ht}_{amp:g}Kday",
        "forcing_type": "heating", "persistent": False, "lock": "none", "seed_npz": None}))
    runs["step2"] = stage(f"{model}/step2", lambda: _run_one(cfg, op, {
        "name": f"step2_{model}_{bg}_{ht}_{amp:g}Kday_moistlock",
        "forcing_type": "heating", "persistent": False, "lock": "moisture", "seed_npz": None}))

    seed = None
    if runs["step1"]:
        seed = os.path.join(cfgmod.bg_output_dir(cfg), f"seed_moisture_{model}_day7.npz")
        stage(f"{model}/seed", lambda: driver.make_moisture_seed(
            runs["step1"], model, 7, seed, step_hours=cfg["step_hours"]))
    if seed and os.path.exists(seed):
        runs["step3"] = stage(f"{model}/step3", lambda: _run_one(cfg, op, {
            "name": f"step3_{model}_{bg}_moistinit_d7",
            "forcing_type": "none", "persistent": False, "lock": "none", "seed_npz": seed}))
        runs["step4"] = stage(f"{model}/step4", lambda: _run_one(cfg, op, {
            "name": f"step4_{model}_{bg}_windlock",
            "forcing_type": "moisture", "persistent": True, "lock": "wind", "seed_npz": seed}))

    stage(f"{model}/compare_fig", lambda: _comparison_fig(cfg, model, runs))
    return runs


def _comparison_fig(cfg, model, runs):
    """Overlay vorticity & TCWV evolution for the steps that completed."""
    labels = {"step1": "Step1 heating", "step2": "Step2 moist-lock",
              "step3": "Step3 moist-init", "step4": "Step4 wind-lock"}
    fig, (axv, axt) = plt.subplots(1, 2, figsize=(13, 4.6))
    for key, lab in labels.items():
        rd = runs.get(key)
        if not rd or not os.path.isdir(rd):
            continue
        d, vm, tm = tracker.timeseries(rd, cfg)
        axv.plot(d, vm * 1e5, "-o", ms=3, label=lab)
        axt.plot(d, tm, "-o", ms=3, label=lab)
    axv.set(title=f"{model}: 850 hPa vorticity anomaly",
            xlabel="day", ylabel=r"max vorticity (10$^{-5}$ s$^{-1}$)")
    axt.set(title=f"{model}: TCWV anomaly",
            xlabel="day", ylabel=r"max TCWV (kg m$^{-2}$)")
    for ax in (axv, axt):
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout()
    out = os.path.join(REPORT_DIR, f"compare_{model}.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[plot] {out}")
    return out


def write_report(cfg, args):
    lines = ["# Full-pipeline run report", ""]
    lines += [f"- background: **{cfg['background']}**, n_days: **{args.n_days}**, "
              f"amp: **{args.amp_K} K/day {args.heat_type}**, models: {args.models}",
              f"- cpu_num: {cfg['cpu_num']} (resolved to all cores)", "",
              "## Stage status", "", "| stage | status | minutes | detail |",
              "|---|---|---|---|"]
    for name, status, detail, secs in STAGES:
        lines.append(f"| {name} | {status} | {secs/60:.1f} | {detail[:80]} |")
    lines += ["", "## Comparison figures", ""]
    for model in args.models:
        f = f"compare_{model}.png"
        if os.path.exists(os.path.join(REPORT_DIR, f)):
            lines += [f"### {model}", f"![{model}]({f})",
                      "Step 1 should grow; Step 2 (moisture lock) should be suppressed.", ""]
    lines += ["## Per-run outputs", "",
              "Each run dir under `outputs/` holds `pert_NNN.npz`, `panels_vort.png`, "
              "`panels_tcwv.png`, `timeseries.png`, `config_used.json`.", ""]
    n_fail = sum(1 for _, s, _, _ in STAGES if s == "FAIL")
    lines.insert(1, f"\n**{n_fail} failed stage(s)** out of {len(STAGES)}.\n")
    with open(os.path.join(REPORT_DIR, "report.md"), "w") as fh:
        fh.write("\n".join(lines))
    print(f"\n[pipeline] report -> {os.path.join(REPORT_DIR, 'report.md')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["pangu", "fcnv2"])
    ap.add_argument("--background", default="JJA")
    ap.add_argument("--n_days", type=int, default=16)
    ap.add_argument("--amp_K", type=float, default=10.0)
    ap.add_argument("--heat_type", default="Deep")
    ap.add_argument("--y0", type=int, default=1991)
    ap.add_argument("--y1", type=int, default=2020)
    args = ap.parse_args()

    cfg = cfgmod.load_config({
        "background": args.background,
        "driver": {"n_days": args.n_days},
        "forcing": {"amp_K_per_day": args.amp_K, "heat_type": args.heat_type},
    })

    global REPORT_DIR
    REPORT_DIR = os.path.join(ROOT, "verification", "full_run", args.background)
    os.makedirs(REPORT_DIR, exist_ok=True)

    t0 = time.time()
    if args.background == "JJA":
        stage("prep_JJA", lambda: prep_jja(cfg, args.y0, args.y1))
    for model in args.models:
        run_model(cfg, model, args.amp_K, args.heat_type)
    write_report(cfg, args)
    print(f"\n[pipeline] TOTAL {(time.time()-t0)/60:.1f} min")
    print("================ STAGES ================")
    for name, status, detail, secs in STAGES:
        print(f"  {status:4s} {name} ({secs/60:.1f} min) {detail[:60]}")


if __name__ == "__main__":
    main()
