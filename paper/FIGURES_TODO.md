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

1. 圓形斑強迫 @10°N/195°E、跑 2–3 步（σφ=σλ≈6.4°）— 看條紋方向/全域性是否不變。
2. 同橢圓搬到 10°S、跑 2–3 步 — 同上。
3. day-1 振幅標度：先用現有 2.5K/5K run 的 pert_001 算條紋帶 RMS（不用新 run），
   需要再補 0.5/1 K/day 的 1–2 步 run。
4. 白噪聲探針：u0 + 微小白噪聲、re-center 1 步，看 J 偏好模態（預期緯向條紋自浮現）。

### Q4.（可選，§3.4 防身）β 與上界 p* 敏感度 + Deep/Shallow 小 ensemble
- β ∈ [0.4, 0.8]、p* ∈ [800, 700] 掃過確認四組排序不變（純計算）。
- Deep/Shallow 各 3–5 member IC 微擾 ensemble，確認兩者峰值順序確實不可分辨
  （reviewer 若追問 1.66 vs 1.41 才需要）。

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
