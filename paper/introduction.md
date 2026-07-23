# 1. Introduction

```說明
前言的故事線分四段：
(1) AI 天氣模式的技能已經追上傳統 NWP，但「它學到的是動力還是圖形比對？」是懸而未決的問題
    → Hakim & Masanam (2024) 的「動力測試」典範是我們的直接靈感（你筆記裡的 HAKIM2024）。
(2) 我們選的考題：ITCZ 正壓不穩定崩解 —— Guinn & Schubert (1993)、Nieto Ferreira &
    Schubert (1997)、Wang & Magnúsdóttir (2005, 2006) 的經典問題，同時也是颱風生成路徑。
(3) 本文做了什麼：凍結背景的有限時間非線性擾動法、成功重現、機制剝奪實驗（鎖水氣/鎖風）、
    垂直分布敏感性與低層 PV 源理論（§3.4；EX/BL 等價性降為附錄 B.5 的邊界通道檢驗）、
    觀測對照 —— 並且誠實面對「迭代 n ≠ 物理天數」的詮釋問題，
    把「模態萃取序列何時可以與觀測時間演化比較」列為本文明確目標之一。
(4) 章節導覽。
你原本的筆記（HAKIM2024 啟發 + 之後要探討 manifold）已織入第 2 段與倒數第 2 段。
```

Data-driven weather prediction (DWP) models trained end-to-end on
reanalysis data now match or exceed the deterministic skill of the world's
best operational numerical weather prediction systems. Pangu-Weather, a
three-dimensional Earth-specific transformer trained on 39 years of ERA5,
outperforms the ECMWF high-resolution forecast on standard headline scores at
a fraction of the computational cost (Bi et al. 2023); FourCastNet v2 achieves
comparable skill with a spherical Fourier neural operator architecture (Bonev
et al. 2023). This success raises a question that forecast scores alone
cannot answer: have these models *encoded the dynamics* of the atmosphere, or
are they performing a sophisticated form of pattern completion that happens to
minimize forecast error (Bonavita 2024)?

One productive way to address this question is to treat the trained network as
a dynamical system and subject it to controlled, idealized experiments of the
kind traditionally performed with dynamical cores. Hakim and Masanam (2024)
pioneered this paradigm: by holding the model on a steady climatological
background and inserting localized perturbations — including a steady tropical
heat source that elicited a recognizable Matsuno–Gill response (Gill 1980) —
they showed that Pangu-Weather reproduces classical dynamical solutions that
are, in that form, absent from its training data. Their study is the direct
inspiration for the present work, and their steady-background technique is the
foundation on which our perturbation framework is built (Section 2).

Here we pose a harder test than a linear steady response: a finite-amplitude
*instability* problem with a well-understood theoretical pedigree. When
convective heating maintains an elongated strip of cyclonic potential
vorticity (PV) along the Intertropical Convergence Zone (ITCZ) or monsoon
trough, the strip is barotropically unstable: it undulates, pools its PV, and
rolls up into a chain of discrete vortices. Guinn and Schubert (1993)
demonstrated this breakdown in shallow-water dynamics; Nieto Ferreira and
Schubert (1997) showed that the resulting vortices are natural tropical-cyclone
precursors and that the process selects vortex spacings of a few thousand
kilometers; Wang and Magnúsdóttir (2005, 2006) extended the analysis to
three-dimensional flows and documented its synoptic-scale occurrence in the
Pacific. ITCZ breakdown is therefore an attractive probe of a DWP model: for
the experiment to succeed, the model must supply (i) the diabatic generation
of PV, (ii) the barotropic instability of a zonally elongated vorticity
strip, and (iii) the coupling of the growing vortices to the moisture field —
none of which is imposed by the experimental design, which prescribes only a
smooth, time-invariant heating.

The real atmosphere occasionally stages this experiment on its own. In
November 2024, the western North Pacific monsoon trough discretized into four
coexisting tropical cyclones (Yinxing, Toraji, Usagi, and Man-yi) aligned
between roughly 13°N and 18°N — the first November on record (since 1951)
with four simultaneous storms in that basin. We use geostationary
(HIMAWARI) imagery of this event, and of a similar sequence in 2023, as an
observational counterpart to the modeled breakdown (Section 3.7), while
being explicit about what such a comparison can and cannot claim.

This paper makes three contributions. First, we present a finite-time
nonlinear perturbation framework — *perpetual background re-centering* — that
holds the background state exactly steady while the perturbation evolves under
the full nonlinear model operator, and we derive its mathematical
interpretation: because the background is frozen and re-anchored at every
step, the iteration is a forced power iteration that extracts the
fastest-growing finite-time structure of the one-step operator about the basic
state — a nonlinear analogue of a singular vector. The iteration index is a
convergence count of this mode extraction, *not* physical elapsed time; we
retain the shorthand "semi-linear" for the method precisely because, as in
classical instability analysis, it studies perturbation growth about a fixed
basic state (Section 2.3). Second, using this framework we show that
Pangu-Weather reproduces the full ITCZ-breakdown sequence — diabatic PV-band
formation displaced poleward of the heating, roll-up into approximately four
discrete vortices, and co-amplifying column moisture — and we isolate the
responsible couplings with mechanism-denial (moisture- and wind-locking)
experiments. Third, we address
head-on the question of when the spatial convergence sequence of a
mode-extraction algorithm may legitimately be compared with an observed
temporal evolution, and we document the artifacts — including an
off-manifold "shock" response at the first iteration — that arise when a
neural operator is driven outside its training distribution. A companion
line of work will pursue this manifold perspective further.

The remainder of the paper is organized as follows. Section 2 describes the
models, the perturbation framework and its interpretation, the diabatic
forcing, the experiment suite, and the observational data. Section 3 presents
the results: PV-band formation, breakdown, sensitivity to season and heating
structure, mechanism denial, time-step sensitivity, and the observed
counterpart. Section 4 discusses implications and limitations, and the
appendices collect verification material and sensitivity galleries.
