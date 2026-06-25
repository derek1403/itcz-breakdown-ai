"""Phase 2: build the remaining background ICs (DJF, annual, ENSO +/-/0).

Waits for the main pipeline to finish (so it does not contend for CPU), then builds
the ICs for all remaining background states.  Experiments are NOT run here -- that is
a scope decision (see pending_decisions/README.md, D1).  Writes a status report to
pending_decisions/phase2_status.md.

    python scripts/build_remaining_backgrounds.py
"""
import os
import time
import traceback
import urllib.request

import _bootstrap  # noqa: F401
from itcz import config as cfgmod
from itcz.data import prep

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "verification", "full_run", "report.md")
STATUS = os.path.join(ROOT, "pending_decisions", "phase2_status.md")
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

log = []


def note(s):
    print(s, flush=True)
    log.append(s)


def _pipeline_running():
    """True if a run_full_pipeline.py process is alive (avoids tripping on a stale
    report.md left by an earlier run)."""
    try:
        import subprocess
        out = subprocess.run(["pgrep", "-f", "run_full_pipeline.py"],
                             capture_output=True, text=True)
        return bool(out.stdout.strip())
    except Exception:
        return False


def wait_for_phase1(timeout_h=12):
    """Block until the main pipeline has finished: report present AND no pipeline
    process alive."""
    note(f"[phase2] waiting for phase 1 ({REPORT}) ...")
    t0 = time.time()
    while _pipeline_running() or not os.path.exists(REPORT):
        if time.time() - t0 > timeout_h * 3600:
            note("[phase2] WARNING: timed out waiting for phase 1; proceeding anyway")
            return
        time.sleep(120)
    time.sleep(30)  # grace so the process fully exits
    note(f"[phase2] phase 1 done after {(time.time()-t0)/60:.0f} min; starting prep")


def build(name, fn):
    try:
        fn()
        note(f"[phase2] OK   {name}")
    except Exception as e:
        note(f"[phase2] FAIL {name}: {e}")
        note("```\n" + traceback.format_exc() + "```")


def build_djf(cfg):
    pairs = prep.djf_pairs(range(1991, 2021))
    fields = prep.season_fields_pairs(cfg, pairs)
    prep.save_ic(cfg, fields, "DJF")
    prep.summarize_ic(cfg, "DJF", "pangu")


def build_annual(cfg):
    fields = prep.season_fields(cfg, range(2000, 2020), months=list(range(1, 13)))
    prep.save_ic(cfg, fields, "annual")
    prep.summarize_ic(cfg, "annual", "pangu")


def fetch_oni(cfg):
    cache = os.path.join(cfg["paths"]["ic_dir"], "oni.ascii.txt")
    os.makedirs(cfg["paths"]["ic_dir"], exist_ok=True)
    if not os.path.exists(cache):
        urllib.request.urlretrieve(ONI_URL, cache)
    djf = []
    with open(cache) as fh:
        next(fh)
        for line in fh:
            p = line.split()
            if len(p) >= 4 and p[0] == "DJF":
                djf.append((int(p[1]), float(p[3])))
    return djf


def build_enso(cfg):
    djf = [(yr, a) for yr, a in fetch_oni(cfg) if 1981 <= yr <= 2025]
    pos = [yr for yr, a in djf if a >= 1.5]
    neg = [yr for yr, a in djf if a <= -1.5]
    neutral = [yr for _, yr in sorted([(abs(a), yr) for yr, a in djf if abs(a) < 0.5])[:6]]
    note(f"[phase2] ENSO years -> pos={pos} neg={neg} neutral={sorted(neutral)}")
    for nm, yrs in (("enso_pos", pos), ("enso_neg", neg), ("enso_neutral", neutral)):
        fields = prep.season_fields_pairs(cfg, prep.djf_pairs(yrs))
        prep.save_ic(cfg, fields, nm)
        prep.summarize_ic(cfg, nm, "pangu")


def main():
    cfg = cfgmod.load_config()
    wait_for_phase1()
    build("DJF", lambda: build_djf(cfg))
    build("annual", lambda: build_annual(cfg))
    build("ENSO (pos/neg/neutral)", lambda: build_enso(cfg))

    os.makedirs(os.path.dirname(STATUS), exist_ok=True)
    with open(STATUS, "w") as fh:
        fh.write("# Phase 2: remaining background ICs\n\n")
        fh.write("Built after the main pipeline finished (no CPU contention). ICs land "
                 "in `ic/u0_<bg>_<model>.npz`. Experiments on these are pending D1.\n\n")
        fh.write("```\n" + "\n".join(log) + "\n```\n")
    note(f"[phase2] status -> {STATUS}")


if __name__ == "__main__":
    main()
