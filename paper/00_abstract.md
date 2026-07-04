# Barotropic Breakdown of the ITCZ in a Global AI Weather Model: A Finite-Time Nonlinear Perturbation Framework

```說明
這是標題頁與摘要。標題強調兩件事：(1) 我們在 AI 模式（Pangu）裡重現了 ITCZ 正壓不穩定捲渦，
(2) 我們用的是「有限時間非線性擾動法」（semi-linear / perpetual background re-centering）。
摘要的敘事線：AI 模式能不能被當成動力系統來「審問」→ 我們設計了凍結背景的擾動實驗 →
加熱在 10°N 產生渦度帶、正壓不穩定捲成 ~4 個渦旋 → 結構對上 2024 年 11 月
西北太平洋四颱並存的觀測事件 → 但我們同時嚴格說明：迭代步數 n 是「模態萃取的收斂次數」，
不是物理時間，這是本文方法論的核心誠實聲明。
作者列與致謝先留空，由你補。
```

**Authors:** [TODO: author list]

**Affiliations:** [TODO]

---

## Abstract

Deep-learning weather prediction (DLWP) models now rival operational numerical
weather prediction in forecast skill, yet whether they encode atmospheric
*dynamics* — rather than sophisticated pattern matching — remains an open
question. Following the dynamical-testing paradigm of Hakim and Masanam (2024),
we interrogate the Pangu-Weather model with a classical instability problem:
the barotropic breakdown of the Intertropical Convergence Zone (ITCZ). We
develop a finite-time nonlinear perturbation framework ("perpetual background
re-centering") in which the model operator $M$ is applied to a perturbed,
steady July–September (JAS) climatological background while the background
itself is re-anchored at every step. Because the background is frozen, the
iteration constitutes a forced power iteration that extracts the
fastest-growing finite-time structure — a nonlinear analogue of a singular
vector of $M$ about the basic state — rather than a forecast trajectory.
Sustained deep-convective heating ($2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$, centered at 10°N) first
generates a potential-vorticity band displaced to the poleward flank of the
heating, which subsequently undulates and rolls up into approximately four
discrete vortices (peak $\zeta' \approx 9\times10^{-4}\ \mathrm{s^{-1}}$,
$\mathrm{TCWV}' \approx 48$ mm). Mechanism-denial experiments (moisture
and wind locking) show the growth requires the wind–moisture coupling the
model has learned. The converged mode structure — a chain of vortices along
the monsoon trough — closely resembles the November 2024 western North
Pacific event in which four tropical cyclones coexisted, the first such
November occurrence on record. We discuss the conditions under which such a
mode-extraction sequence can be meaningfully compared with an observed
temporal evolution, and the limitations imposed by off-manifold ("manifold
shock") artifacts of the neural operator.

---

## Plain-language summary

AI weather models are trained only to predict tomorrow's weather from
today's, yet we find that one of them, Pangu-Weather, has internalized a
classical piece of tropical dynamics: when a band of tropical heating is
switched on, the model spontaneously produces a strip of spinning air that
breaks up into a chain of typhoon-like vortices — the same "ITCZ breakdown"
process theorized from shallow-water dynamics in the 1990s and visible in
satellite imagery, most spectacularly in November 2024 when four typhoons
lined up across the western Pacific at once. We introduce a careful
experimental protocol that keeps the model's background state fixed so that
only the response to the heating grows, and we are explicit about what the
method does and does not measure.
