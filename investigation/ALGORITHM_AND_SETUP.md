# 算法、初始場、加熱 forcing 細節

所有 file:line 對應 2026-06-25 的程式碼。

## 1. 算法：Perpetual Background Re-centering
核心迭代（[src/itcz/experiment/driver.py:82-92](../src/itcz/experiment/driver.py)）：

```
B1 = M(u0)                       # 凍結的一步背景漂移（用未夾的 u0 算！）
u'_0 = 0  (Step1/2) 或 day-7 moisture seed (Step3/4)
for n = 1..N:
    f_n = f_base if (persistent or n<=Nf) else 0
    A   = u0 + u'_{n-1} + f_n     # 每步都錨回穩態 u0
    clip_moisture(A)             # 進 M 前強制 q>=0 / 0<=RH<=100%
    u'_n = M(A) - B1             # 扣掉常數一步漂移
    u'_n = LOCK(u'_n)            # Step2: 水氣歸零；Step4: 風歸零
    save u'_n
```

- 背景永遠錨在穩態 u0，避免混沌天氣 spin-up。理論前提：u0 近似 M 的不動點
  （M(u0)≈u0），時間平均場越平滑越成立。
- **注意不對稱**：`B1 = op.step(u0)`（driver.py:82）用的是**未經 clip 的 u0**，
  但迴圈內每個 A 都先 `clip_moisture`。若擾動把某處推到飽和，clip 會在該處注入
  一個不被 B1 抵銷的偏差 → 疑似噪聲來源之一（待開關測試）。

## 2. 四個步驟（experiment block）
| Step | 腳本 | u'_0 | forcing | lock |
|---|---|---|---|---|
| 1 | run_step1.py | 0 | heating（前 7 天 on，後 off） | none |
| 2 | run_step2.py | 0 | heating | moisture→0 每步 |
| 3 | run_step3.py | step1 day-7 moisture 種子 | none | none |
| 4 | run_step4.py | step1 day-7 moisture 種子 | persistent moisture | wind→0 每步 |

driver 不做續跑；重跑會從 pert_000 覆蓋（[driver.py:75-83](../src/itcz/experiment/driver.py)）。

## 3. 初始場（u0）平均方式
### paperDJF（論文忠實版，目前使用）— [scripts/prep_paper_djf.py](../scripts/prep_paper_djf.py)
- **0000 UTC only**（每月檔取 `valid_time=0`，即 00Z）。
- **1979–2019**（41 年），月份 (12,1,2)，共 123 個月場。
- **day-weighted**（各月以天數加權）→ 真正的 per-00Z 時間平均。
- 1980–2019 取自共用 archive；缺的 1979 D/J/F 下載到 `data_raw/`。
- 輸出 `ic/u0_paperDJF_{pangu,fcnv2}.npz`（各 233M，已驗證 T850/風速/TCWV 合理）。

### 對照：repo 內建 DJF — [scripts/prep_djf.py](../scripts/prep_djf.py)
- **diurnal mean（全時段/全 hour 平均）**、**1991–2020**。
- 與 paperDJF 的差別：全時段 vs 00Z、年代不同、加權不同。

> 重要：論文（Hakim & Masanam 2024）明訂 IC =「0000 UTC 1979–2019 DJF ERA5
> time average」（Dynamical Tests 論文 line 200-201），**與 paperDJF 一致**。
> 論文亦指出時間平均場「smoother than any individual state」，正是要這種平滑穩態。
> → IC 方法已對；改成「全時段平均」會退回 repo DJF（已證實同樣雜亂），預期無助益。

### 論文提供的平均好 IC / 程式碼
Data availability：**github.com/modons/DL-weather-dynamics**（Dynamical Tests
論文 line 588-590）。可下載其 DJF 平均 IC 與方法程式，作為 ground truth 驗證
我們的 u0 與算法。

## 4. 加熱 forcing — [src/itcz/experiment/forcing.py](../src/itcz/experiment/forcing.py)
### 水平結構（高斯橢圓）
- 由「地理範圍」指定：`center_(lat,lon)` ± `(lat,lon)_halfwidth`，
  σ = halfwidth / `edge_sigmas`（edge_sigmas=2 → 虛線邊界在 2σ）。
- **現行 config**：center_lat 7.5、lat_halfwidth 6 → 1.5–13.5°N；
  center_lon 195、lon_halfwidth 75 → 120°E–90°W(270°E)。
- **放大判讀（待試）**：5–15°N、125°E–95°W → center_lat 10 / lat_halfwidth 5；
  center_lon 195 / lon_halfwidth 70。

### 垂直結構（vertical_profile, forcing.py:65-80）
- 僅 200–1000 hPa 非零。Deep=sin(πpn)、Stratiform=sin(2πpn)、
  Shallow=(sin(πpn)−sin(2πpn))/√2。

### 振幅換算（**已確認正確**）
- `amp_per_step = amp_K_per_day * step_hours/24`（forcing.py:108）。
  10 K/day → 每 6h **+2.5 K**。沒有 4 倍過量問題。
- 但 `amp_K_per_day` 該設多少未定：
  - 論文「weak tropical heating」線性測試用 **0.1 K/day**（Dynamical Tests line 241/330）。
  - ITCZ breakdown（Guinn-Schubert）是非線性不穩定，需**有限振幅**才會捲渦，
    故不必是 0.1；正確值需掃描以重現 AI-Forum（峰值 ~47×10⁻⁵、乾淨衰減）。
- 加熱施加在溫度場：Pangu 加到 upper[T]；FCNv2 加到 13 層 T block
  （layout.py:123-124, 164-165）。

## 5. 診斷（渦度/TCWV）— [src/itcz/plotting/tracker.py](../src/itcz/plotting/tracker.py)
- 渦度：`relative_vorticity` 用 `np.gradient`（有限差分）於 **0.25° 全解析度**
  （tracker.py:34-42）→ 會放大格點小尺度噪聲，並使 band-max 峰值偏高且鋸齒。
- timeseries 取 `track_band` 內的**最大值**（對噪聲極敏感）。
- AI-Forum 的乾淨/低峰值可能來自對渦度做**平滑或譜截斷**後再取 max（待驗證）。
