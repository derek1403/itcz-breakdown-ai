# ITCZ Breakdown in Global AI Weather Models

Reproduction of the **ITCZ breakdown** dynamics of Guinn & Schubert (1994) —
barotropic instability of an ITCZ-like vorticity strip rolling up into discrete
vortices — inside the global AI weather models **Pangu-Weather** and
**FourCastNet v2 (FCNv2)**, using a finite-time nonlinear perturbation method.

Run everything in the `pangu_env` conda environment:

```bash
PY=/home/pc/.conda/envs/pangu_env/bin/python
```

---

## 1. The method — Perpetual Background Re-centering

The growth mechanism is a **finite-time nonlinear perturbation evolution** (not a
tangent-linear Jacobian). With model operator `M` (one 6-h step), a *stationary*
background `u0` (a climatology or a single day), a frozen one-step drift
`B = M(u0)`, an initial perturbation `u'_0`, and per-step forcing `f_n`:

```
B = M(u0)
for n = 1 .. N:
    A_n   = u0 + u'_{n-1} + f_n      # state fed to M, ALWAYS anchored to steady u0
    #A_n   = clip_moisture(A_n)       # enforce q>=0 / 0<=r<=100% before M #在investigation中已經拿掉 
    u'_n  = M(A_n) - B              # peel the constant one-step model drift
    u'_n  = LOCK(u'_n)              # optional channel zeroing (Steps 2/4)
```

Why this scheme (vs. power-iteration or a free rollout):

1. Every input to `M` is `u0 + perturbation`, so the smooth ITCZ background never
   spins up chaotic synoptic weather.
2. Subtracting `B1` removes the model's constant one-step drift exactly.
3. `u'_n` accumulates the perturbation's nonlinear evolution over many days across
   a perfectly steady background. "Day N" = step `N × step_hours/24`.

Implemented in [driver.py](driver.py); verified exactly in
[tests/test_driver_math.py](tests/test_driver_math.py).

### Physical assumptions (explicit)

* **Heating pulse ≈ continuous rate.** The discrete thermal pulse added each 6-h
  step (e.g. **+2.5 K** for a 10 K/day rate, since `2.5 = 10 × 6/24`) is treated
  as a reasonable approximation of the *continuous diabatic heating rate* acting
  over that step. Same convention for the Step-4 moisture source.
* **Moisture physical bounds.** Before each call to `M`, the assembled state's
  moisture is clipped to physical ranges (`q ≥ 0` for Pangu; `0 ≤ r ≤ 100 %` for
  FCNv2) to avoid unphysical negative humidity driving spurious oscillations.
* **Cross-model moisture equivalence.** Moisture forcing is specified as a single
  generic specific-humidity rate (kg/kg per day); [layout.py](layout.py) converts
  it to each model's variables — Pangu `q`; FCNv2 `r` (via the background-`T`
  q→RH conversion) **plus** the consistent `tcwv` increment — so the same config
  gives physically equivalent forcing on both models.

---

## 2. The four experiments

| Step | Script | Initial `u'_0` | Forcing | Lock |
|------|--------|----------------|---------|------|
| 1 Standard ITCZ breakdown | `scripts/run_step1.py` | 0 | heating (7 d on, then off) | none |
| 2 Moisture locking | `scripts/run_step2.py` | 0 | heating | moisture `u'` → 0 each step |
| 3 Moisture-only init | `scripts/run_step3.py` | day-7 moisture anomaly from Step 1 | none | none |
| 4 Wind locking | `scripts/run_step4.py` | day-7 moisture anomaly | persistent moisture | wind `u'` → 0 each step |

Expected (cf. reference PDF): Step 1 grows vortices by ~day 9–12 with co-growing
TCWV; Step 2 suppresses growth (PDF p.5); Step 3 tests whether a pure moisture
anomaly can excite vortices; Step 4 isolates moisture evolution without wind
feedback.

---

## 3. Workflow

```bash
# --- Step 0: build background states u0 (writes ic/u0_<bg>_<model>.npz) ---
$PY scripts/prep_jja.py              # headline: JJA 1991-2020 climatology
$PY scripts/prep_djf.py             # DJF climatology
$PY scripts/prep_annual.py          # annual mean
$PY scripts/prep_ragasa.py          # 2025-09-17 00Z typhoon day (single day)
$PY scripts/prep_enso.py            # enso_pos / enso_neg / enso_neutral DJF composites

# --- Steps 1-4 (default model=pangu, background=JJA; see config.yaml) ---
$PY scripts/run_step1.py --model pangu --background JJA --amp_K 10 --heat_type Deep
$PY scripts/run_step2.py --model pangu --background JJA --amp_K 10
$PY scripts/run_step3.py --step1_dir outputs/JJA/step1_pangu_JJA_Deep_10Kday
$PY scripts/run_step4.py --step1_dir outputs/JJA/step1_pangu_JJA_Deep_10Kday

# Run the same on FCNv2 by adding --model fcnv2 (expects "no moisture evolution").
# Re-plot any finished run:
$PY scripts/plot_run.py outputs/<run_name> --model pangu
```

Outputs are grouped by background: each run writes under
`outputs/<background>/<run_name>/`: `pert_NNN.npz` (the perturbation `u'_n` per step),
`config_used.json`, `panels_vort.png`, `panels_tcwv.png`. The background's initial-field
figures (`ic_vort_<model>.png`, `ic_tcwv_<model>.png`, via `scripts/plot_background.py`)
sit at the `outputs/<background>/` level, alongside the run dirs. Cost on CPU ≈ 45 s/step
(Pangu), 14 s/step (FCNv2); a 16-day run is 64 steps.

---

## 4. Code map (`src/itcz/` package + `scripts/` entry points)

```
config.yaml                 # all paths/params (project root)
src/itcz/
  config.py                 # config loading + write-path resolution
  data/prep.py              # ERA5 -> model-IC (season/day averaging, packing)
  models/
    layout.py               # State container + per-model channel layout,
                            #   locking, clip_moisture, q<->r conversion, TCWV
    operators.py            # self-contained Pangu(ONNX) & FCNv2(torch) -> M.step()
    vendor/fourcastnetv2/   # vendored SFNO net (self-contained; weights read externally)
  experiment/
    forcing.py              # heating ellipse (by extent) + vertical profiles + moisture forcing
    driver.py               # Perpetual Background Re-centering loop; 4-step variants
  plotting/tracker.py       # vorticity/TCWV diagnostics, vortex track, maps, time series
scripts/                    # prep_*.py, run_step{1..4}.py, plot_run.py (thin CLIs)
tests/test_driver_math.py   # exact math + locking unit tests (mock operator)
verification/               # verification harness, figures, and its own README
```

The three top-level concerns map to the subpackages the way you asked:
**處理資料 → `data/`**, **載入模型 → `models/`**, **實驗 → `experiment/`** (plus
`plotting/` for diagnostics).

### Model channel facts (handled in `layout.py`)
* **Pangu**: `surface` (4,721,1440)=[msl,u10,v10,t2m]; `upper` (5,13,721,1440)=[z,q,t,u,v];
  levels 1000→50; **no TCWV channel** → TCWV = (1/g)∫q dp.
* **FCNv2**: (73,721,1440); sfc[0:8]=[10u,10v,100u,100v,2t,sp,msl,tcwv];
  upper u(8:21) v(21:34) z(34:47) t(47:60) r(60:73); levels 50→1000; direct TCWV channel.

All outputs stay inside this project directory; ERA5 / model-weight directories are
read-only.

---

## 5. Verification

```bash
$PY tests/test_driver_math.py        # exact recurrence + locking on a tiny mock grid
```

Full verification harness + figures + its own README live in `verification/`
(`python verification/run_verification.py`). Validated end-to-end: forcing ellipse
matches the PDF dashed contour (`verification/figures/02_forcing_ellipse.png`); Pangu's
integrated TCWV and FCNv2's TCWV channel agree (RMSE ~3.6 kg/m²) on the RAGASA IC; both
operators produce finite, physical one-step output on real ICs.

---

## 6. 為什麼有 `investigation/`（排查與試錯）

§1–5 的 pipeline 跑得起來，但拿去對 **`related_paper/AI-Forum.pdf`**（本專案早期作品、
原始碼已不可考的參考結果）時，結果對不上：渦度量級過強、結構不像、TCWV 偏低。為了釐清
**「到底是哪個環節造成落差」**，另開 `investigation/` 做系統性診斷與試錯——**不動 §1–5 主程式**，
全部用獨立腳本驗證，再把確定有效的改動回寫主程式。

**逐項排查的結論（詳見報告）：**

* **已排除（不是問題）**：
  * 方位/經度 — Pangu I/O 方位正確（一步漂移 RMS 0.85 K）。
  * 初始場 — 我們自建的 `u0_paperDJF` ≈ 論文官方 `mean_DJF.h5`（熱帶 RMSE < 1%）。
  * 渦度診斷 — 對擾動 `u'` 直接算渦度是對的（渦度線性：`ζ(u') = ζ(u'+B) − ζ(B)`，實測差 1e-7）。
* **校準到位**：加熱**振幅** 10 → ~1.5–3 K/day（原本 10 把系統打進過度非線性）、
  加熱**區域** → 5–15°N / 125°E–95°W。
* **找到關鍵變因 = 加熱「垂直分布」**：Deep/Stratiform/Shallow 三種 sin 分布在 1000 hPa 都歸零
  （邊界層不加熱），TCWV 卡在 ~30；改成**均勻加熱（含低層 1000–250 hPa）**後，低層加熱驅動水氣輻合，
  TCWV 才上到 ~45（對上 AI-Forum）。**故 §1 的 `clip_moisture` 已在 investigation 驗證後拿掉**
  （與論文一致），垂直分布新增 `uniform` 選項。
* **本質限制**：ITCZ breakdown 是**混沌**正壓不穩定，逐日**確切渦旋位置**對微小 IC 差異極敏感
  （0.2 K → day12 場相關係數 0.42），只能對齊統計/定性特徵，不能逐點重現（論文亦有此警告）。
* **仍未解（待討論）**：day1 我們是全域緯向條紋、AI-Forum 是 2D 紅藍斑塊（疑重力波）；
  陸地較早長出渦度；中緯度 day9 後偏活躍。

**進去看哪裡：**

* **[investigation/進度報告0625_總整理.md](investigation/進度報告0625_總整理.md)** — 大統整（內嵌 2D 渦度圖、
  AI-Forum 目標對照、已排除變因、最佳結果、未解問題、下一步），對外討論看這份。
* `investigation/進度報告0625_*.md` — 各階段時間戳報告；`investigation/FINDINGS_AND_EXPERIMENTS.md`、
  `ALGORITHM_AND_SETUP.md` — 細節與實驗紀錄。
* `investigation/standalone/` — 可攜單檔腳本（h5→npy、跑 Pangu 加熱、畫渦度），純 for 迴圈、好讀。
* `investigation/figs/` — 所有圖；`investigation/ref/` — 下載的論文官方 code 與資料（**不上 git**）。
