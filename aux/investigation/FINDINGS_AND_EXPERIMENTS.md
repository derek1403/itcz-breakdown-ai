# 診斷結論、假設排序、實驗計畫

## A. 診斷證據
1. **paperDJF ≈ DJF ≈ JJA（同樣雜亂）**：三者都用現行程式，渦度場 day6 起中緯度
   寬頻噪聲、無乾淨 ITCZ 渦旋。→ 問題與背景場/當機無關，是 pipeline 層級。
   - 圖：`outputs/{DJF,JJA,paperDJF}/step1_pangu_*/panels_vort.png`
2. **量級/形狀 vs AI-Forum**（repo DJF compare_pangu.png vs AI-Forum page4）：

   | | 現行程式 | AI-Forum（目標） |
   |---|---|---|
   | Step1 渦度峰值 | ~80×10⁻⁵ s⁻¹ | ~47×10⁻⁵ s⁻¹ |
   | 曲線 | 鋸齒、day12 後仍 55–80 | 平滑、day12 達峰後乾淨衰減 |
   | 場 | 全域中緯度混沌 | 僅 ITCZ 帶乾淨渦旋 |
3. **AI-Forum 不是現行程式畫的**：標題 "…after N days"、版面（day0 單張+2 欄）
   在現行 tracker 不存在（現行為 "…anomaly day {day}"）。早期版本已不可考。

## B. 假設排序（最可能 → 次要）
1. **加熱振幅過強（10 K/day）**：把系統推進過度非線性 → 峰值過高+中緯度混沌。
   ITCZ breakdown 需有限振幅，但正確值可能在 ~0.5–5 K/day。**最優先掃描。**
2. **渦度診斷無平滑**：0.25° 有限差分 + band-max → 峰值灌水、鋸齒。加平滑/譜截斷
   可能同時修好「峰值 80→47」與「鋸齒→平滑」與「panel 乾淨度」。**低成本先試。**
3. **算法與論文不一致**：現行用「凍結 B1 + 每步 clip」；論文方法（GitHub）可能用
   完整 control 軌跡相減等。需比對論文程式。
4. **clip_moisture 不對稱**：B1 用未夾 u0、A 每步夾 → 飽和區注入偏差。開關測試。
5. **加熱區域**：1.5–13.5°N vs 5–15°N 等。影響渦旋位置/緯度，較非主因，但要對齊。

> IC 平均方式**不在主要嫌疑**：論文確認 00Z DJF 1979–2019 為正確 IC；且我們所有
> IC 變體（paperDJF 00Z、repo DJF 全時段、JJA）都同樣雜亂 → IC 非鑑別因子。
> 仍可用論文 GitHub 的平均 IC 做一次性對照以徹底排除。

## B2. 對照論文官方程式（investigation/ref/DL-weather-dynamics/）
讀 `run_heating.py` + `panguweather_utils.py` 後，與我們 repo 的**實質差異**：

| 項目 | 論文官方 (run_heating) | 我們 repo |
|---|---|---|
| 加熱振幅 | **amp = 0.1 K/day** | **10 K/day（100×）** |
| 加熱施加處 | 模式**輸出後**(post-M)，對 T 均勻加 levels 1000–250hPa | **輸入端**(pre-M) 穿過 M，sin 垂直 profile |
| moisture clip | **無** | 每步 clip q/RH |
| 穩態機制 | 減預存 mean tendency（mean_state_tendency.py） | B1=M(u0)（**數學等價**，已推導） |
| 加熱時長 | 全程持續 | Step1 前 7 天 on 後 off |
| 水平形狀 | cos(kφ)×Gaspari-Cohn 經向局地化 | 高斯橢圓 |

推導：論文 `state_k = M(state_{k-1}) + heating − mean_dt`，令 mean_dt=M(mean)−mean，
得 `p_k = M(mean+p_{k-1}) − M(mean) + heating`（heating 為 post-M 純線性注入）。
我們：`u'_n = M(u0+u'_{n-1}+f) − M(u0)`（f 為 pre-M、穿過模式）。
→ **穩態/再錨機制等價；差別在 (a) 振幅 100×、(b) heating 注入點 pre-M vs post-M、
(c) 我們多了 clip、(d) 垂直 profile**。算法骨架沒錯，問題在 forcing 細節與振幅。

### 論文提供的平均 IC（回答使用者提問：有！）
下載點：**https://www.atmos.washington.edu/~hakim/DL_weather_dynamics/**
（含 model weights、climatological mean state `mean_DJF.h5`、perturbation fields）。
mean state 為 h5：`mean_pl`(z,q,t,u,v × 13 levels)、`mean_sfc`、lat、lon。
data_prep/ 有完整重建流程（download→compute_mean→mean_state_tendency→regression）。
→ 可下載 `mean_DJF.h5` 與我們的 `ic/u0_paperDJF_pangu.npz` 逐場比對驗證。

## B3. 診斷平滑測試結果（假設②，已驗證命中一大半）
對現有 paperDJF pangu step1（10 K/day）渦度做高斯平滑（lon-wrap）後 band-max：

| σ(格點, ~0.25°/格) | band-max ×10⁻⁵ s⁻¹ |
|---|---|
| 0 (raw) | 79.3 |
| 6 (~1.5°) | 11.7 |

- σ=6 平滑後**場結構與 AI-Forum 對上**：day9–12 沿 ITCZ 連貫渦度帶+離散渦旋，
  **中緯度安靜**。→ raw 的「全域混沌」大半是 0.25° 有限差分格點噪聲。
- 但 σ=6 過度（峰值 11.7≪47、渦旋不夠銳利）。AI-Forum 的 47+銳利離散渦旋
  介於 raw 與 σ6 之間 → 需**較輕平滑（σ~2–3）＋較低加熱振幅**的組合。
- 圖：`outputs/paperDJF/step1_pangu_paperDJF_Deep_10Kday/panels_vort_smoothed_s6.png`、
  `timeseries_smoothing_s6.png`（σ2/3/4 產生中）。

## C. 實驗計畫（fcnv2 走 GPU，快速試錯）
裝置：RTX 3080（device=cuda）。為加速迭代，先用較短積分（n_days≈12）＋只 fcnv2。
每個實驗看 step1 的 panels_vort/tcwv 與 timeseries，對齊 AI-Forum（乾淨渦旋、
峰值 ~47×10⁻⁵、day12 達峰後衰減）。

建議**序貫**（非全因子）以省算力：
1. **E0 baseline**：現行設定（10 K/day、舊區域、clip on）跑 fcnv2，建立對照。
2. **E1 振幅掃描**：固定區域=放大判讀(5–15°N/125°E–95°W)，amp ∈ {0.5, 1, 2, 5} K/day。
   找出最接近 AI-Forum 峰值/形狀者。
3. **E2 診斷平滑**：對 E1 最佳者，渦度加空間平滑/譜截斷重畫，看是否更貼合。
4. **E3 clip 開關**：對最佳設定關掉 clip_moisture，比較噪聲。
5.（可選）**E4 對照論文**：下載 github.com/modons/DL-weather-dynamics 的 IC/方法，
   驗證 u0 與算法。

## D. 實驗紀錄

### 重要決策（2026-06-25）
- **以 pangu 為定版主模式**：AI-Forum page2 乾淨渦旋為 pangu、論文亦用 pangu；
  fcnv2 振幅響應差很多（見下），只用於 GPU 快速探方向。
- **加熱區域更新**：config.yaml 改為 **5–15°N / 125°E–95°W**
  （center_lat=10, lat_halfwidth=5, center_lon=195, lon_halfwidth=70）— 依使用者放大判讀。
- **AI-Forum 視為 raw（σ≈0）**：使用者判讀其有自然 speckle、未平滑 → 用 raw 評估。
- **快速掃描法**：investigation/sweep_fcnv2_fast.py 不存 182MB 完整 state（那是 ~53s/step
  的瓶頸），只算 band-max + 存 snapshot 2D 渦度 → fcnv2 每振幅 3.5 min（GPU），
  pangu 每振幅 ~50 min（CPU）。

### 振幅 → raw band-max 峰值（×10⁻⁵ s⁻¹）
fcnv2 (paperDJF, 舊區域, n_days16)：
| amp | 0.1 | 0.5 | 1 | 2 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|---|---|
| peak | 1.9 | 3.1 | 3.1 | 6.1 | 10.9 | 13.5 | 24.8 | 30.9 |
→ fcnv2 反應弱，外推 ~28–30 K/day 才達 47；且低振幅(≤2K)幾乎不捲渦。**棄 fcnv2 作定版。**

pangu (paperDJF, 新區域 5–15N, n_days16)：**進行中** amps=[3,5,7]
| amp | 3 | 5 | 7 | 10(舊區域,既有) |
|---|---|---|---|---|
| peak | (跑) | (跑) | (跑) | 79.3 |
→ 目標 raw peak≈47 + day12 達峰後衰減 + 中緯度安靜。pangu 10K(舊)=79，預期 ~5K 附近。

### 診斷平滑（pangu 10K 舊區域 step1，band-max ×10⁻⁵）
σ0=79.3, σ1=64.6, σ2=43.0, σ3=27.8, σ4=19.3, σ6=11.7。
σ≈1.5 對上 47；但 σ=2 場仍中緯度偏吵、timeseries 形狀不對（不衰減）→ 平滑非唯一解，
振幅才是關鍵。圖：investigation/figs/day12_sigma_compare.png、timeseries_sigma_compare.png。

### 定版 run：pangu amp=3 K/day, 新區域 5-15N（outputs/paperDJF/step1_pangu_paperDJF_Deep_3Kday）
- ✅ 渦度峰值 ~45×10⁻⁵（AI-Forum ~47）、ITCZ 沿 5-15N 捲出離散渦旋、day0-6 乾淨。**大體正確。**
- ⚠️ 殘留落差（指向 forcing 細節，非振幅/IC）：
  1. timeseries 不衰減（鋸齒升到 day16；AI-Forum day12 達峰後衰減）——疑小尺度串級灌大 raw band-max。
  2. TCWV ~30 < AI-Forum ~45（要壓渦度到 45 得用 amp=3，但 TCWV 就不足 → 水氣/forcing 機制有差）。
  3. 中緯度仍比 AI-Forum 活躍。
- 圖：panels_vort.png / panels_tcwv.png / timeseries.png（在該 run 目錄）。

### ✅ IC 驗證完成（2026-06-25）：我們的 IC ≈ 論文官方 IC
論文 ERA5_means.zip（使用者並行下載完成）解壓得 mean_DJF.h5 等。
轉成 ic/u0_paperHM_pangu.npz（結構與我們完全相同：upper(5,13,721,1440)、surface(4,721,1440)、
lat90→-90、levels1000→50）。逐場比對 ours(u0_paperDJF) vs paper：
| var | RMSE | RMSE/場std |
|---|---|---|
| t | 0.22 K | 0.8% |
| z | 61 | 0.1% |
| u | 0.42 m/s | 3.8% |
| q | 4.6e-5 | 1.4% |
差異極小且集中在高緯/風暴帶/地形（平均殘差），**熱帶 ITCZ 區幾乎無差**。
→ **IC 不是位置/結構差異來源。** 圖：investigation/figs/ic/ic_ours_vs_paper.png。
- paperHM IC 跑 pangu step1 amp=3 完成（outputs/paperHM/step1_pangu_paperHM_Deep_3Kday）。

### 🔑 混沌發現：渦旋位置對微小 IC 差異敏感
paperDJF vs paperHM（IC 僅差 ~0.2K）兩 run 比對：
- peak band-max：45.5 vs 43.5（統計一致）。
- 熱帶太平洋框(0-30N,120-270E)渦度場相關係數：day6=0.77 → day9=0.66 → **day12=0.42**（去相關）。
→ ITCZ breakdown 是正壓不穩定(混沌捲渦)：**early/統計可重現，但 day9-12 確切渦旋位置對 IC 微差極敏感**。
→ **「位置與 AI-Forum 不同」是混沌本質，非 bug/IC 錯。** 論文 README 亦警告 heating 實驗對環境最敏感。
→ 對齊目標應為統計/定性特徵（ITCZ 帶位置、渦旋尺度、成長時序、峰值、TCWV 共生），非逐日位置。

### ✅ Forcing refinement（2026-06-25）：論文版 forcing 修好 TCWV 與 timeseries 形狀
pangu amp=3 新區域，3 變體（investigation/figs/refine/）：
| 變體 (inject/clip/vert) | vort 峰 | TCWV 峰 | 形狀 |
|---|---|---|---|
| current (pre/clip/sin) | 45.5 | 31.6 | 鋸齒不衰減 |
| postM only (post/clip/sin) | 43.4 | 31.6 | 同上（post-M 本身幾乎無差）|
| **paper (post/noclip/uniform)** | 57.6 | **47.2** | **day7-9 達峰後衰減（對上 AI-Forum）** |
- **關鍵 = 均勻垂直加熱(1000-250hPa) + 不 clip**：Deep sin profile 集中中層、clip 抑制水氣 →
  TCWV 起不來且不飽和。改均勻+不clip → TCWV 47≈AI-Forum 45，且 vort/TCWV 都呈現峰後衰減。
- 待校正：paper forcing 較強 → vort 衝 57(>47)、峰偏早(day7-9 vs day12)；降振幅至 ~1.5-2 可校回。
- 圖：compare_refine.png、snaps_paper_post_noclip_uniform.png。

### 待補
- **paper-faithful forcing + 降振幅**（~1.5-2 K/day）定版，使 vort≈47、峰≈day12。
- 隔離 uniform vs no-clip 各自貢獻（理論上 uniform 為主）。
- 論文 ERA5_means.zip 解壓後（已完成）：
  解壓 → mean_DJF.h5(mean_pl: z,q,t,u,v×13；mean_sfc: msl,u10,v10,t2m；正好對上 Pangu)
  → 轉成 ic/u0_paperHM_pangu.npz → (a) 與 u0_paperDJF_pangu.npz 逐場比對；
  (b) 用 amp=3 新區域跑 step1 對照我們自建 IC。
- **Fig1 ground truth**：用論文 run_heating.py（amp=0.1, 赤道 120E）跑出原生 Fig1。
- **forcing refinement**：clip on/off、heating post-M（加在模式輸出後）、垂直 profile、
  heating 持續 vs 7天後關 —— 看能否同時修好 timeseries 形狀/TCWV/中緯度三項落差。
