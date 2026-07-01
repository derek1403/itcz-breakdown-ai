# Verification

Reproduce everything here with:

```bash
/home/pc/.conda/envs/pangu_env/bin/python verification/run_verification.py
# (add --no_model to run only the fast, no-model checks)
```

It regenerates every figure in [figures/](figures/) and prints a summary. Below is
what each check tests and the result obtained on this machine (RAGASA IC,
`pangu_env`). All six checks pass.

| # | Check | Result |
|---|-------|--------|
| 1 | Driver math + locking (exact, mock operator) | **PASS** |
| 2 | Forcing ellipse matches PDF extent | west **120°E**, east **90°W**, center **165°W** |
| 3 | Vertical heating profiles | Deep/Stratiform/Shallow as specified |
| 4 | TCWV: Pangu ∫q dp vs FCNv2 channel | RMSE **3.56**, bias **0.43** kg/m² |
| 5 | Operator one step finite & physical | Pangu 44 s, FCNv2 12 s, T850 230–304 K, finite |
| 6 | End-to-end mini run grows vorticity | vort_max **0 → 7.9 ×10⁻⁵ s⁻¹**, TCWV **0 → 8.2 kg/m²** |

---

## Check 1 — driver math & locking (the core algorithm)

Runs [../tests/test_driver_math.py](../tests/test_driver_math.py) on a tiny
synthetic grid with mock operators where the answer is known analytically:

* **Re-centering recurrence** — with `M(x)=α·x`, the driver must produce
  `u'_1 = α·f` and `u'_2 = α(1+α)·f`, and `u'_0 ≡ 0`. Verified to `1e-6`. This is
  the exact check that `A_n = u0 + u'_{n-1} + f_n` is anchored to `u0` and that
  `B1 = M(u0)` is subtracted correctly.
* **Moisture lock** — with a temperature→moisture coupling operator, the moisture
  perturbation is nonzero when unlocked and **exactly 0** at every step when locked.
* **Wind lock** — `u,v` (and `u10,v10`) perturbations forced to 0.
* **clip_moisture** — enforces `q ≥ 0` without touching other channels.

Result: `ALL TESTS PASSED`.

## Check 2 — forcing ellipse vs the PDF dashed contour

![ellipse](figures/02_forcing_ellipse.png)

The ellipse is now specified by **geographic extent** with proper lat/lon axes. The
dashed boundary is centered at **165°W (7.5°N)** and reaches **120°E** on the west
and **90°W** on the east — matching the reference PDF. (`lon_halfwidth = 75°`,
`lat_halfwidth = 6°`.)

## Check 3 — vertical heating profiles

![vprofiles](figures/03_vertical_profiles.png)

Deep (mid-trop max ~600 hPa), Stratiform (upper heating / lower cooling), and
Shallow (low-level max ~700 hPa), all confined to 200–1000 hPa.

## Check 4 — cross-model TCWV consistency

![tcwv](figures/04_tcwv_agreement.png)

Two *independent* TCWV diagnostics on the same RAGASA atmosphere agree closely:
Pangu's column integral `(1/g)∫q dp` (13 levels) vs FCNv2's prognostic `tcwv`
channel. RMSE 3.56 kg/m² / bias 0.43 kg/m² on values up to ~70 kg/m² (~5%); the
residual sits along coastal/sharp-gradient zones, as expected from coarse 13-level
integration. This validates the Pangu TCWV diagnostic used in the plots.

## Check 5 — operators run on real data

![operator](figures/05_operator_step.png)

One 6-h step of each model on the RAGASA IC: output is finite and physical (T850
230–304 K before and after). Confirms the self-contained Pangu (ONNX) and FCNv2
(vendored SFNO + torch) loaders and the unified `M.step()` interface work on real
initial conditions. Timing: Pangu ≈ 44 s/step, FCNv2 ≈ 12 s/step (CPU).

## Check 6 — end-to-end growth

![integration](figures/06_integration_vort.png)

A short real run (Pangu, RAGASA, Deep +10 K/day) through the full
driver→save→diagnostics→plot chain. The 850-hPa vorticity anomaly emerges **inside
the heating ellipse** and grows together with TCWV:

```
day        0.00   0.25   0.50
vort_max   0.00   3.19   7.91   (10^-5 s^-1)
tcwv_max   0.00   4.11   8.22   (kg m^-2)
```

This is the expected early-phase ITCZ-breakdown signature (co-growing vorticity and
moisture in the right location). Full roll-up into discrete vortices is expected by
~day 9–12 in a complete 16-day run.

---

### Not covered here (cost)

The full multi-decadal `prep_jja.py` (30-yr average) and the complete 64-step
experiments (Steps 1–4) are left to run on demand — Check 6 exercises the identical
code path at short length. A 16-day run ≈ 48 min (Pangu) / 15 min (FCNv2).
