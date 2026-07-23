# Barotropic Breakdown of the ITCZ in a Global AI Weather Model


---

## Abstract

Data-driven weather prediction (DWP) models now rival operational numerical weather prediction in forecast skill, yet whether they encode atmospheric *dynamics* — rather than sophisticated pattern matching — remains an open question. Following the dynamical-testing paradigm of Hakim and Masanam (2024), we interrogate the Pangu-Weather model with a classical instability problem: the barotropic breakdown of the Intertropical Convergence Zone (ITCZ). We develop a finite-time nonlinear perturbation framework ("perpetual background re-centering") in which the model operator $M$ is applied to a perturbed, steady July–September (JAS) climatological background while the background itself is re-anchored at every step. Because the background is frozen, the iteration constitutes a forced power iteration that extracts the fastest-growing finite-time structure — a nonlinear analogue of a singular vector of $M$ about the basic state — rather than a forecast trajectory. Sustained deep-convective heating ($2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$, centered at 10°N) first generates a potential-vorticity band displaced to the poleward flank of the heating, which subsequently undulates and rolls up into approximately four discrete vortices (peak $\zeta' \approx 9\times10^{-4}\ \mathrm{s^{-1}}$, $\mathrm{TCWV}' \approx 48\ \mathrm{mm}$). Mechanism-denial experiments (moisture and wind locking) show the growth requires the wind–moisture coupling the model has learned. The converged mode structure — a chain of vortices along the monsoon trough — closely resembles the November 2024 western North Pacific event in which four tropical cyclones coexisted, the first such November occurrence on record. We discuss the conditions under which such a mode-extraction sequence can be meaningfully compared with an observed temporal evolution, and the limitations imposed by off-manifold ("manifold shock") artifacts of the neural operator.

---

## Plain-language summary

AI weather models are trained only to predict tomorrow's weather from today's, yet we find that one of them, Pangu-Weather, has internalized a classical piece of tropical dynamics: when a band of tropical heating is switched on, the model spontaneously produces a strip of spinning air that breaks up into a chain of typhoon-like vortices — the same "ITCZ breakdown" process theorized from shallow-water dynamics in the 1990s and visible in satellite imagery, most spectacularly in November 2024 when four typhoons lined up across the western Pacific at once. We introduce a careful experimental protocol that keeps the model's background state fixed so that only the response to the heating grows, and we are explicit about what the method does and does not measure.

# 1. Introduction


Data-driven weather prediction (DWP) models trained end-to-end on reanalysis data now match or exceed the deterministic skill of the world's best operational numerical weather prediction systems. Pangu-Weather, a three-dimensional Earth-specific transformer trained on 39 years of ERA5, outperforms the ECMWF high-resolution forecast on standard headline scores at a fraction of the computational cost (Bi et al. 2023); FourCastNet v2 achieves comparable skill with a spherical Fourier neural operator architecture (Bonev et al. 2023). This success raises a question that forecast scores alone cannot answer: have these models *encoded the dynamics* of the atmosphere, or are they performing a sophisticated form of pattern completion that happens to minimize forecast error (Bonavita 2024)?

One productive way to address this question is to treat the trained network as a dynamical system and subject it to controlled, idealized experiments of the kind traditionally performed with dynamical cores. Hakim and Masanam (2024) pioneered this paradigm: by holding the model on a steady climatological background and inserting localized perturbations — including a steady tropical heat source that elicited a recognizable Matsuno–Gill response (Gill 1980) — they showed that Pangu-Weather reproduces classical dynamical solutions that are, in that form, absent from its training data. Their study is the direct inspiration for the present work, and their steady-background technique is the foundation on which our perturbation framework is built (Section 2).

Here we pose a harder test than a linear steady response: a finite-amplitude *instability* problem with a well-understood theoretical pedigree. When convective heating maintains an elongated strip of cyclonic potential vorticity (PV) along the Intertropical Convergence Zone (ITCZ) or monsoon trough, the strip is barotropically unstable: it undulates, pools its PV, and rolls up into a chain of discrete vortices. Guinn and Schubert (1993) demonstrated this breakdown in shallow-water dynamics; Nieto Ferreira and Schubert (1997) showed that the resulting vortices are natural tropical-cyclone precursors and that the process selects vortex spacings of a few thousand kilometers; Wang and Magnúsdóttir (2005, 2006) extended the analysis to three-dimensional flows and documented its synoptic-scale occurrence in the Pacific. ITCZ breakdown is therefore an attractive probe of a DWP model: for the experiment to succeed, the model must supply (i) the diabatic generation of PV, (ii) the barotropic instability of a zonally elongated vorticity strip, and (iii) the coupling of the growing vortices to the moisture field — none of which is imposed by the experimental design, which prescribes only a smooth, time-invariant heating.

The real atmosphere occasionally stages this experiment on its own. In November 2024, the western North Pacific monsoon trough discretized into four coexisting tropical cyclones (Yinxing, Toraji, Usagi, and Man-yi) aligned between roughly 13°N and 18°N — the first November on record (since 1951) with four simultaneous storms in that basin. We use geostationary (HIMAWARI) imagery of this event, and of a similar sequence in 2023, as an observational counterpart to the modeled breakdown (Section 3.7), while being explicit about what such a comparison can and cannot claim.

This paper makes three contributions. First, we present a finite-time nonlinear perturbation framework — *perpetual background re-centering* — that holds the background state exactly steady while the perturbation evolves under the full nonlinear model operator, and we derive its mathematical interpretation: because the background is frozen and re-anchored at every step, the iteration is a forced power iteration that extracts the fastest-growing finite-time structure of the one-step operator about the basic state — a nonlinear analogue of a singular vector. The iteration index is a convergence count of this mode extraction, *not* physical elapsed time; we retain the shorthand "semi-linear" for the method precisely because, as in classical instability analysis, it studies perturbation growth about a fixed basic state (Section 2.3). Second, using this framework we show that Pangu-Weather reproduces the full ITCZ-breakdown sequence — diabatic PV-band formation displaced poleward of the heating, roll-up into approximately four discrete vortices, and co-amplifying column moisture — and we isolate the responsible couplings with mechanism-denial (moisture- and wind-locking) experiments. Third, we address head-on the question of when the spatial convergence sequence of a mode-extraction algorithm may legitimately be compared with an observed temporal evolution, and we document the artifacts — including an off-manifold "shock" response at the first iteration — that arise when a neural operator is driven outside its training distribution. A companion line of work will pursue this manifold perspective further.

The remainder of the paper is organized as follows. Section 2 describes the models, the perturbation framework and its interpretation, the diabatic forcing, the experiment suite, and the observational data. Section 3 presents the results: PV-band formation, breakdown, sensitivity to season and heating structure, mechanism denial, time-step sensitivity, and the observed counterpart. Section 4 discusses implications and limitations, and the appendices collect verification material and sensitivity galleries.

# 2. Methodology


## 2.1 Models and background states

We use two independently trained global DWP models as our "laboratory atmospheres." The primary model is Pangu-Weather (Bi et al. 2023), a 3D Earth-specific transformer operating on 13 pressure levels (1000–50 hPa; five upper-air variables $z,q,T,u,v$) plus four surface fields (MSLP, $u_{10}$, $v_{10}$, $T_{2m}$) on a 0.25° grid. Pangu is distributed as a family of fixed-lead operators; we use the 24-h operator for all headline experiments and the 6-h operator for the time-step sensitivity test of Section 3.6. The secondary model is FourCastNet v2 (FCNv2; Bonev et al. 2023), a spherical Fourier neural operator with 73 channels including a native total-column-water-vapor (TCWV) channel.

Two architectural facts are load-bearing for the interpretation of our results. First, *Pangu's inputs contain no solar zenith angle, no top-of-atmosphere radiation, and no timestamp of any kind*: the trained network is a pure spatial mapping

$$ X_{t+\Delta t} = M\left(X_{t}\right), $$

with no knowledge of local solar time. Any diurnal information the operator carries must therefore be implicit in the statistics of its training transitions, a point to which we return in Section 3.6. Second, Pangu carries no moisture column integral, so TCWV must be diagnosed as $\mathrm{TCWV} = g^{-1}\int q\, dp$; FCNv2 carries TCWV natively. We verified that the two definitions agree on identical states to within an RMSE of $\sim 3.6\ \mathrm{kg} \cdot \mathrm{m^{-2}}$ (Appendix A), so that moisture responses can be compared across models. Moisture forcing is specified once, as a specific-humidity rate, and converted to each model's native variables ($q$ for Pangu; relative humidity plus the consistent TCWV increment for FCNv2, using the background temperature for the conversion).

The background (basic) state $u_0$ is the 1979–2019 July–September (JAS) climatological mean built from ERA5 (Hersbach et al. 2020). A seasonal climatology has two virtues as a basic state. Dynamically, it contains a realistic, zonally elongated summer ITCZ / monsoon-trough shear zone in the Northern Hemisphere — the substrate the instability needs (Section 3.3 shows the response collapses when the winter climatology is used instead). Methodologically, it is smooth: it contains no individual synoptic systems, so a free-running forecast from it does not immediately spin up weather that would swamp the perturbation signal. The choice of season proves to be a controlling parameter, and we treat it as part of the experiment design rather than a technicality. The background's column moisture, with the heating footprint of Section 2.4 overlaid, is shown in Fig. 2a; the full background fields are documented in Appendix A.

## 2.2 The perturbation framework: perpetual background re-centering

We wish to measure how a perturbation grows *about the fixed basic state* $u_0$ under the full nonlinear model operator $M$. A free rollout of $M$ from $u_0+\delta$ will not do: the trajectory drifts away from $u_0$ (both through the model's climate drift and through genuine synoptic development), and after a few steps the "perturbation" is measured about a background that no longer exists. Hakim and Masanam (2024) addressed this by constructing steady backgrounds; we extend their approach into a recursive scheme that keeps the background steady *for arbitrarily many steps* while letting the perturbation evolve nonlinearly.

Let $M$ denote one model step (24 h unless stated), $u_0$ the steady background, $f_n$ the forcing increment added at step $n$ (Section 2.4), and $u'_n$ the perturbation carried across steps. Define the frozen one-step drift

$$ B \equiv M(u_0), $$

computed once. The iteration is

$$
\begin{aligned}
A_n &= u_0 + u'_{n-1} + f_n, \\
u'_n &= M(A_n) - B, \\
u'_n &\leftarrow \mathcal{L}\left(u'_n\right),
\end{aligned}
\qquad n = 1,\dots,N,
$$

with $u'_0 = 0$ for the standard experiment and $\mathcal{L}$ an optional channel-locking operator used only in the mechanism-denial experiments (Section 2.5). The loop is sketched in Fig. 1. Three properties make this scheme suitable:

![Fig. 1](pic/fig_method_schematic.png)

*Fig. 1: The perpetual background re-centering loop.*

1. *The input to $M$ is always anchored to $u_0$.* The model never sees a free-running trajectory, so the smooth background cannot spin up synoptic-scale "weather" of its own.
2. *The constant drift is removed exactly.* Because the background part of the input is identically $u_0$ at every step, its image under any map is identically $B$; subtracting $B$ therefore removes the model's one-step climate drift without linearization error. (This exactness is a property of re-anchoring, not of any small-amplitude assumption.)
3. *The perturbation evolves fully nonlinearly.* No Jacobian is ever formed or applied; $M$ acts on the complete state $u_0+u'+f$.

The mathematical content of the scheme is seen by Taylor-expanding $M$ about $u_0$. Writing $\mathbf{J} \equiv \partial M/\partial x \,|_{u_0}$ and $\mathbf{H} \equiv \partial^2 M/\partial x^2\,|_{u_0}$, and letting $\delta_n \equiv u'_{n-1} + f_n$ denote the total departure fed to the model at step $n$,

$$
u'_n \;=\; M(u_0+\delta_n) - M(u_0)
\;=\; \underbrace{\mathbf{J}\,\delta_n}_{\text{linear growth}}
\;+\; \underbrace{\tfrac{1}{2}\,\delta_n^{\top}\mathbf{H}\,\delta_n + \cdots}_{O(\lVert\delta_n\rVert^{2})}.
$$

This expansion identifies the two engines of perturbation growth. The linear term $\mathbf{J}\delta_n$ contains the classical instability: directions of state space in which the linearized one-step map about the ITCZ basic state has amplification factors exceeding unity — for our problem, the barotropic instability of the heated vorticity strip. The higher-order terms are the *rectified nonlinear* contributions: vortex merger and axisymmetrization, the finite-amplitude saturation of the roll-up, and the wind–moisture coupling in which perturbation winds converge background moisture that in turn modifies the perturbation heating response. At the amplitudes we force ( $\lVert \delta \rVert$ set by a $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ heating sustained throughout the experiment), these quadratic-and-higher terms are essential and active; the method coincides with a tangent-linear calculation only in the formal limit $\lVert\delta\rVert \to 0$, which we are deliberately not in. Following the usage established for this class of experiment we nevertheless refer to the scheme by the shorthand *semi-linear*; the next subsection explains why that name, understood correctly, is apt.

## 2.3 Interpretation: a nonlinear power iteration, not a forecast

The defining feature of the recurrence above — and the point on which its interpretation hinges — is that the background is re-anchored to $u_0$ at *every* step. The background state therefore never leaves $t=0$: however large the perturbation grows, it is never permitted to modify the flow upon which it grows. By construction there is *no wave–mean-flow interaction* in this system.

This has a precise mathematical consequence. If $M$ were linear, the iteration $u'_n = \mathbf{J}(u'_{n-1} + f_n)$ would be a forced power iteration, whose homogeneous part converges (up to normalization) to the eigenvector of $\mathbf{J}$ with the largest modulus eigenvalue — the fastest-growing mode of the one-step operator about $u_0$. Our iteration is the fully nonlinear analogue: repeated application of $M$, always re-centered on the same $u_0$, *selects and amplifies the fastest-growing finite-time structure of $M$ about the point $u_0$*, saturating at finite amplitude through the $O(\lVert\delta\rVert^2)$ terms. In this sense the converged pattern is a **nonlinear singular vector** of the single-step operator at the basic state, extracted by power iteration.

It follows that the iteration index $n$ must not be read as physical atmospheric time. Although each application of $M$ is nominally a 24-h integration — and we will write "nominal day $n$" for readability — the sequence $n = 1, 2, \dots, N$ is the *convergence history of a mode-extraction algorithm*: early iterations are dominated by the projection of the forcing onto the growing structure, intermediate iterations by quasi-exponential amplification, and late iterations by nonlinear saturation. A real atmosphere evolving over fifteen days would meanwhile change its own background state profoundly; ours is locked to the JAS climatology throughout. This is exactly the sense in which the method deserves the name *semi-linear*: as in classical linear instability analysis, we study the growth of perturbations about a prescribed, fixed basic state — except that the operator applied to the perturbation is the full nonlinear $M$ rather than its linearization.

This interpretation imposes a discipline on how the results may be compared with observations, and we state it here as one of the declared aims of the paper: to establish the conditions under which the *spatial convergence sequence* of such a mode extraction can be meaningfully placed beside an *observed temporal evolution*. The comparison is defensible only to the extent that (i) the observed background (here, the monsoon trough) is quasi-stationary over the observed interval, so that nature is approximately running a fixed-background instability problem too, and (ii) the comparison is made at the level of the *converged mode structure* — the wavenumber, spacing, latitude, and morphology of the vortex chain — rather than as a step-by-date alignment. Section 3.7 applies this standard.

## 2.4 Diabatic forcing

The forcing $f_n$ is an idealized ITCZ-scale heating added to the temperature field at every step during the forcing period. It is separable in the horizontal and vertical.

*Horizontal structure.* The heating is centered at 10°N, 195°E, in the western–central Pacific, with a separable Gaussian envelope

$$ h(\phi,\lambda) \;=\;
\exp\!\left[-\tfrac{1}{2}\left(\frac{\phi-10^\circ}{\sigma_\phi}\right)^{2}
            -\tfrac{1}{2}\left(\frac{\lambda-195^\circ}{\sigma_\lambda}\right)^{2}\right],
\qquad \sigma_\phi \approx 6.4^\circ,\; \sigma_\lambda \approx 65^\circ, $$

i.e., an ITCZ-scale zonally elongated ellipse spanning roughly 5–25°N and a wide Pacific sector (Fig. 2b; its meridional cross-section in Fig. 2d). An alternative cosine-lobe envelope, adapted from the forcing construction of Hakim and Masanam (2024), was also tested; the character of the breakdown is the same under both (the amplitude scales with the net delivered heating), and the comparison is given in Appendix B.

![Fig. 2](../outputs/JAS/pangu24_Deep_2.5Kday_gauss/heating_dist_check.png)

*Fig. 2: The forcing and its background. (a) JAS climatological TCWV with the heating footprint contoured in black (0.25 and 0.6 of the peak rate); (b) horizontal structure of the applied Gaussian heating ($2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ peak, centered at 10°N, 195°E); (c) the Deep vertical profile $Q(p)$; (d) meridional cross-section of the envelope at 195°E.*

*Vertical structure.* The vertical profile is the deep-convective mode

$$ Q(p) \;=\; \sin\!\left(\pi\,\frac{p - 200\ \mathrm{hPa}}{800\ \mathrm{hPa}}\right),
\qquad 200 \le p \le 1000\ \mathrm{hPa}, $$

which peaks at 600 hPa and vanishes at 200 and 1000 hPa (Fig. 2c). This profile is adopted as the leading EOF of observed diabatic heating over tropical oceans:
Chen and Masunaga (2025, their Fig. 2b) show that the first EOF of the $Q_1$ vertical structure in the convectively active tropics is a deep, single-signed mode of essentially this shape. Alternative profiles (stratiform, shallow, and vertically uniform) are used in the sensitivity experiments of Section 3.3.

*Amplitude and duration.* The heating rate is $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ at the horizontal and vertical maximum, applied as a discrete increment at each step (+2.5 K per 24-h step; +0.625 K per 6-h step). We treat this discrete pulse as an approximation to a continuous diabatic heating rate acting over the step — the same convention used for the moisture source in Step 4. The heating is sustained at every iteration for the full length of each experiment ($N = 20$ for the headline run and the profile and amplitude sensitivity runs; $N = 16$ for the mechanism-denial suite and the seasonal control), maintaining the strip against dissipation while the instability develops upon it. Amplitude is a genuinely calibrated quantity: the sweep of Appendix B.2 places the headline $2.5\ \mathrm{K} \cdot \mathrm{day^{-1}}$ near the amplitude that maximizes the organized vortex response — $0.5 - 1\ \mathrm{K} \cdot \mathrm{day^{-1}}$ under-force the strip (weaker, later peaks), while by $5 - 10\ \mathrm{K} \cdot \mathrm{day^{-1}}$ the system is overdriven and the clean roll-up degrades.

## 2.5 The experiment suite

The headline experiment and its mechanism-denial variants form a four-step suite, distinguished by the initial perturbation, the forcing, and the locking operator $\mathcal{L}$:

| Step | Name | $u'_0$ | Forcing | $\mathcal{L}$ (per step) |
|---|---|---|---|---|
| 1 | Standard breakdown | 0 | sustained heating | none |
| 2 | Moisture locking | 0 | sustained heating | moisture channels of $u' \to 0$ |
| 3 | Moisture-only initialization | day-7 moisture anomaly from Step 1 | none | none |
| 4 | Wind locking | day-7 moisture anomaly | persistent moisture source | wind channels of $u' \to 0$ |

The locking operator acts on the *perturbation*, zeroing the designated channels after every step, so that (for example) in Step 2 the model always sees the background moisture field: any moisture–dynamics feedback is denied while the thermal forcing proceeds untouched. Steps 3 and 4 probe the converse: whether a moisture anomaly alone (with and without the winds it would otherwise induce) can excite the instability. Together the four steps factor the coupled growth into its wind and moisture pathways.

Beyond the suite, four families of controls are run: (i) a *seasonal control* — the identical experiment on the DJF climatology, which tests whether the response is set by the background ITCZ rather than by the forcing; (ii) an *external-mode versus boundary-layer heating* pair, which places the heating either in the barotropic (external) vertical mode or in the boundary layer alone (Section 3.4; Appendix B.5); (iii) an *amplitude sweep* ($0.5 - 10 \mathrm{K} \cdot \mathrm{day^{-1}}$; Appendix B.2); and (iv) a *time-step control* repeating Step 1 with the 6-h Pangu operator (Section 3.6). The full suite is run on both Pangu and FCNv2.

## 2.6 Diagnostics

The primary diagnostics are the 850-hPa perturbation relative vorticity $\zeta'_{850}$ and the perturbation column water vapor $\mathrm{TCWV}'$. Because the curl is a linear operator, computing $\zeta'$ directly from the perturbation winds is exact — $\zeta(u') = \zeta(u' + B) - \zeta(B)$ — which we verified numerically to machine precision ($\sim10^{-7}$ relative). Time series of the domain peak values (within the forced sector) track the growth and saturation; snapshot panels at selected iterations show the spatial morphology.

One caveat governs all point-wise comparisons. The breakdown is a chaotic instability: a 0.2 K change in the initial perturbation lowers the day-12 spatial correlation of the vorticity field to 0.42, even though the statistics (peak amplitude, number and spacing of vortices, latitude of the chain) are robust. All comparisons in this paper — against the reference experiment and against observations — are therefore made at the level of structure and statistics, never of exact vortex positions.

## 2.7 Observational data

The observational counterpart uses full-disk imagery from the Himawari geostationary satellite, retrieved from the PCCU/ASRAD archive at daily 00Z: the water-vapor channel and the infrared window channel. Two western North Pacific events are documented: the primary case of 5–14 November 2024, in which the monsoon trough discretized into four coexisting tropical cyclones (Yinxing, Toraji, Usagi, Man-yi), and a secondary case of 30 August – 6 September 2023 (Saola, Haikui, Kirogi, with Yun-yeung forming to the east). For each event we archive the daily full-disk frames, tropical western Pacific crops, and multi-day roll-up montages (Section 3.7; Appendix C).

# 3. Results


## 3.1 Spin-up: a vorticity band on the poleward flank of the heating

The prescribed heating is meridionally symmetric about its center at 10°N, yet the model's first response is not. Within the first two to three iterations a coherent band of positive perturbation vorticity emerges along the *northern* flank of the heated region (Fig. 3a, first panels), with much weaker signal to the south. This asymmetry is exactly what diabatic PV dynamics requires. For heating $\dot\theta$ acting on air with potential vorticity $P$, the material PV source is (Haynes and McIntyre 1987)

$$ \frac{DP}{Dt} \;\approx\; P\,\frac{\partial \dot\theta}{\partial \theta}, $$

below the level of maximum heating, where $\partial\dot\theta/\partial\theta > 0$: diabatic heating amplifies PV in proportion to the PV already present. In the undisturbed tropics the ambient PV is dominated by the planetary contribution, which increases monotonically with latitude ($P \propto f$ at leading order). A meridionally symmetric heating therefore generates more PV on its poleward side than on its equatorward side, and the low-level PV (and vorticity) band that results sits displaced to the north of the heating maximum. This is the same mechanism by which sustained convective heating builds the ITCZ shear zone in PV-theoretic models of the Hadley circulation (Schubert et al. 1991). The model was never told any of this: it receives a symmetric temperature increment and produces the asymmetric PV response that the conservation theorems demand — an early indication that the learned operator carries the relevant dynamics.

![Fig. 3](pic/fig3_panels_vort.png)

*Fig. 3: Snapshot panels of $\zeta'_{850}$ across the iteration (nominal days 0–15). Early panels show the poleward-displaced vorticity band; later panels the roll-up into discrete vortices.*

## 3.2 Barotropic breakdown of the heated strip

As the forcing continues, the vorticity band sharpens and elongates along roughly 8–15°N, and from nominal day 9 onward it undulates, pools its vorticity, and rolls up into discrete vortices — approximately four by nominal day 15, spaced a few thousand kilometers apart along the strip (Fig. 3, later panels). The morphology is the canonical ITCZ breakdown of Guinn and Schubert (1993) and Nieto Ferreira and Schubert (1997): a varicose distortion of a cyclonic PV strip, pooling into proto-vortices connected by filaments, followed by discretization. The perturbation column moisture amplifies in phase with the vortices (Fig. 4), consistent with the wind–moisture coupling analyzed in Section 3.5.

Quantitatively, the peak 850-hPa perturbation vorticity reaches $\zeta' \approx 89 \times 10^{-5}\ \mathrm{s^{-1}}$ at nominal day 12, when four discrete vortices stand along $\sim$ 15°N between roughly 145°E and 170°W, and the peak perturbation column water vapor reaches $\approx 48\ \mathrm{mm}$ at nominal day 14; thereafter the vortices drift poleward and the chain loses its zonal alignment. The co-amplification of the moisture field with the vorticity field, and the emergence of a discrete vortex chain from a smooth zonal forcing, are the two signatures the experiment was designed to test for. Consistent with the chaos caveat of Section 2.6, individual vortex longitudes are sensitive to the experimental details and only the statistics — vortex count, spacing, latitude, amplitude — are robust.

![Fig. 4a](pic/fig4a_panels_tcwv.png)

*Fig. 4a: $\mathrm{TCWV}'$ snapshot panels for the headline run.*

![Fig. 4b](pic/fig4b_timeseries.png)

*Fig. 4b: $\zeta'_{850}$ (left) and $\mathrm{TCWV}'$ (right) at individual vortex centres versus iteration; each line is one tracked vortex branch.*

## 3.3 What controls the response

Having established the breakdown itself, we ask what sets its strength. The sensitivity experiments of Section 2.5 identify three controls — the basic state, the forcing amplitude, and the vertical structure of the heating — and each carries a distinct piece of physics.

The dominant control is the background, not the forcing. Running the identical forcing on the DJF climatology instead of JAS collapses the instability (Fig. 5a). On the summer background the peak vorticity undergoes explosive growth after nominal day 8, reaching $89 \times 10^{-5}\ \mathrm{s^{-1}}$; on the winter background — whose ITCZ lies south of the heated band — it saturates near $14 \times 10^{-5}\ \mathrm{s^{-1}}$ by day 9 and never organizes, a factor of $\sim$6 weaker. The moisture response, by contrast, is nearly identical in the two seasons (Fig. 5b): the column moistening is the direct, quasi-passive thermodynamic response to the sustained heating, available on any background, whereas the vortex growth requires a basic state whose ITCZ shear zone is ripe for barotropic breakdown. The instability, in other words, belongs to the background state, and the heating merely excites it — as barotropic-instability theory would insist.

![Fig. 5](pic/fig5_seasonal_timeseries.png)

*Fig. 5: Seasonal control under identical Gaussian Deep $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ forcing, JAS versus DJF background. (a) Peak $\zeta'_{850}$ versus iteration: explosive growth on the summer background, saturation without organization on the winter background. (b) Peak $\mathrm{TCWV}'$ versus iteration: nearly identical in the two seasons.*

The forcing amplitude, by contrast, sets only where on a familiar curve the experiment sits — and the two response fields part company along it. An amplitude sweep at $0.5$, $1$, $2.5$, $5$, and $10\ \mathrm{K} \cdot \mathrm{day^{-1}}$ (Appendix B.2) shows the column moistening rising monotonically with amplitude (peak $\mathrm{TCWV}'$ climbs from $35$ to $61\ \mathrm{mm}$), consistent with a quasi-passive thermodynamic response. The vortex response, however, is *non-monotonic*: peak $\zeta'$ rises from $\sim 64$ at $0.5$–$1\ \mathrm{K} \cdot \mathrm{day^{-1}}$ to its maximum of $89 \times 10^{-5}\ \mathrm{s^{-1}}$ at the $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ headline value, then *falls back* to $68$ at $5$ and $42$ at $10\ \mathrm{K} \cdot \mathrm{day^{-1}}$, with the peak arriving ever earlier (day 19 → 9). Beyond a few $\mathrm{K} \cdot \mathrm{day^{-1}}$ the forcing is overdriven: the response goes strongly nonlinear from the outset, spreads well beyond the forced strip into the midlatitudes, and the clean four-vortex roll-up never consolidates. The headline $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ is thus close to the amplitude that maximizes the organized vortex response, not merely a point on a rising quasi-linear stretch.

The vertical structure of the heating is the most discriminating control of the three, and — tellingly — the two response fields order the four profiles *differently*. With equal amplitude and horizontal envelope:

| profile | peak $\zeta'$ ($10^{-5}\ \mathrm{s^{-1}}$) | peak $\mathrm{TCWV}'$ (mm) |
|---|---|---|
| Deep (peak 600 hPa) | 89.4 | 48.4 |
| Shallow (peak $\sim$800 hPa) | 76.1 | 51.7 |
| uniform (1000–200 hPa) | 54.0 | 69.2 |
| Stratiform (low-level cooling) | 8.3 | 16.3 |

Three features stand out. First, the profiles that heat the lower free troposphere (Deep, Shallow) build the strongest vortex chains even though both deliver *zero* heating at 1000 hPa. Second, the vertically uniform profile — the one with the largest boundary-layer heating — is markedly weaker in vorticity yet strongest in moisture. Third, stratiform heating, which cools the lower troposphere, kills the instability almost completely while still moistening weakly. (Consistent with Section 2.6, we read the Deep-versus-Shallow difference as within the chaos-dominated uncertainty of peak amplitudes; the Stratiform collapse and the uniform/Deep separation are large and robust.) The full time series are shown in Appendix B.4. The vorticity and moisture responses are evidently controlled by *different functionals of the same profile* $Q(p)$ — identifying those functionals is the subject of the next subsection.

## 3.4 What the vertical profile controls: the low-level diabatic PV source

The theory that fits both orderings is already on the table: it is the diabatic PV source of Section 3.1, now read in the vertical. The interior source $DP/Dt \approx P\,\partial\dot\theta/\partial\theta$ generates cyclonic PV wherever the heating *increases with height*, i.e., below the heating maximum; and heating delivered at the lower boundary itself contributes a separate boundary source — a Bretherton-type PV sheet at the surface (Haynes and McIntyre 1987). Because the strip whose breakdown we measure lives at 850 hPa, the relevant quantity is the source integrated over the layer in which that strip is built, roughly 1000–700 hPa:

$$
S \;=\; \underbrace{\Big[\,Q(700\ \mathrm{hPa}) - Q(1000\ \mathrm{hPa})\,\Big]}_{\text{interior: } \int \partial\dot\theta/\partial z\, dz}
\;+\; \underbrace{\beta\, Q_B}_{\text{surface sheet}},
$$

with $\beta$ an $O(1)$ dilution factor for the surface-concentrated sheet (it must be redistributed over the depth of the strip, so $\beta < 1$). Evaluating $S$ on the model levels for the four profiles and normalizing to the uniform case (with $\beta = 0.55$ fixed by the single calibration condition that $S$ reproduce the uniform-to-Deep ratio):

| profile | interior $Q_{700}{-}Q_{1000}$ | $Q_B$ | $S$ (rel. uniform) | observed $\zeta'$ (rel. uniform) |
|---|---|---|---|---|
| Deep | 0.92 | 0 | 1.66 (calibration) | 1.66 |
| Shallow | 1.15 | 0 | 2.08 | 1.41 |
| uniform | 0.00 | 1 | 1.00 | 1.00 |
| Stratiform | $-0.71$ | 0 | $< 0$ | 0.15 |

The functional reproduces every robust feature of the ordering: Deep and Shallow are strongest because their low-level heating *gradient* is large — the surface value is irrelevant; uniform is intermediate because its interior gradient vanishes and it forces the strip through the (diluted) boundary pathway alone; and Stratiform's low-level *cooling* makes the source negative precisely in the layer where the strip and its moisture supply must be built — the instability is not weakened but switched off. The one free number, $\beta \approx 0.55$, is of the expected order ($O(1)$, $<1$); since it is fixed on the Deep row, that row matches by construction and the Shallow and Stratiform rows are the independent tests. One transparency point deserves emphasis. Within the sine pair the value of $\beta$ is immaterial — Deep and Shallow both have $Q_B = 0$, so their $S$ ratio is pinned at the interior-gradient ratio $1.15/0.92$ regardless of calibration — and $S$ therefore ranks Shallow *above* Deep for any $\beta$, whereas the single realizations rank Deep first. This inversion involves exactly the pair that Section 2.6 assigns to chaos-dominated peak-amplitude uncertainty (the two runs also peak on different nominal days), and we read it as such rather than tune it away; the $\beta$-independent content of the theory — the sign of $S$ and the separation of the sine profiles from uniform — is what the data test, and what they confirm.

The moisture response obeys a different and simpler functional: the mean heating over the moisture-rich boundary layer, $\langle Q\rangle_{1000-850}$, which sets the low-level convergence. Its values (uniform 1.00, Shallow 0.55, Deep 0.28, Stratiform $-0.49$) predict exactly the observed $\mathrm{TCWV}'$ ordering — uniform strongest, Stratiform collapsed — with Deep and Shallow lifted above the passive prediction by the vortex-driven convergence of their strong circulations, the same two-way coupling isolated in Section 3.5.

Figure 6 shows the fingerprint directly, in the field the functional orders. At nominal day 12 the Deep and Shallow profiles have organized discrete vortex chains along the strip; the vertically uniform profile — the external-mode/boundary-only case, with zero interior gradient in the strip-building layer — produces a weaker, less discretized band forced through the surface sheet alone; and the Stratiform profile has essentially no coherent low-level vorticity. The separations between the panels — the sine profiles above uniform, Stratiform extinguished — are the separations of $S$. We stress that the discriminating field is the low-level vorticity, *not* the 500-hPa geopotential height: at 500 hPa the deep-column uniform profile projects most strongly of the four onto the external geopotential mode, exactly the reading this section rejects, and only $\zeta'_{850}$ exposes the low-level strip that $S$ governs (the 500-hPa view of the same four runs, which follows yet a third functional — the column integral — is shown in Appendix B.4, Fig. B5).

An independent pair of experiments corroborates the boundary pathway in isolation. External-mode heating (EX, 1000–50 hPa) and boundary-layer heating (BL, 1000–700 hPa) both have zero interior gradient in the strip-building layer, so both force the strip through the surface sheet alone; with equal boundary amplitude the source $S$ is identical, and the model produces closely similar 500-hPa height responses (Appendix B.5, Fig. B6), consistent with the classical external-mode projection argument discussed there. We note for completeness that a full-column external-mode projection of the heating — integrating $-\partial Q/\partial z$ from surface to top — is *not* the controlling functional: that integral collapses to the boundary values and cancels exactly the interior low-level gradient that the experiments show dominates. The strip is built locally, not by column projection. With this reading, one equation — the diabatic PV source — accounts for both the meridional asymmetry of Section 3.1 (through $P \propto f$) and the vertical-profile fingerprint of Section 3.3 (through $\partial\dot\theta/\partial z$ plus its boundary term): the learned operator behaves, in both respects, as if it carries that equation.


![Fig. 6](../aux/investigation/figs/hakim/exbl_evolution_Deep_Sha_Uni_Str/profiles4_vort850_day12.png)

*Fig. 6: Perturbation 850-hPa relative vorticity $\zeta'_{850}$ at nominal day 12 for the four heating profiles under identical Gaussian Deep-amplitude $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ forcing (JAS background, 24-h operator): Deep and Shallow (top) build discrete vortex chains; the vertically uniform / external-mode case (bottom-left) forms a weaker, less discretized band through the boundary pathway alone; Stratiform (bottom-right) is switched off. Panel titles give the instantaneous peak $|\zeta'|$ (in $10^{-5}\ \mathrm{s^{-1}}$); the green dashed ellipse marks the heating footprint. The robust separations in the panels — the sine profiles above uniform, Stratiform switched off — are the separations of the low-level PV source $S$; the Deep–Shallow pair order lies within single-run variability (Section 2.6). The companion 500-hPa comparison of the same four runs, and the EX/BL boundary-pathway pair, are in Appendix B.4–B.5.*

## 3.5 Mechanism denial: the wind–moisture coupling is necessary

The four-step suite factors the growth into its pathways (Fig. 7).

The moisture-locking experiment gives the sharpest verdict. With the perturbation moisture zeroed at every step (Step 2), the identical heating produces almost no vortex growth: the peak perturbation vorticity reaches only $\approx 5.5 \times 10^{-5}\ \mathrm{s^{-1}}$, a suppression of roughly $94\%$ relative to the standard run. Denying the model its moisture anomaly removes the co-amplification between converging perturbation winds and column moisture, and with it, essentially the entire instability — the learned breakdown is a *moist* barotropic breakdown. Conversely, initializing with the day-7 moisture anomaly alone (Step 3) tests whether a moisture field can excite the instability without its accompanying winds: the model spins up a vigorous vortex response from moisture alone, reaching $\zeta' \approx 79 \times 10^{-5}\ \mathrm{s^{-1}}$ within nine iterations — comparable in amplitude to the standard run, and earlier, since the experiment begins from a mature moisture seed. The learned coupling thus operates in both directions: winds build moisture (Step 1 vs. 2), and moisture builds winds (Step 3). Finally, locking the winds while sustaining the moisture source (Step 4) isolates the moisture evolution with the dynamical feedback denied: the column moisture then accumulates steadily (to $\approx 53\ \mathrm{mm}$ by day 16) without ever organizing into vortices — moisture alone, denied its winds, is inert. Taken together, the suite shows that the full breakdown requires the two-way coupling — winds converging moisture, moisture sustaining the vortices — that the model has evidently learned from data. On FCNv2 the moisture pathway is far weaker at equal forcing, requiring an order of magnitude larger amplitude for a comparable response, a model contrast we return to in Section 4.

![Fig. 7](pic/fig7_steps_overlay.png)

*Fig. 7: The four-step mechanism-denial suite (Pangu, JAS background, 24-h operator). (a) Peak $\zeta'_{850}$ versus iteration: moisture-locking (Step 2) suppresses the growth almost entirely, while a moisture-only initialization (Step 3) excites it. (b) Peak $\mathrm{TCWV}'$ versus iteration: the wind-locked run (Step 4) accumulates moisture steadily without ever organizing.*

## 3.6 Sensitivity to the operator time step: 24-h versus 6-h

Repeating the headline experiment with the 6-h Pangu operator (four applications per nominal day, forcing scaled to +0.625 K per step, sustained as in the 24-h run) yields a visibly noisier evolution: the vorticity band and a subsequent roll-up are present, but embedded in filamentary, land-anchored, high-frequency clutter absent from the 24-h run, and the discrete four-vortex chain never emerges as cleanly (Fig. 8). The peak amplitudes are also inflated ( $\zeta' \approx 101$ vs. $89 \times 10^{-5}\ \mathrm{s^{-1}}$ ; $\mathrm{TCWV}' \approx 77$ vs. $48\ \mathrm{mm}$ ), the moisture field especially.

We emphasize at the outset what this difference is *not*. Pangu's inputs contain no solar zenith angle, no top-of-atmosphere radiation, and no clock (Section 2.1); the operator cannot "know what time it is," so naive diurnal-cycle aliasing is not an available explanation. Two mechanisms, both consistent with the architecture, account for the difference:

1. *Statistically learned diurnal tendencies.* The 6-h operator was trained on state transitions that straddle sunrise and sunset; over land, those transitions contain a strong systematic heating or cooling signal. A purely spatial map can and does absorb such signals into its learned tendency, conditioned on the spatial fingerprints of the state (e.g., land–sea temperature contrast patterns). The 24-h operator, by contrast, always maps a state to the *same local solar time* 24 h later, so the diurnal signal integrates out of its training targets. Under our frozen-background recurrence, the 6-h operator therefore keeps injecting land-anchored heating/cooling responses into $u'$ — the state it sees is perpetually "the same time of day," while its learned tendency includes a diurnal expectation — and this contamination has no counterpart in the 24-h chain.

2. *Autoregressive error accumulation.* Reaching the same nominal lead requires four times as many applications of $M$. Single-step artifacts of the network — checkerboard and other high-wavenumber structures, and ordinary one-step error — compound four times per nominal day instead of once. The 6-h chain is therefore intrinsically noisier than the 24-h chain, independent of any diurnal consideration.

Both mechanisms predict exactly what is observed: excess high-frequency variance, preferentially anchored to land, superposed on an otherwise similar breakdown. For the purposes of this study the 24-h operator is therefore the cleaner instrument, and all headline results use it.

![Fig. 8](pic/fig8_6h_vs_24h_day12.png)

*Fig. 8: $\zeta'_{850}$ at nominal day 12 under identical sustained Gaussian Deep $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ forcing. (a) The 24-h operator: four discrete vortices along the strip. (b) The 6-h operator: a noisier field with filamentary, land-anchored clutter and no clean vortex chain. Full snapshot panels for both runs are in Appendix D.*

## 3.7 An observed counterpart: the November 2024 quadruple-typhoon event

Between 5 and 14 November 2024 the western North Pacific monsoon trough discretized into four coexisting tropical cyclones — Yinxing, Toraji, Usagi, and Man-yi — aligned between roughly 13°N and 18°N: the first November on record (since 1951) with four simultaneous storms in the basin. Himawari infrared imagery (Fig. 9) shows the sequence: an elongated convective trough with two incipient centers (6–7 Nov), progressive discretization (8–9 Nov), and four distinct vortices in a row (10–13 Nov), which then translate west-northwestward and poleward. The morphology — a zonally aligned chain of vortices emerging from a monsoon-trough strip, with spacings of a few thousand kilometers — is the observational face of the same barotropic breakdown the model produces, as anticipated by the theoretical and observational literature (Guinn and Schubert 1993; Nieto Ferreira and Schubert 1997; Wang and Magnúsdóttir 2006). A second, less clean event from August–September 2023 is shown in Appendix C.

The discipline of Section 2.3 governs what we claim here. The model's sequence $n = 9 \to 12 \to 15$ is the convergence history of a mode-extraction iteration about a frozen background; the observed 7 → 9 → 11 November sequence is a true temporal evolution over a background that is itself evolving. A step-by-date alignment of the two would be dynamically indefensible, and we do not make one. The comparison we do make is structural: the *converged* modeled mode — a chain of approximately four vortices along $\sim$10–15°N with several-thousand-kilometer spacing, co-located vorticity and moisture maxima, and poleward-flank genesis — is the structure the real monsoon trough produced. The comparison is meaningful, rather than merely suggestive, to the degree that the observed background satisfied the fixed-background premise: during the event week the monsoon trough remained quasi-stationary as a large-scale feature while the vortices grew upon it, which is precisely the regime in which a fixed-background instability calculation is the appropriate idealization. Establishing this correspondence — converged extracted mode versus observed end-state structure, under a quasi-stationary background — is the sense in which we consider the observations to corroborate the modeled breakdown.

![Fig. 9](pic/fig9_model_vs_obs.png)

*Fig. 9: (a) Top row: modeled $\zeta'_{850}$ at iterations 6, 9, 12, 15 of the mode extraction (frozen JAS background). (b) Bottom row: Himawari infrared imagery, 00Z 7–13 November 2024, as the western North Pacific monsoon trough discretizes into four coexisting tropical cyclones (Yinxing, Toraji, Usagi, Man-yi). The two rows are deliberately labeled in different units — iterations versus dates — because the comparison is of structure, not of a time axis (Section 2.3). Full eight-panel IR montage: `../obs/2024-11_WPac_quad-typhoon/rollup_IR_Nov06-13.jpg`.*

# 4. Discussion and Conclusions

## 4.1 What the model has learned

The experiments were designed so that success could not be scripted. The forcing supplied to Pangu-Weather is a smooth, meridionally symmetric, time-invariant temperature increment; everything that follows — and each step of it is a nontrivial dynamical inference — was produced by the learned operator. The first response is a PV band displaced to the poleward flank of a symmetric heating, which is what the diabatic PV equation demands of a fluid on a rotating sphere (Section 3.1); the model was never shown that equation. The band then destabilizes at the wavenumber and spacing that barotropic-instability theory selects for such a strip (Section 3.2). The growth requires, and gets, a two-way wind–moisture coupling, as the mechanism-denial suite shows by taking it away (Section 3.5). And the response amplitude is governed by the background state, not the forcing (Section 3.3) — the signature of a genuine instability of the basic state rather than a memorized response to heating. Taken together with the steady linear responses documented by Hakim and Masanam (2024), these results support the stronger claim: at least for tropical dynamics on synoptic and planetary scales, the model has internalized dynamical relationships, not merely climatological correlations.

The cross-model contrast sharpens the point. FCNv2, trained on the same reanalysis with a different architecture, reproduces the barotropic roll-up only weakly and requires an order-of-magnitude larger forcing for a comparable response, with a much weaker moisture pathway. Whatever is responsible — architecture, training protocol, or the spectral smoothing tendencies documented for this model class (Bonavita 2024) — the dynamics recovered by our framework is a property of the individual trained model, not an inevitability of data-driven forecasting. Dynamical testing of the kind performed here therefore has discriminating power between models that headline scores do not.

## 4.2 Mode extraction versus observed evolution

We return to the interpretive question raised in Section 2.3, because it is the hinge on which the observational comparison turns. Our recurrence holds the background at $t=0$ forever: there is no wave–mean-flow interaction, and the iteration is a forced power iteration converging toward the fastest-growing finite-time structure of the one-step operator about the basic state — a nonlinear singular vector. The index $n$ counts algorithmic convergence, not days of weather. The observed November 2024 sequence, by contrast, is a genuine temporal evolution. We have argued (Section 3.7) that the comparison between the two is nevertheless meaningful under two explicit conditions: the comparison is made at the level of converged mode structure, and the observed background is quasi-stationary over the interval — as the monsoon trough was during the event week. Under those conditions, nature is approximately running the fixed-background instability problem that our algorithm solves, and the agreement in structure (a chain of four vortices along the trough at several-thousand-kilometer spacing) is evidence about dynamics, not a coincidence of imagery. Where either condition fails — a rapidly evolving background, or comparison of intermediate iterates to intermediate dates — the correspondence should not be pressed, and we have not pressed it.

## 4.3 Off-manifold artifacts: the day-1 "manifold shock"

The first iteration of every forced experiment exhibits a characteristic transient: globe-spanning, zonally banded striations — present far outside the forced sector — together with non-banded anomalies anchored to land, orography, and coastlines, and grid-scale checkerboard noise. It is tempting to read the striations as inertia–gravity-wave adjustment to an unbalanced heating — the physical response a primitive-equation model would produce — and we considered that reading; but we set it aside, because the phenomenology does not support it. Physical adjustment is dispersive: it propagates away from the forcing at identifiable group speeds over a finite adjustment time. The transient instead appears fully formed within a single operator application and does not propagate.

The explanation we advance is statistical rather than physical. The trained operator is reliable only on (a neighborhood of) the manifold $\mathcal{M}$ of atmospheric states it was fitted to; the forced input $u_0 + \delta + f$ — a climatological mean plus an idealized heating that no reanalysis state resembles — lies off that manifold. Note first that the exact drift removal of Section 2.2 guarantees the background's own off-manifold correction cannot appear in $u'$ (it is absorbed into $B$ identically); the entire transient lives in the differential response $M(u_0+\delta)-M(u_0) = \mathbf{J}\delta + \tfrac12\,\delta^\top\mathbf{H}\, \delta + \cdots$. Off-manifold, *neither term of this expansion is disciplined by training*: the Jacobian $\mathbf{J}$ is a derivative taken at a point the network never saw, and the remainder reflects unconstrained network curvature. The geometry of the transient is therefore set by the structure of this untrained linearization, not by the shape of the forcing. Its three components read off directly: the background $u_0$ is nearly zonally symmetric, so the modes of $\mathbf{J}$ are approximately zonal harmonics — globally extended bands onto which the global attention projects even a localized forcing, explaining striations far from the heated sector; where sharp static features (coastlines, orography) break that symmetry, the same response anchors locally, explaining the non-banded land-locked anomalies; and the discrete patch/window architecture contributes its own fixed-pixel-scale checkerboard. We term this transient the *manifold shock*. The two readings are distinguishable in principle, and the distinguishing signatures favor the latter: single-step appearance versus dispersive timescale; geometry set by the basic state's symmetry and the model's static sensitivities versus propagation away from the source. Direct tests — invariance of the striations under changes of forcing shape and hemisphere, amplitude scaling of the day-1 residue (linear would implicate $\mathbf{J}$, superlinear the curvature), and a white-noise probe of $\mathbf{J}$'s preferred modes — are the subject of companion work on the geometry of DWP state manifolds, and are where we continue the program sketched in the Introduction.

Practically, the manifold shock is a nuisance signal, and it is one reason (alongside the mechanisms of Section 3.6) that idealized perturbation experiments in neural operators must be designed and read with care: some of what the model returns is dynamics, and some is the geometry of its training distribution pushing back.

## 4.4 Further limitations

Three further limitations bound our claims. First, the breakdown is chaotic: exact vortex positions are irreproducible under $0.2 \mathrm{K}$ initial differences (Section 2.6), so all validation is statistical/structural; this is a property of the physical problem as much as of the model. Second, the model grows spurious early vorticity over land within the forced sector, earlier and stronger than the oceanic character of the process warrants — we suspect the same land-anchored learned tendencies implicated in the 6-h noise (Section 3.6) and note it as an open item. Third, the midlatitudes become more active after nominal day 9 than the tropical confinement of the forcing would lead one to expect; whether this is a physical teleconnection (cf. the planetary-wave radiation in Hakim and Masanam 2024) or accumulated artifact has not been established.

## 4.5 Conclusions

A frozen-background, finite-time nonlinear perturbation framework — perpetual background re-centering — turns a data-driven weather model into an instrument for classical instability analysis. Applied to Pangu-Weather with an idealized deep-convective ITCZ heating on a JAS climatological basic state, the framework recovers the complete barotropic ITCZ-breakdown sequence: diabatically generated PV banding on the poleward flank of the heating, roll-up into approximately four discrete vortices with realistic spacing, co-amplifying column moisture, background-controlled growth, and suppression under moisture denial — and with a structural counterpart in the November 2024 quadruple-typhoon event. Equally important are the interpretive boundaries we have drawn: the iteration extracts a nonlinear singular vector rather than simulating weather; its comparison with observed evolution is licensed only by background quasi-stationarity and made at the level of converged structure; and part of the model's response to out-of-distribution forcing is the geometry of its training manifold rather than atmospheric dynamics. Within those boundaries, the verdict of the experiment is clear: the dynamics of ITCZ breakdown is in the machine.


# References


Bi, K., Xie, L., Zhang, H., Chen, X., Gu, X., and Tian, Q., 2023: Accurate
medium-range global weather forecasting with 3D neural networks. *Nature*,
**619**, 533–538, doi: [10.1038/s41586-023-06185-3](https://doi.org/10.1038/s41586-023-06185-3).

Bonavita, M., 2024: On some limitations of current machine learning weather
prediction models. *Geophys. Res. Lett.*, **51**, e2023GL107377,
doi: [10.1029/2023GL107377](https://doi.org/10.1029/2023GL107377).

Bonev, B., Kurth, T., Hundt, C., Pathak, J., Baust, M., Kashinath, K., and
Anandkumar, A., 2023: Spherical Fourier neural operators: Learning stable
dynamics on the sphere. *Proc. 40th Int. Conf. on Machine Learning (ICML)*,
PMLR 202, 2806–2823. (arXiv: [2306.03838](https://arxiv.org/abs/2306.03838))

Chen, Y.-C., and Masunaga, H., 2025: Vertical velocity and diabatic heating
top-heaviness in the convective evolution over tropical oceans. *J. Geophys.
Res. Atmos.*, **130**, e2024JD043054, doi: [10.1029/2024JD043054](https://doi.org/10.1029/2024JD043054).

Gill, A. E., 1980: Some simple solutions for heat-induced tropical
circulation. *Quart. J. Roy. Meteor. Soc.*, **106**, 447–462,
doi: [10.1002/qj.49710644905](https://doi.org/10.1002/qj.49710644905).

Guinn, T. A., and Schubert, W. H., 1993: Hurricane spiral bands. *J. Atmos.
Sci.*, **50**, 3380–3404,
[journals.ametsoc.org](https://journals.ametsoc.org/view/journals/atsc/50/20/1520-0469_1993_050_3380_hsb_2_0_co_2.xml).

Hakim, G. J., and Masanam, S., 2024: Dynamical tests of a deep learning
weather prediction model. *Artif. Intell. Earth Syst.*, **3**, e230090,
doi: [10.1175/AIES-D-23-0090.1](https://doi.org/10.1175/AIES-D-23-0090.1).

Haynes, P. H., and McIntyre, M. E., 1987: On the evolution of vorticity and
potential vorticity in the presence of diabatic heating and frictional or
other forces. *J. Atmos. Sci.*, **44**, 828–840,
[journals.ametsoc.org](https://journals.ametsoc.org/view/journals/atsc/44/5/1520-0469_1987_044_0828_oteova_2_0_co_2.xml).

Hersbach, H., and Coauthors, 2020: The ERA5 global reanalysis. *Quart. J.
Roy. Meteor. Soc.*, **146**, 1999–2049, doi: [10.1002/qj.3803](https://doi.org/10.1002/qj.3803).

Nieto Ferreira, R., and Schubert, W. H., 1997: Barotropic aspects of ITCZ
breakdown. *J. Atmos. Sci.*, **54**, 261–285,
[journals.ametsoc.org](https://journals.ametsoc.org/view/journals/atsc/54/2/1520-0469_1997_054_0261_baoib_2.0.co_2.xml).

Schubert, W. H., Ciesielski, P. E., Stevens, D. E., and Kuo, H.-C., 1991:
Potential vorticity modeling of the ITCZ and the Hadley circulation.
*J. Atmos. Sci.*, **48**, 1493–1509,
[journals.ametsoc.org](https://journals.ametsoc.org/view/journals/atsc/48/12/1520-0469_1991_048_1493_pvmoti_2_0_co_2.xml).

Wang, C.-C., and Magnúsdóttir, G., 2005: ITCZ breakdown in three-dimensional
flows. *J. Atmos. Sci.*, **62**, 1497–1512,
doi: [10.1175/JAS3409.1](https://doi.org/10.1175/JAS3409.1).

Wang, C.-C., and Magnúsdóttir, G., 2006: The ITCZ in the central and eastern
Pacific on synoptic time scales. *Mon. Wea. Rev.*, **134**, 1405–1421,
doi: [10.1175/MWR3130.1](https://doi.org/10.1175/MWR3130.1).

---

# Appendices

## Appendix A: Method verification

The perturbation framework rests on the exactness of the drift removal and on the physical fidelity of the forcing construction; both are verified independently of the scientific experiments.

*Recurrence and locking.* The re-centering recurrence and the channel-locking operator $\mathcal{L}$ are verified exactly against hand-computed sequences on a mock operator and miniature grid (unit tests in `aux/tests/test_driver_math.py`): the implementation reproduces $u'_n = M(u_0+u'_{n-1}+f_n) - M(u_0)$ and the zeroing semantics of Steps 2 and 4 to machine precision.

*Forcing geometry.* The horizontal envelope actually applied in every production run is documented, per run, by the `heating_dist_check.png` generated in each run directory, and for the headline configuration in Fig. 2 of the main text. The four vertical profiles available to the sensitivity experiments of Section 3.3 are shown in Fig. A1.

![Fig. A1](../aux/verification/figures/03_vertical_profiles.png)

*Fig. A1: Vertical heating profiles (Deep, stratiform, shallow, uniform).*

*Cross-model moisture consistency.* Pangu's diagnosed $\mathrm{TCWV}=g^{-1}\!\int q\,dp$ agrees with FCNv2's native TCWV channel on identical states to RMSE $\approx 3.6\ \mathrm{kg} \cdot \mathrm{m^{-2}}$ (Fig. A2), validating cross-model comparison of moisture responses.

![Fig. A2](../aux/verification/figures/04_tcwv_agreement.png)

*Fig. A2: Integrated q (Pangu) versus native TCWV channel (FCNv2).*

*Background as-run.* The full JAS background state of the headline run is documented in Fig. A3; the heating actually applied is Fig. 2 of the main text.

![Fig. A3](../outputs/JAS/ic_JAS_check.png)

*Fig. A3: JAS 1979–2019 climatological background (vorticity and TCWV).*

## Appendix B: Sensitivity gallery

### B.1 Horizontal envelope: Gaussian versus cosine lobes

Two horizontal envelopes were tested for the heating of Section 2.4: the separable Gaussian used throughout the paper, and an alternative built from zonal lobes $\cos\!\left(8(\phi-10^\circ)\right)$ under a Gaspari–Cohn zonal envelope, adapted from the forcing construction of Hakim and Masanam (2024). Their footprints are compared in Figs. B1a–b, and the resulting $\zeta'_{850}$ evolutions in Figs. B1c–d: the breakdown proceeds in the same way in both — same poleward-flank band, same roll-up into a chain of discrete vortices with similar spacing and latitude — so the choice of envelope does not control the character of the instability. The amplitudes do differ: the all-positive Gaussian delivers more net column heating than the sign-alternating cosine lobes at equal peak rate, and its peak vorticity response is correspondingly larger (roughly a factor of two). Since the structure is envelope-independent and the Gaussian is the smoother, simpler prescription, it is used for the headline experiments.

![Fig. B1a](../aux/investigation/aiforum_repro/figs/heating_dist_gauss.png)

*Fig. B1a: Gaussian envelope.*

![Fig. B1b](../aux/investigation/aiforum_repro/figs/heating_dist.png)

*Fig. B1b: Cosine-lobe envelope (after Hakim and Masanam 2024).*

![Fig. B1c](pic/fig3_panels_vort.png)

*Fig. B1c: $\zeta'_{850}$ evolution, Gaussian envelope (= Fig. 3).*

![Fig. B1d](pic/figB1d_panels_vort.png)

*Fig. B1d: $\zeta'_{850}$ evolution, cosine-lobe envelope.*

### B.2 Amplitude

Peak-response time series across the amplitude sweep — the headline configuration (Pangu 24-h operator, JAS background, Gaussian Deep heating, sustained) rerun at $0.5$, $1$, $5$, and $10\ \mathrm{K} \cdot \mathrm{day^{-1}}$ alongside the $2.5\ \mathrm{K} \cdot \mathrm{day^{-1}}$ headline run — are shown in Fig. B2. The two fields diverge along the sweep. The column moistening (panel b) increases monotonically with amplitude, peak $\mathrm{TCWV}'$ rising from $34.6\ \mathrm{mm}$ at $0.5\ \mathrm{K} \cdot \mathrm{day^{-1}}$ to $61.2\ \mathrm{mm}$ at $10\ \mathrm{K} \cdot \mathrm{day^{-1}}$ — the quasi-passive thermodynamic response. The vortex response (panel a) is *non-monotonic*: peak $\zeta'_{850}$ is $64.0$ and $63.3 \times 10^{-5}\ \mathrm{s^{-1}}$ at $0.5$ and $1\ \mathrm{K} \cdot \mathrm{day^{-1}}$, maximizes at $89.4$ at the $2.5\ \mathrm{K} \cdot \mathrm{day^{-1}}$ headline value, then declines to $68.1$ at $5$ and $42.3$ at $10\ \mathrm{K} \cdot \mathrm{day^{-1}}$, the peak arriving progressively earlier (nominal day 19 → 15 → 12 → 12 → 9). The headline amplitude therefore sits near the optimum for the organized breakdown: below it the strip is under-forced and slow to roll up; well above it the response goes strongly nonlinear from the outset, spreads well beyond the forced strip into the midlatitudes, and the clean four-vortex chain never consolidates.

![Fig. B2](pic/figB2_amp_sweep.png)

*Fig. B2: Amplitude sweep in the headline configuration (five amplitudes $0.5$–$10\ \mathrm{K} \cdot \mathrm{day^{-1}}$). (a) Peak $\zeta'_{850}$ versus iteration — non-monotonic, maximized at the $2.5\ \mathrm{K} \cdot \mathrm{day^{-1}}$ headline value. (b) Peak $\mathrm{TCWV}'$ versus iteration — monotonically increasing with amplitude.*

### B.3 Seasonal control

Snapshot panels of the DJF-background control of Section 3.3, identical Gaussian Deep $2.5 \mathrm{K} \cdot \mathrm{day^{-1}}$ forcing.

![Fig. B3](pic/figB3_panels_vort.png)

*Fig. B3: $\zeta'_{850}$ evolution, DJF background.*

### B.4 Vertical-profile sensitivity

Peak-response time series for the four vertical heating profiles of Section 3.3 (identical horizontal envelope and amplitude; runs `outputs/JAS/pangu24_{Deep,Shallow,uniform,Stratiform}_2.5Kday_gauss`). The curves display the two pathways analyzed in Section 3.4: uniform grows earliest (surface-sheet pathway) but saturates lowest in vorticity while leading in moisture throughout; Deep and Shallow amplify later and higher (interior PV-source pathway); Stratiform never grows in either field.

![Fig. B4](pic/figB4_profiles_overlay.png)

*Fig. B4: Vertical-profile sensitivity. (a) Peak $\zeta'_{850}$ versus iteration. (b) Peak $\mathrm{TCWV}'$ versus iteration.*

The same four runs viewed at 500 hPa (Fig. B5) complete the functional accounting of Section 3.4. The mid-tropospheric height response is not the strip but the far-field stationary-wave response to the tropical heat source, and its amplitude follows yet a third functional of the profile: the net column heating $\int Q\,dp$, which is largest for uniform ($1.00$), then Deep ($2/\pi \approx 0.64$), then Shallow ($\approx 0.45$), and *vanishes identically* for Stratiform, whose upper-level heating and low-level cooling cancel in the column integral. Accordingly, Deep, Shallow, and uniform produce wave trains of nearly the same geometry — the pattern is set by the source location and the frozen background, which are common to all four runs, so once the response is excited it converges to the background's preferred far-field structure and the profiles differ only in amplitude — while Stratiform, with zero net column heating and no growing strip, leaves the 500-hPa field nearly unperturbed. The three response fields thus read three different moments of the same $Q(p)$: $\zeta'_{850}$ the low-level source $S$, $\mathrm{TCWV}'$ the boundary-layer mean $\langle Q\rangle_{1000-850}$, and $z'_{500}$ the column integral — which is also why Section 3.4 warns that the 500-hPa field, where uniform is strongest, is the wrong place to look for the strip-building pathway.

![Fig. B5](../aux/investigation/figs/hakim/exbl_evolution_Deep_Sha_Uni_Str/profiles4_500z_day20.png)

*Fig. B5: Perturbation 500-hPa geopotential height at nominal day 20 for the four vertical profiles (same runs as Fig. B4; contour interval 30 m, red positive, blue dashed negative; green dashed ellipse marks the heating footprint). Deep, Shallow, and uniform excite closely similar far-field wave trains, strongest for uniform; Stratiform, whose net column heating integrates to zero, leaves the field nearly flat.*

### B.5 Boundary-pathway check: external-mode versus boundary-layer heating

A classical vertical-mode argument holds that the projection of a heating profile onto the external (barotropic) mode, $\int -(\partial Q/\partial z)\,\Psi_0\,dz$ with the external-mode structure function $\Psi_0(z)$ nearly constant in the vertical, collapses by parts to the boundary values of $Q$ — essentially $Q_B$ at the surface. Two heatings with equal surface amplitude should therefore produce the same external-mode (mid-tropospheric height) response *regardless of how much total heat they deposit in the column*. The pair of experiments in Fig. B6 tests exactly this: external-mode heating (EX, all levels 1000–50 hPa) versus boundary-layer heating (BL, 1000–700 hPa only) at equal amplitude — the EX column receives several times the total heating of BL — in a Hakim–Masanam-style configuration (steady heating in an elliptical footprint centered at 0°N, 120°E, at $0.1$ and $0.5\ \mathrm{K} \cdot \mathrm{day^{-1}}$; note this auxiliary configuration differs from the headline forcing of Fig. 2). At both amplitudes the 500-hPa height responses of EX and BL are nearly indistinguishable, as the projection argument demands: a nontrivial check that the learned operator respects the modal structure of the response to heating. In the language of Section 3.4 the pair is equally clean: both profiles have zero interior gradient in the strip-building layer and equal $Q_B$, hence equal low-level PV source $S$ — the pure boundary pathway in isolation. The column projection validated here is, however, *not* the functional that controls the low-level strip (Section 3.4 shows the interior gradient dominates there), which is why this check lives in the appendix rather than the main text.

![Fig. B6](../aux/investigation/figs/hakim/exbl_evolution_EX_BL/day12.png)

*Fig. B6: Perturbation 500-hPa geopotential height at nominal day 12, external-mode heating (EX, top) versus boundary-layer heating (BL, bottom), at $0.1\ \mathrm{K} \cdot \mathrm{day^{-1}}$ (left) and $0.5\ \mathrm{K} \cdot \mathrm{day^{-1}}$ (right); red dashed ellipse marks the heating footprint. Each EX panel is nearly identical to the BL panel below it, as the external-mode projection argument predicts.*

## Appendix C: The August–September 2023 event

A second observed monsoon-trough discretization, 30 August – 6 September 2023, produced Saola, Haikui, and Kirogi, with Yun-yeung forming to the east (Fig. C1). The event is meridionally less aligned than the November 2024 case but exhibits the same strip-to-vortices morphology.

![Fig. C1](../obs/2023-09_WPac_triple-plus/rollup_IR_Aug30-Sep06.jpg)

*Fig. C1: Himawari IR montage, 30 Aug – 6 Sep 2023.*

## Appendix D: 24-h versus 6-h operator panels

Full snapshot panels for the 6-h experiment of Section 3.6, for comparison with the 24-h headline panels (Fig. 3).

![Fig. D1](pic/figD1_panels_vort.png)

*Fig. D1: $\zeta'_{850}$ evolution with the 6-h operator (sustained forcing, scaled to +0.625 K per step — the controlled counterpart of the 24-h run). Note the land-anchored high-frequency clutter discussed in Section 3.6.*

![Fig. D2](pic/fig3_panels_vort.png)

*Fig. D2: Companion 24-h run from the same pipeline configuration.*

