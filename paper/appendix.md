# Appendices

```說明
附錄四部分（依你指示改版：inverse 圖已移除；cos vs 高斯的比較放進 B.1，
註明 cos 版源自 Hakim & Masanam 的做法、結論是無明顯差異）：
A. 方法驗證 —— 漂移去除的精確性（單元測試）、強迫幾何、Pangu 積分 TCWV vs
   FCNv2 原生 TCWV 通道一致性（RMSE ~3.6 kg/m²）。
B. 敏感性圖庫 —— B.1 水平包絡 cos vs 高斯；B.2 振幅掃描；B.3 DJF 季節對照面板
   （等 DJF 高斯 run 跑完會自動有 panels_vort）。
C. 次要觀測事件 —— 2023 年 8–9 月 Saola/Haikui/Kirogi(+Yun-yeung)。
D. 24h vs 6h 完整面板。
```

## Appendix A: Method verification

The perturbation framework rests on the exactness of the drift removal and on
the physical fidelity of the forcing construction; both are verified
independently of the scientific experiments.

*Recurrence and locking.* The re-centering recurrence and the channel-locking
operator $\mathcal{L}$ are verified exactly against hand-computed sequences
on a mock operator and miniature grid (unit tests in
`aux/tests/test_driver_math.py`): the implementation reproduces
$u'_n = M(u_0+u'_{n-1}+f_n) - M(u_0)$ and the zeroing semantics of Steps 2
and 4 to machine precision.

*Forcing geometry.* The horizontal envelope geometry and its boundary
ellipse are verified in Fig. A1, and the four vertical profiles used in
Section 3.3c are shown in Fig. A2.

![Fig. A1](../aux/verification/figures/02_forcing_ellipse.png)
*Fig. A1: Horizontal forcing envelope and boundary ellipse.*

![Fig. A2](../aux/verification/figures/03_vertical_profiles.png)
*Fig. A2: Vertical heating profiles (Deep, stratiform, shallow, uniform).*

*Cross-model moisture consistency.* Pangu's diagnosed
$\mathrm{TCWV}=g^{-1}\!\int q\,dp$ agrees with FCNv2's native TCWV channel on
identical states to RMSE $\approx 3.6$ kg m$^{-2}$ (Fig. A3), validating
cross-model comparison of moisture responses.

![Fig. A3](../aux/verification/figures/04_tcwv_agreement.png)
*Fig. A3: Integrated q (Pangu) versus native TCWV channel (FCNv2).*

*Background and heating as-run.* The JAS background state and the heating
distribution actually applied in the headline run are documented in Figs. A4
and A5.

![Fig. A4](../outputs/JAS/ic_JAS_check.png)
*Fig. A4: JAS 1979–2019 climatological background (vorticity and TCWV).*

![Fig. A5](../outputs/JAS/heating_dist_check.png)
*Fig. A5: Applied heating distribution.*

## Appendix B: Sensitivity gallery

### B.1 Horizontal envelope: Gaussian versus cosine lobes

Two horizontal envelopes were tested for the heating of Section 2.4: the
separable Gaussian used throughout the paper, and an alternative built from
zonal lobes $\cos\!\left(8(\phi-10^\circ)\right)$ under a Gaspari–Cohn
zonal envelope, adapted from the forcing construction of Hakim and Masanam
(2024). Their footprints are compared in Figs. B1a–b, and the resulting
$\zeta'_{850}$ evolutions in Figs. B1c–d: the breakdown proceeds in the same
way in both — same poleward-flank band, same roll-up into a chain of
discrete vortices with similar spacing and latitude — so the choice of
envelope does not control the character of the instability. The amplitudes
do differ: the all-positive Gaussian delivers more net column heating than
the sign-alternating cosine lobes at equal peak rate, and its peak vorticity
response is correspondingly larger (roughly a factor of two). Since the
structure is envelope-independent and the Gaussian is the smoother, simpler
prescription, it is used for the headline experiments.

![Fig. B1a](../aux/investigation/aiforum_repro/figs/heating_dist_gauss.png)
*Fig. B1a: Gaussian envelope.*

![Fig. B1b](../aux/investigation/aiforum_repro/figs/heating_dist.png)
*Fig. B1b: Cosine-lobe envelope (after Hakim and Masanam 2024).*

![Fig. B1c](pic/fig3_panels_vort.png)
*Fig. B1c: $\zeta'_{850}$ evolution, Gaussian envelope (= Fig. 3).*

![Fig. B1d](pic/figB1d_panels_vort.png)
*Fig. B1d: $\zeta'_{850}$ evolution, cosine-lobe envelope.*

### B.2 Amplitude

Peak-response time series across the amplitude sweep (Fig. B2) show
quasi-linear early scaling through a few K day$^{-1}$ and an overdriven
regime by $\sim$10 K day$^{-1}$.

![Fig. B2](../aux/investigation/figs/sweep/pangu/timeseries_amps.png)
*Fig. B2: Amplitude sweep, Pangu, peak responses.*

### B.3 Seasonal control

Snapshot panels of the DJF-background control of Section 3.3a, identical
Gaussian Deep 2.5 K day$^{-1}$ forcing.

![Fig. B3](pic/figB3_panels_vort.png)
*Fig. B3: $\zeta'_{850}$ evolution, DJF background.*

## Appendix C: The August–September 2023 event

A second observed monsoon-trough discretization, 30 August – 6 September
2023, produced Saola, Haikui, and Kirogi, with Yun-yeung forming to the
east (Fig. C1). The event is meridionally less aligned than the November
2024 case but exhibits the same strip-to-vortices morphology.

![Fig. C1](../obs/2023-09_WPac_triple-plus/rollup_IR_Aug30-Sep06.jpg)
*Fig. C1: Himawari IR montage, 30 Aug – 6 Sep 2023.*

## Appendix D: 24-h versus 6-h operator panels

Full snapshot panels for the 6-h experiment of Section 3.6, for comparison
with the 24-h headline panels (Fig. 3).

![Fig. D1](pic/figD1_panels_vort.png)
*Fig. D1: $\zeta'_{850}$ evolution with the 6-h operator (sustained forcing,
scaled to +0.625 K per step — the controlled counterpart of the 24-h run).
Note the land-anchored high-frequency clutter discussed in Section 3.6.*

![Fig. D2](pic/fig3_panels_vort.png)
*Fig. D2: Companion 24-h run from the same pipeline configuration.*
