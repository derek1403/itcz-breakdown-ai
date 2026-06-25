# DJF run — scientific summary (Steps 1–4, Pangu & FCNv2)

Config: background **DJF (1991–2020)**, heating **Deep +10 K/day**, ellipse 165°W /
120°E→90°W, **16 days** (64 × 6 h). All **14 stages succeeded** (0 failures), ~7.3 h.
Auto status: [report.md](report.md). Tracked-peak anomalies in the ITCZ band
(0–20°N, 120°E–90°W):

| run | peak vorticity (10⁻⁵ s⁻¹) | @day | peak TCWV (kg m⁻²) | @day |
|-----|--------------------------:|-----:|-------------------:|-----:|
| **pangu** S1 heating       | **80.1** | 11.8 | **88.6** | 14.8 |
| pangu S2 moisture-lock     | 18.4 |  9.2 | 0.0 | – |
| pangu S3 moisture-init     | 73.9 | 12.2 | 85.8 | 15.5 |
| pangu S4 wind-lock         | 0.0 | – | 60.5 | 16.0 |
| **fcnv2** S1 heating       | **115.9** | 16.0 | 47.0 | 15.8 |
| fcnv2 S2 moisture-lock     | 17.1 |  8.8 | 0.0 | – |
| fcnv2 S3 moisture-init     | 68.3 | 16.0 | 45.3 | 15.8 |
| fcnv2 S4 wind-lock         | 0.0 | – | 36.1 | 14.5 |

Plots: [compare_pangu.png](compare_pangu.png), [compare_fcnv2.png](compare_fcnv2.png).
Initial field: `outputs/DJF/ic_vort_pangu.png`, `outputs/DJF/ic_tcwv_pangu.png`.

## Findings (and DJF-vs-JJA comparison)

**Pangu — same mechanism as JJA, slightly stronger.** Step 1 grows to ζ′≈80 (JJA 64)
and TCWV′≈89 (JJA 86); Step 2 moisture-lock collapses it to ζ′≈18, TCWV≡0; Step 3
(moisture-only seed) grows vigorously (ζ′≈74); Step 4 (wind-lock) keeps ζ′=0 while TCWV
accumulates (≈60). The moisture-essential result is robust across season.

**Note on the fixed NH heating in DJF.** The heating ellipse is held at 7.5°N in all
seasons, so DJF tests the *same forced structure* on a different background. The
breakdown still develops, i.e. the imposed ITCZ heating drives the instability even when
the DJF NH background ITCZ is weaker — the background modulates but does not prevent it.

**FCNv2 — flat then a vigorous LATE breakdown.** Unlike FCNv2/JJA (weak throughout),
FCNv2/DJF vorticity stays ~15–20 until ~day 12, then climbs steeply to **ζ′≈116 by day
16** (Step 1) and ≈68 (Step 3). The day-15 spatial panel
(`outputs/DJF/step1_fcnv2_DJF_Deep_10Kday/panels_vort.png`) shows **coherent vortex
filaments**, not grid noise, so this reads as a real late, explosive breakdown rather
than an artifact. Caveats to keep in mind:
- The peak is at the **last day (16)** and still rising — the run does not capture its
  saturation; extending to ~20 d (D4) would show where it tops out.
- Magnitude (116) exceeds Pangu's, and the tracked max is a single in-band maximum;
  some contribution near domain edges/coasts is visible. Worth confirming with a longer
  run and/or a tighter `track_band` before over-interpreting the absolute value.
- Moisture-lock (S2) stays flat (~17) the whole time, so the late growth **is**
  moisture-dependent in FCNv2/DJF — a contrast with FCNv2/JJA where S1≈S2 throughout.

## Reproduce
```bash
PY=/home/pc/.conda/envs/pangu_env/bin/python
$PY scripts/run_full_pipeline.py --models pangu fcnv2 --background DJF
```
