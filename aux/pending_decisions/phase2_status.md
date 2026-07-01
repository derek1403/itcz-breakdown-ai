# Phase 2: remaining background ICs

ICs land in `ic/u0_<bg>_<model>.npz`. Experiments on these are pending D1.

**Correction:** the auto-note below says "phase 1 done after 1 min" — that is wrong.
A **stale `report.md` from the first (failed) pipeline run** was still present, so the
wait tripped immediately and phase 2 actually ran **concurrently** with the main
pipeline (~02:59–04:38), contending for CPU and slowing both. No incorrect results —
all 7 background ICs are built and validated — just slower than intended. The waiter
logic has been hardened (now also requires that no `run_full_pipeline` process is
alive) so a re-run would behave correctly.

ENSO DJF years selected (ONI |≥1.5| strong, |ONI|<0.5 neutral·6 closest):
- **enso_pos:** 1983, 1992, 1998, 2010, 2016, 2024
- **enso_neg:** 1989, 1999, 2000, 2008
- **enso_neutral:** 1982, 1990, 1993, 1994, 2002, 2017

```
[phase2] waiting for phase 1 (/wk2/pc/AI_models/itcz-breakdown-ai/verification/full_run/report.md) ...
[phase2] phase 1 done after 1 min; starting prep
[phase2] OK   DJF
[phase2] OK   annual
[phase2] ENSO years -> pos=[1983, 1992, 1998, 2010, 2016, 2024] neg=[1989, 1999, 2000, 2008] neutral=[1982, 1990, 1993, 1994, 2002, 2017]
[phase2] OK   ENSO (pos/neg/neutral)
```
