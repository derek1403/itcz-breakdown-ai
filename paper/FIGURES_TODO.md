# FIGURES_TODO — 執行狀態（2026-07-02 更新）

```說明
你核准「都可以運行」後的執行紀錄。組合圖統一由 paper/pic/make_figs.py 產生
（$PY paper/pic/make_figs.py fig5|fig7|fig8|fig9|schematic|all，$PY = pangu_env python）。
高斯化重跑：主管線 outputs/JAS 的 Step1/2 本來就是高斯（README §8 回寫的預設），
所以只需補 DJF 高斯對照與 6h 持續加熱版；Step3/4 原本是 6h 跑的，為了套組一致改以 24h 重跑。
運算分工：本機跑 DJF + Step3/4 重跑；leibniz (140.112.67.122, ~/itcz_run) 跑 64 步的
6h 持續加熱版（cpu、pangu_env）。
```

## 已完成

| 項目 | 產物 | 狀態 |
|---|---|---|
| F1 model-vs-obs money figure | `pic/fig9_model_vs_obs.png`（已嵌入 results §3.7 Fig. 9） | ✅ |
| F4 方法示意圖 | `pic/fig_method_schematic.png`（已嵌入 methodology §2.2 Fig. M1） | ✅ |
| 峰值數字萃取（高斯 Step1） | ζ' 89.4e-5 @ day 12；TCWV' 48.4 @ day 14（已入 §3.2 與摘要） | ✅ |

## 執行中（機器跑著）

| 項目 | 指令/位置 | 用途 | 完成後動作 |
|---|---|---|---|
| DJF 高斯對照 | 本機 `run_step1.py --background DJF --amp_K 2.5 --heat_type Deep` → `outputs/DJF/step1_pangu_DJF_Deep_2.5Kday` | Fig 5 + Appendix B.3 | `make_figs.py fig5`；§3.3a 填 DJF 峰值 |
| 6h 持續加熱 | leibniz `~/itcz_run`，log `run_6h_2.5K_sustained.log`（64 步 cpu） | §3.6 / Fig 8 受控比較（原 6h run 是 7 天脈衝，與 24h 持續加熱不對照） | rsync 回本機 `outputs/JAS/step1_pangu_JAS_Deep_2.5Kday_6h_sustained/` → `make_figs.py fig8` |

## 排隊中（DJF 跑完接著跑）

| 項目 | 指令 | 用途 |
|---|---|---|
| Step 3 重跑（24h） | `run_step3.py --model pangu --background JAS --step1_dir outputs/JAS/step1_pangu_JAS_Deep_2.5Kday` | 套組一致（原 6h 版已改名 `*_6h` 存檔） |
| Step 4 重跑（24h） | `run_step4.py --model pangu --background JAS --step1_dir outputs/JAS/step1_pangu_JAS_Deep_2.5Kday` | 同上 |
| F2 Step1–4 疊圖 | `make_figs.py fig7` → `pic/fig7_steps_overlay.png` | 取代 results §3.5 的三張分開 timeseries；順便定稿 §3.5 數字 |

## 參考數字（已萃取，6h 舊 run 的 day 已換算）

- Step 1（24h 高斯）: ζ' 89.4e-5 @ d12；TCWV' 48.4 @ d14
- Step 2（24h 鎖水氣）: ζ' 5.5e-5（成長抑制 ~94%）；TCWV' ≡ 0
- Step 3（舊 6h 版）: ζ' 80.3e-5 @ d10；TCWV' 84.8 @ d16 — 待 24h 重跑確認
- Step 4（舊 6h 版）: ζ' ≡ 0（鎖風）；TCWV' 68.6 @ d16 — 待 24h 重跑確認
- 6h pulse7d：ζ' 79.8e-5 @ d11.5；TCWV' 70.0 @ d15.5
