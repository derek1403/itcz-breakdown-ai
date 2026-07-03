# FIGURES_TODO — 執行狀態（2026-07-02 第二次更新）

```說明
「都可以運行」核准後的執行紀錄。組合圖由 paper/pic/make_figs.py 產生
（$PY paper/pic/make_figs.py fig5|fig7|fig8|fig9|schematic|all，$PY = pangu_env python）。
高斯化：主管線 outputs/JAS 的 Step1/2 本來就是高斯（README §8 預設），只補了 DJF 對照與
6h 持續加熱版；Step3/4 原為 6h 跑的，已改 24h 重跑（舊版存檔為 *_6h）。
運算分工：本機（GPU）跑 DJF + Step3/4 重跑；leibniz (140.112.67.122, ~/itcz_run,
pangu_env, cpu) 跑 64 步 6h 持續加熱版，跑完 rsync 回本機。
```

## 已完成

| 項目 | 產物 | 已嵌入 |
|---|---|---|
| fig9 model-vs-obs money figure | `pic/fig9_model_vs_obs.png` | results §3.7 Fig. 9 |
| 方法示意圖 | `pic/fig_method_schematic.png` | methodology §2.2 Fig. M1 |
| fig5 JAS vs DJF 疊圖 | `pic/fig5_seasonal_timeseries.png` | results §3.3a Fig. 5 |
| fig7 Step1–4 疊圖 | `pic/fig7_steps_overlay.png` | results §3.5 Fig. 7 |
| DJF 高斯對照 run | `outputs/DJF/step1_pangu_DJF_Deep_2.5Kday/` | App. B.3 |
| Step3/4 24h 重跑 | `outputs/JAS/step{3,4}_pangu_*/`（舊 6h 版 → `*_6h`） | §3.5 數字 |
| 6h 持續加熱 run（leibniz） | rsync → `outputs/JAS/step1_pangu_JAS_Deep_2.5Kday_6h_sustained/` | 見下 |

## 進行中

- [ ] rsync 6h_sustained 回本機 → `make_figs.py fig8` → 換掉 results §3.6 Fig. 8 與
      App. D 的 pulse7d 圖（受控比較：兩者皆持續加熱 16 天）。

## 定稿數字（24h 高斯套組）

| Run | peak ζ' (10⁻⁵ s⁻¹) | peak TCWV' (mm) |
|---|---|---|
| Step 1 standard | 89.4 @ d12 | 48.4 @ d14 |
| Step 2 moisture-locked | 5.5（抑制 ~94%） | ≡ 0 |
| Step 3 moisture-only init | 79.0 @ d9 | 42.3 @ d11 |
| Step 4 wind-locked | ≡ 0 | 52.6 @ d16 |
| DJF control | 14.1 @ d9（~6× 弱） | 45.8 @ d15（與 JAS 幾乎同） |
