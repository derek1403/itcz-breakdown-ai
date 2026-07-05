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
[aux/tests/test_driver_math.py](aux/tests/test_driver_math.py).

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
$PY scripts/prep_jas.py              # headline: JAS climatology — validated AI-Forum IC (§7)
$PY scripts/prep_jja.py             # JJA 1991-2020 climatology
$PY scripts/prep_djf.py             # DJF climatology
$PY scripts/prep_annual.py          # annual mean
$PY scripts/prep_ragasa.py          # 2025-09-17 00Z typhoon day (single day)
$PY scripts/prep_enso.py            # enso_pos / enso_neg / enso_neutral DJF composites

# --- Steps 1-4, per-experiment layout (recommended): one manifest drives all 4 steps ---
# The manifest outputs/<bg>/<spec>/config.yaml holds the VARIABLE setup (model, step_hours,
# background, driver, heat_type, amp); the root config.yaml supplies shared defaults
# (paths, plot, forcing geometry). --exp reads that manifest and writes to <spec>/stepN.
EXP=outputs/JAS/pangu24_Deep_2.5Kday_gauss
$PY scripts/run_step1.py --exp $EXP
$PY scripts/run_step2.py --exp $EXP
$PY scripts/run_step3.py --exp $EXP          # seeds from $EXP/step1 by default
$PY scripts/run_step4.py --exp $EXP          # seeds from $EXP/step1 by default

# Extend/resume any finished run to more days (full-state warm-start from its last pert):
$PY scripts/resume_run.py $EXP/step1 --n_days 20 --forcing_days 20

# Legacy flat layout still works (no --exp): writes to outputs/<bg>/step1_<model>_<bg>_<heat>_<amp>Kday/
$PY scripts/run_step1.py --model pangu --background JAS --amp_K 2.5 --heat_type Deep

# Re-plot any finished run (path-based; works on either layout):
$PY scripts/plot_run.py $EXP/step1 --model pangu
```

**Output layout (per-experiment).** Each spec folder groups one experiment's four steps:
`outputs/<background>/<spec>/` holds `config.yaml` (the manifest) + `step1/ … step4/`, and each
`stepN/` holds `pert_NNN.npz` (the perturbation `u'_n` per step), `config_used.json` (the
fully-resolved cfg actually run), `panels_vort.png`, `panels_tcwv.png`. The spec folder also holds
`heating_dist_check.png` — its own 4-panel heating figure (paper Fig. 2), generated per-spec by
`scripts/plot_heating.py --all <bg>` (`tracker.plot_heating_dist`, cfg-driven). Spec-folder naming =
`<model><step_hours-for-pangu>_<heat>_<amp>Kday_<method>` (e.g. `pangu24_Deep_2.5Kday_gauss`,
`fcnv2_Deep_2.5Kday_gauss`). Background-level figures (`ic_*`) and the shared moisture seeds sit at
`outputs/<background>/`. Cost on CPU ≈ 45 s/step (Pangu),
14 s/step (FCNv2). (Backgrounds other than JAS are still in the legacy flat layout pending
the same migration.)

---

## 4. Code map — 完整結構見 [tree.md](tree.md)

專案結構總覽（只含程式/文件骨架、不含圖片與資料）集中在根目錄的 **[tree.md](tree.md)**，
並由該檔連到每個資料夾自己的 README。核心 `src/itcz/` 套件：

```
config.yaml                 # all paths/params (project root)
src/itcz/
  config.py                 # config loading + write-path resolution
  data/prep.py              # ERA5 -> model-IC (season/day averaging, packing)
  models/layout.py          # State container + per-model channel layout, locking, clip_moisture, q<->r, TCWV
  models/operators.py       # self-contained Pangu(ONNX) & FCNv2(torch) -> M.step()
  models/vendor/fourcastnetv2/   # vendored SFNO net (weights read externally)
  experiment/forcing.py     # heating (separable 2D Gaussian) + vertical profiles + moisture forcing
  experiment/driver.py      # Perpetual Background Re-centering loop; 4-step variants
  plotting/tracker.py       # vorticity/TCWV diagnostics, vortex track, maps, time series
scripts/                    # prep_*.py, run_step{1..4}.py, plot_*.py (thin CLIs)
aux/tests/test_driver_math.py  # exact math + locking unit tests (mock operator)
aux/verification/           # verification harness, figures, and its own README
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
$PY aux/tests/test_driver_math.py        # exact recurrence + locking on a tiny mock grid
```

Full verification harness + figures + its own README live in `aux/verification/`
(`python aux/verification/run_verification.py`). Validated end-to-end: forcing ellipse
matches the PDF dashed contour (`aux/verification/figures/02_forcing_ellipse.png`); Pangu's
integrated TCWV and FCNv2's TCWV channel agree (RMSE ~3.6 kg/m²) on the RAGASA IC; both
operators produce finite, physical one-step output on real ICs.

---

## 6. 為什麼有 `aux/investigation/`（排查與試錯）

§1–5 的 pipeline 跑得起來，但拿去對 **`aux/related_paper/AI-Forum.pdf`**（本專案早期作品、
原始碼已不可考的參考結果）時，結果對不上：渦度量級過強、結構不像、TCWV 偏低。為了釐清
**「到底是哪個環節造成落差」**，另開 `aux/investigation/` 做系統性診斷與試錯——**不動 §1–5 主程式**，
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

* **[aux/investigation/進度報告0625_總整理.md](aux/investigation/進度報告0625_總整理.md)** — 大統整（內嵌 2D 渦度圖、
  AI-Forum 目標對照、已排除變因、最佳結果、未解問題、下一步），對外討論看這份。
* `aux/investigation/進度報告0625_*.md` — 各階段時間戳報告；`aux/investigation/FINDINGS_AND_EXPERIMENTS.md`、
  `ALGORITHM_AND_SETUP.md` — 細節與實驗紀錄。
* `aux/investigation/standalone/` — 可攜單檔腳本（h5→npy、跑 Pangu 加熱、畫渦度），純 for 迴圈、好讀。
* `aux/investigation/figs/` — 所有圖；`aux/investigation/ref/` — 下載的論文官方 code 與資料（**不上 git**）。

---

## 7. ✅ 突破：找到原作設定（JAS IC）並成功重現 — `aux/investigation/aiforum_repro/`

> 2026-06，**對上 AI-Forum 了**。完整定案見
> [aux/investigation/aiforum_repro/結果.md](aux/investigation/aiforum_repro/結果.md)，
> 試錯過程見 [aux/investigation/aiforum_repro/歷程.md](aux/investigation/aiforum_repro/歷程.md)。

**關鍵發現**：找到原作的原始設定圖
[`aux/related_paper/horizontal_heating.png`](aux/related_paper/horizontal_heating.png)（deep convective,
2.5 K/day, center 10°N）與 [`aux/related_paper/IC.png`](aux/related_paper/IC.png)（標題寫明
**1979–2019 JAS climatology**）。**原作 IC 是 JAS（夏季），不是先前一直用的 DJF**、**原作加熱範圍是最後才被接露的**—— 這正是過去對不上的主因：冬季北半球 10°N 沒有強 ITCZ，Deep 加熱起不來、加熱範圍與量值要多種嘗試導致效率不彰。

**成功設定**（`aiforum_repro/1_run_pangu.py`，semi-linear/make_steady、24h Pangu、16 天）：
* **IC = JAS** 氣候平均（`ref/ERA5_means/mean_JAS.h5`；`config.yml: mean_state_season: JAS`。
  注意 `fetch_mean_state/fetch_tendency` 預設 DJF，務必傳 `season`）。
* **水平**：`perturbations_ellipse(lat,lon, k=8, ylat=10, xlon=195, L=25000km)`
  = `cos(8(φ−10°))` 緯向波瓣（約 −1.25~21.25°N）× Gaspari-Cohn 經向（中心 165°W、範圍約 60°E~30°W）。
* **垂直**：Deep = `sin(π·(p−200)/800)`（1000–200 hPa、峰值 600 hPa）。
* **振幅**：2.5 K/day。

**結果**：peak 850hPa **ζ' ~39.8 ×10⁻⁵**（day13 達峰後衰減）、peak **TCWV' ~45.3 mm**（day15），
day12–15 沿 10°N 捲出**離散渦旋** —— 量級與結構都對上目標
（[aiforum_repro/figs/vort_JAS_Deep_amp2.5.png](aux/investigation/aiforum_repro/figs/vort_JAS_Deep_amp2.5.png)、
[timeseries.png](aux/investigation/aiforum_repro/figs/timeseries.png)）。

**對照測試（JAS/DJF × 正常/inverse）**：四組 ζ 峰
**JAS 正常 39.8 ≫ DJF inverse 30.9 > DJF 正常 21.3 > JAS inverse 19.2**，
反應強弱 ∝ 被加熱的 5–25°N 帶上「真實 ITCZ 有多強/多濕」，再次確認**季節（IC）是關鍵變因**。
（`inverse` = 一開始把 IC+tendency 的 lat 方向 `[::-1]` 翻轉再丟 Pangu。）

**怎麼跑**：
```bash
cd aux/investigation/aiforum_repro
PY=/home/pc/.conda/envs/pangu_env/bin/python
$PY 0_plot_heating.py     # 加熱+IC確認圖
$PY 1_run_pangu.py Deep   # 主結果（JAS）
$PY 2_plot_results.py     # vort/tcwv/timeseries panels
```
> 規則：要更動任何 py，**先複製一份新檔改名再執行**（如 DJF 對照用的 `1_run_pangu_djf.py`），
> 勿直接改定案檔（`config.yml`、`panguweather_utils.py`、`0_plot_heating.py`、`1_run_pangu.py`、`2_plot_results.py`）。

---

## 8. ✅ investigation 收尾：validated 設定已回寫主程式

已確認主 pipeline 的 `B1=M(u0)` re-centering 與 aiforum_repro 的 `make_steady`（減模型 24h drift）
**數學等價**，落差純粹來自參數。故將 §7 的 validated 設定回寫為 **`config.yaml` 預設**並重跑 Step 1–4：

* `background: JAS`、`forcing.amp_K_per_day: 2.5`、`heat_type: Deep`
* 水平分離式 2D 高斯：中心 10°N/195°E、σ_lat≈6.4°、σ_lon≈65°（`horizontal_ellipse` 本就是高斯，僅調 sigma）
* `driver.clip_moisture: false`（investigation 驗證後拿掉）；`forcing.py` 新增 `uniform` 垂直選項備用
* stepping 維持 6 h（每日加熱等比縮放；AI-Forum 原以 24 h 驗證，若差距大可切 `pangu_weather_24.onnx`）

Step 1–4 於 Pangu 與 FCNv2 上重跑，輸出見 `outputs/JAS/`。investigation 目錄整體歸檔於 `aux/`。

### 8.1 📁 outputs/JAS/ 已改為 per-experiment layout（2026-07）

`outputs/JAS/` 已從舊的扁平 `step<N>_<model>_JAS_...` 命名，改成**每個實驗一個 spec 資料夾、其下放 step1–4**：

```
outputs/JAS/pangu24_Deep_2.5Kday_gauss/     # ← 主線（24h、Deep、2.5K/day、gauss；step1 已延長到 20 天）
    config.yaml                             # manifest：只放變異參數，跑法 run_stepN.py --exp <此資料夾>
    step1/ step2/ step3/ step4/             # 各步的 pert_NNN.npz + config_used.json + 圖
outputs/JAS/fcnv2_Deep_2.5Kday_gauss/       # 對應 FCNv2 主線
outputs/JAS/{pangu6,fcnv2}_Deep_{5,10}Kday_gauss/          # 其他 amp（多為 step1–2）
outputs/JAS/pangu6_Deep_2.5Kday_gauss/          # 6h 主線（sustained/fd20），step1–4 一套
outputs/JAS/pangu6_Deep_2.5Kday_gauss_pulse7d/  # 6h 加熱 7 天後關（fd7）的替代版，step1–4 一套
```

**一個 `config.yaml` 只服務一組 step1–4**：若某步的來源不確定，就依該 spec 的 manifest 重跑一組覆蓋（例如原
`moistinit6h`/`windlock6h` 來源不明，改由主線 manifest 重跑 step3/4）。命名 =
`<model><step_hours(僅pangu)>_<heat>_<amp>Kday_<method>[_變體]`。**其他背景（DJF/JJA/paper*/ragasa）仍為舊扁平命名，
待以同一方式遷移**（遷移為同磁碟 rename，`config_used.json` 原樣保留，另生成 spec 層 `config.yaml` manifest）。
