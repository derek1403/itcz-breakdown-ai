# ITCZ-breakdown 排查筆記 (investigation/)

本資料夾記錄「為何現行 pipeline 的結果與 AI-Forum 早期乾淨圖不符」的排查過程、
算法/初始場/加熱設定的細節，以及試錯實驗的計畫與紀錄。

最後更新：2026-06-25

## 導覽
- **[進度報告0625_總整理.md](進度報告0625_總整理.md) — ⭐ 大統整（含內嵌 2D 渦度圖、AI-Forum 目標對照、
  已排除變因、最佳結果、未解問題、下一步）。對外討論看這份。**
- [進度報告0625_1700_垂直加熱.md](進度報告0625_1700_垂直加熱.md) — 四種垂直加熱分布比較（含圖）。
- [進度報告0625_1545.md](進度報告0625_1545.md) — 方位驗證 / day1 條紋 / IC 平滑 / pre-M 隔離。
- [進度報告0625_1450.md](進度報告0625_1450.md) — forcing refinement 三變體說明。
- [ALGORITHM_AND_SETUP.md](ALGORITHM_AND_SETUP.md) — 算法、初始場平均方式、加熱 forcing 細節（file:line）。
- [FINDINGS_AND_EXPERIMENTS.md](FINDINGS_AND_EXPERIMENTS.md) — 診斷結論、假設排序、實驗紀錄表。
- [standalone/](standalone/) — 可攜的單檔腳本（h5→npy、跑 Pangu 加熱、畫渦度）。

## 問題陳述
參考圖（`related_paper/AI-Forum.pdf`，使用者早期作品、來源已不可考）顯示：
Step1 加熱後沿 ITCZ 捲起**乾淨的離散渦旋**，渦度 timeseries 在 day12 達峰
~47×10⁻⁵ s⁻¹ 後**平滑衰減**，中緯度安靜。

現行 pipeline（同一份程式）對 **DJF / JJA / paperDJF 三個背景都產生雜亂結果**：
day6 起中緯度寬頻噪聲、無乾淨渦旋捲起、渦度峰值 ~80×10⁻⁵ 且鋸齒、day12 後不衰減。

→ 落差**不是 paperDJF 或當機造成**，是現行 pipeline 與早期乾淨版之間的系統性差異。

## 目前狀態
- ✅ 資料完整性：paperDJF IC（00Z DJF 1979–2019）已建好並驗證；ERA5 來源齊全。
- ✅ 背景 pipeline 已停止（原 PID 701990），step1/step2(pangu) 產出保留。
- ⏸ 暫停長時間連跑，先做小規模 fcnv2(GPU) 試錯，確認大方向正確再續。

## 關鍵待驗證
1. 加熱振幅（現行 10 K/day vs 論文線性測試 0.1 K/day；ITCZ breakdown 需有限振幅，
   正確值待掃描）。
2. 加熱區域（現行 lat 1.5–13.5°N / lon 120°E–90°W vs 放大判讀 5–15°N / 125°E–95°W）。
3. `clip_moisture` 的不對稱性是否注入噪聲（開關測試）。
4. 算法本身是否與論文一致（論文程式碼：github.com/modons/DL-weather-dynamics）。
5. 渦度診斷是否需平滑/譜截斷（0.25° 有限差分會放大格點噪聲與峰值）。

## 算法檔案地圖（檢查算法看這些）
所有 src 路徑相對於 repo 根 `/wk2/pc/AI_models/itcz-breakdown-ai/`。

### 核心算法（最重要，前 4 個）
1. **迭代主體（方法本身）** `src/itcz/experiment/driver.py` 的 `run()` L49–97：
   `B1=op.step(u0)`(L82)、`A=u0+u_prev+f_n`(L86)、`clip_moisture(A)`(L87)、
   `u_n=op.step(A)-B1`(L88)、lock(L89)。= Perpetual Background Re-centering。
2. **加熱 forcing** `src/itcz/experiment/forcing.py`：
   - **水平高斯分布** = `horizontal_ellipse` **L46–50**：
     `exp(-0.5(dlat/σlat)² - 0.5(dlon/σlon)²)`；σ 由 `sigmas()` L35–38 = halfwidth/edge_sigmas。
   - 垂直 `vertical_profile` L65–80；組合 `_unit_field` L83–88；振幅換算 `heating_forcing` L108。
   - ⚠️ 論文用 cos(kφ)×Gaspari-Cohn（非高斯）— 見下 #10。
3. **模式步進 M** `src/itcz/models/operators.py`：`PanguOperator.step` L63–68（直接餵 ONNX）、
   `FCNv2Operator.step` L101–108（先標準化再反標準化）。
4. **State 運算** `src/itcz/models/layout.py`：`clip_moisture`(Pangu L138–140/FCNv2 L181–185)、
   `add_temperature`(L123/164)、`add_moisture`(L126/167)、`get_uv`、`tcwv`。

### 設定 / 時間 / 診斷 / IC
5. `config.yaml`：forcing 區域 L43–46、amp、n_days/forcing_days、診斷 `track_band` L63。
6. `src/itcz/config.py`：`n_steps`、`forcing_steps`、`ic_path`。
7. `src/itcz/plotting/tracker.py`：`relative_vorticity` L34–42（有限差分）、`track_max` L61–66（band 取最大）。
8. `scripts/prep_paper_djf.py`：00Z DJF 1979–2019 day-weighted IC 平均。

### 對照論文官方算法（直接比對）
9. `investigation/ref/DL-weather-dynamics/run_heating.py`：amp=0.1 L67、區域 ylat=0/xlon=120 L69–71。
10. `investigation/ref/DL-weather-dynamics/panguweather_utils.py`：`run_panguweather` 加熱 **post-M** L128–130、
    `make_steady` 減 mean tendency L132–134；`perturbations_ellipse`（cos(kφ)×GC 區域函數）L208。

### 與論文的實質差異（已比對，記於 FINDINGS_AND_EXPERIMENTS.md B2）
振幅(我們可調 vs 0.1)、加熱注入點(pre-M vs post-M)、水平形狀(高斯 vs cos×GC)、
垂直(sin profile vs 均勻 1000–250hPa)、clip(我們有 vs 論文無)、穩態機制(B1≡mean tendency，等價)。
