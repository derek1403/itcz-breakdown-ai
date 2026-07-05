# FIGURES_TODO — 執行狀態（2026-07-05 更新）

```說明
執行紀錄 + 排程。你重整了 outputs/（pangu24_Deep_2.5Kday_gauss/step{1..4} 這種
「一個實驗一個資料夾、步驟為子資料夾」的結構，每個資料夾都有 heating_dist_check.png
與 config.yaml），make_figs.py 的路徑常數我已跟上新結構。
目前本機還有 pangu 在跑 —— 下面「排隊中」的 run 等 GPU 空了再跑（或丟 leibniz）。
```

## 圖 ↔ run 對應（新結構）

| 圖 | 來源 |
|---|---|
| Fig 2（四合一強迫圖） | `../outputs/JAS/pangu24_Deep_2.5Kday_gauss/heating_dist_check.png` |
| Fig 3 / 4a / 4b | `pic/fig3_panels_vort.png` 等（你重繪版，源 `pangu24_Deep_2.5Kday_gauss/step1`） |
| Fig 5 / 7 | `make_figs.py fig5 / fig7`（路徑已更新到 `pangu24_.../step{1..4}` 與 DJF run） |
| Fig 8 / D1 | `pangu24_.../step1` vs `pangu6_Deep_2.5Kday_gauss/step1` |
| Fig 9 | `make_figs.py fig9`（源 `pangu24_.../step1` + obs fulldisk） |

## 排隊中（CPU 空了再跑）

### Q2. Day-1 manifold-shock 判別實驗（logic/discussion4.3.md §6；都很便宜）

config 級細節（pangu 一律 `device: cpu` 全核，見 Q5 教訓）：

1. **圓形斑強迫**：spec `outputs/JAS/pangu24_Deep_2.5Kday_gauss_circle/`，
   config = 主線複製 + `device: cpu`、`driver: {n_days: 3, forcing_days: 3}`、
   `forcing: {lat_halfwidth: 12.8, lon_halfwidth: 12.8}`（σφ=σλ≈6.4°，中心不動）。
   只跑 step1。判讀：day-1 條紋方向/全域性是否與橢圓版相同。
2. **搬到 10°S**：spec `outputs/JAS/pangu24_Deep_2.5Kday_gauss_10S/`，
   config = 主線複製 + `device: cpu`、`driver: {n_days: 3, forcing_days: 3}`、
   `forcing: {center_lat: -10.0}`。只跑 step1。
3. **day-1 振幅標度**：✅ 不用新 run 了 —— Q5 的 0.5/1/5/10 掃描每個 run 的
   pert_001 就是資料，加上主線 2.5，共五點；算條紋帶（例如 40–60°N 或熱帶外）
   RMS 對 amp 作圖，看線性/飽和。
4. **白噪聲探針**（腳本不是 config）：u0 + N(0, ~0.05 K) 微擾（只加 T 通道即可），
   re-center 1–2 步、f=0，看 u' 的偏好模態（預期緯向條紋自浮現 = J 的結構）。
   可仿 scripts/run_step1.py 寫 20 行小腳本；pangu24、device: cpu。

### Q4.（可選，§3.4 防身）β 與上界 p* 敏感度 + Deep/Shallow 小 ensemble
- β ∈ [0.4, 0.8]、p* ∈ [800, 700] 掃過確認四組排序不變（純計算）。
  注意：Deep/Shallow 的 S 比值與 β 無關（兩者 Q_B=0，比值=1.15/0.92 釘死），
  所以 β 敏感度只需要看正弦組 vs uniform 的分離。β 已定案 0.55（單一校準條件、
  正文 Deep 列標 "(calibration)"）。
- Deep/Shallow 各 3–5 member IC 微擾 ensemble，確認兩者峰值順序確實不可分辨
  （reviewer 若追問 1.66 vs 1.41 才需要）。

### Q5. 振幅掃描重跑（進行中，2026-07-05；CPU 全核）
舊 B.2 圖（`aux/investigation/figs/sweep/pangu/timeseries_amps.png`）不能用：
sweep_fcnv2_fast.py 產出，資料夾名取自 --model（=pangu）但**圖題是寫死的
"fcnv2 paperDJF"**（腳本 119 行），且設定為 paperDJF 冬季背景 + 舊 cos 加熱 +
7 天脈衝 + 振幅 3/5/7 —— 與主線全不匹配。已補跑正確設定：

- spec（已建、已開跑）：`outputs/JAS/pangu24_Deep_{0.5,1,5,10}Kday_gauss`，
  config.yaml = 主線 pangu24_Deep_2.5Kday_gauss 逐字複製，只改兩處：
  `forcing.amp_K_per_day: <0.5|1|5|10>` 與新增頂層 `device: cpu`
  （**你提醒的教訓已吃進去：pangu 在本機 GPU 會退回單核 CPU（~2 min/步），
  必須 device: cpu 走 root config 的 cpu_num: -1 全核；fcnv2 才用 GPU**）。
  其餘同主線：JAS、gauss、Deep、n_days 20、forcing_days 20（持續）。
- 只跑 step1：`$PY scripts/run_step1.py --exp outputs/JAS/pangu24_Deep_<A>Kday_gauss --no_plot`
  （log: `outputs/JAS/logs/amp_sweep_20260705.log`；2.5 K/day 重用主線 run）。
- 圖：`$PY paper/pic/make_figs.py figamps` → `pic/figB2_amp_sweep.png`
  （附錄 B.2 已改指向新圖）。
- ✅ 已跑完（你完成）、圖已入 B.2；2026-07-05 最終檢查時我用 tracker 重算四個
  新 run 全部命中你寫的數字（64.0@d19 / 63.3@d15 / 68.1@d12 / 42.3@d9；TCWV
  34.6→61.2 單調）。§3.3 已由你改寫成「水氣單調、渦度非單調、2.5 近最優」——
  與數據一致；methodology §2.4/§2.5 的舊敘述（1.5–3 bracket、0.1–20 範圍）已同步修正。

## 已完成（歷史紀錄）

- fig9 model-vs-obs、方法示意圖（現 Fig. 1）、fig5、fig7、fig8：均已產出並嵌入；
  你之後重繪了幾乎所有圖（fig3/fig4a/fig4b/B1d/B3/D1 等改由 pic/ 下你的腳本產生）。
- DJF 高斯對照（ζ' 14.1 @d9 / TCWV 45.8）；Step3/4 24h 重跑（79.0 @d9；ζ≡0/52.6）；
  6h 持續加熱（leibniz，ζ' 101.4 @d12 / TCWV 77.3）。
- Appendix 原 Fig. A1（aux forcing ellipse）已移除：該水平加熱只用於 aux 驗證、
  從未用於 output run（且疑長不出渦旋，待確認）；A 編號順移（A1=垂直剖面、A2=TCWV 一致性、A3=背景）。
- **Q1（垂直分布）已由你跑完**（pangu24_{Stratiform,Shallow,uniform}_2.5Kday_gauss）；
  §3.3 新表定稿、§3.4 依 FTR/Q3 筆記全面改寫成「低層 PV 源」理論
  （S = 內部梯度 + β·邊界 sheet 對 ζ'；⟨Q⟩_BL 對 TCWV'；見 logic/results3.4.md）；
  Appendix B.4 疊圖 = `make_figs.py figprofiles` → `pic/figB4_profiles_overlay.png`。
- **Q3（F₀ 表）已結案**：三種 F₀ 定義都 fit 不了資料（你的 FTR 筆記），由上述雙泛函理論取代。

## 定稿數字（24h 高斯套組）

| Run | peak ζ' (10⁻⁵ s⁻¹) | peak TCWV' (mm) |
|---|---|---|
| Step 1 standard | 89.4 @ d12 | 48.4 @ d14 |
| Step 2 moisture-locked | 5.5（抑制 ~94%） | ≡ 0 |
| Step 3 moisture-only init | 79.0 @ d9 | 42.3 @ d11 |
| Step 4 wind-locked | ≡ 0 | 52.6 @ d16 |
| DJF control | 14.1 @ d9（~6× 弱） | 45.8 @ d15（與 JAS 幾乎同） |
| 6h sustained | 101.4 @ d12 | 77.3 @ d16 |
| amp 0.5 | 64.0 @ d19 | 34.6 @ d20 |
| amp 1 | 63.3 @ d15 | 39.2 @ d18 |
| amp 5 | 68.1 @ d12 | 50.7 @ d18 |
| amp 10 | 42.3 @ d9 | 61.2 @ d20 |
| profiles（2.5）| Shallow 76.1 / uniform 54.0 / Strat 8.3 | Shallow 51.7 / uniform 69.2 / Strat 16.3 |
