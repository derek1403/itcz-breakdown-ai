# Pending decisions (for your review)

I kept working autonomously and did everything I'm confident about. A few choices
need your call before I commit large compute. Each item lists the **question**, my
**recommendation**, and **what I did by default** so nothing is blocked. Just reply
with the numbers + choices and I'll execute quickly.

Status when I wrote this: the headline pipeline (JJA, Pangu **and** FCNv2, Steps 1–4)
was running and healthy. Pangu Step 1 already reproduced the ITCZ-breakdown roll-up
(see `outputs/JJA/step1_pangu_JJA_Deep_10Kday/panels_vort.png`).

---

## D1. Experiment scope across background states
**Q:** Run Steps 1–4 on the *other* backgrounds too (DJF, annual, RAGASA, ENSO+/–/0),
or keep JJA as the only experiment set?
- **Recommendation:** JJA is the headline (done). For sensitivity, run **RAGASA** and
  **ENSO+ vs ENSO−** with Step 1 only (not the full 4 steps) — that already shows how
  the background state changes the breakdown. The full matrix (7 bg × 2 models × 4
  steps ≈ 56 runs, ~1–2 days CPU) is likely overkill.
- **Default I did:** built the **ICs for all 7 backgrounds** (you asked for all 7), but
  ran experiments on **JJA only**. Other backgrounds are ready to run on demand.
- **Cost:** each background = ~3.5 h Pangu + ~1 h FCNv2 for all 4 steps.

## D2. Forcing variants (the PDF p.4 three-curve panel)
**Q:** The PDF time-series panel has 3 curves. Reproduce them by running extra
variants? Options: **(a)** 3 vertical profiles Deep/Stratiform/Shallow at 10 K/day;
**(b)** amplitudes 10 vs 5 K/day; **(c)** both.
- **Recommendation:** (a) Deep/Stratiform/Shallow at 10 K/day on **JJA Pangu** — that's
  the most likely meaning and gives a direct 3-curve comparison.
- **Default I did:** only **Deep, 10 K/day** so far.
- **Cost:** +2 Pangu runs (~1.7 h) for the two extra profiles.

## D3. ENSO classification thresholds
**Q:** I used ONI |≥1.5| = strong El Niño / La Niña, |ONI|<0.5 = neutral (6 closest to
zero), years 1981–2025. OK, or different thresholds/years?
- **Recommendation:** keep defaults.
- **Default I did:** built `enso_pos/neg/neutral` ICs with these (see
  `pending_decisions/phase2_status.md` for the exact years chosen, and whether the ONI
  download succeeded — if no network, this is skipped and flagged there).

## D4. Integration length
**Q:** `n_days = 16` (PDF runs to day 16). Keep, or extend (e.g. 20 d to see late
vortex mergers)?
- **Recommendation:** keep 16.
- **Default I did:** 16.

## D5. FYI (no action needed unless you want to)
- One corrupt ERA5 source file (`upper/r/2014-08`, truncated) — handled by skipping it;
  details in `verification/data_integrity_JJA.md`. Re-download only if you want that one
  month back (negligible for a 30-yr mean; affects FCNv2 RH only).
- Default heating center is **165°W (7.5°N), 120°E→90°W** per the PDF; change in
  `config.yaml` if you want it narrower/wider.
- **Disk usage:** the JJA run wrote **~95 GB** (8 runs × 64 full-state npz). All 7
  backgrounds at full scope would be ~0.7 TB. If that's a concern I can (a) save only
  every Nth step (`driver.save_every`), or (b) store only the diagnostic channels
  needed for plots (850 u/v + moisture/tcwv) instead of the full state — ~20× smaller.
  Say the word and I'll switch the default; existing runs can also be thinned in place.

---

### My suggested "good default" if you just want me to proceed
D1 = RAGASA + ENSO± with Step 1 only; D2 = run Deep/Stratiform/Shallow on JJA Pangu;
D3 = keep; D4 = keep. Tell me "go with suggested defaults" and I'll run them.

---

## Ready-to-run commands (so it launches in one step)
All assume `PY=/home/pc/.conda/envs/pangu_env/bin/python` and cwd = project root.
Background ICs for these are built by phase 2 (see `phase2_status.md`).

**D2 — heating-profile variants on JJA Pangu (3-curve panel):**
```bash
$PY scripts/run_step1.py --model pangu --background JJA --heat_type Stratiform
$PY scripts/run_step1.py --model pangu --background JJA --heat_type Shallow
# then overlay with the existing Deep run:
$PY scripts/plot_run.py outputs/JJA/step1_pangu_JJA_Stratiform_10Kday --model pangu
```
(amplitude variant instead: add `--amp_K 5`)

**D1 — Step 1 on other backgrounds (sensitivity):**
```bash
for BG in ragasa enso_pos enso_neg; do
  $PY scripts/run_step1.py --model pangu --background $BG
done
```

**Full Steps 1–4 on another background (expensive, ~4.5 h each):**
```bash
$PY scripts/run_full_pipeline.py --models pangu fcnv2 --background DJF
```

