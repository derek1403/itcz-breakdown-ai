# 4. Discussion and Conclusions

```說明
討論章。內容：
(1) 這些結果對「AI 模式學到了什麼」的意涵 —— 不是背答案：對稱加熱 → 北偏 PV 帶（守恆律的要求）、
    正壓捲渦、風–水氣耦合，都是設計上沒有餵給它的。
(2) 兩模式對比 —— FCNv2 水氣路徑弱很多 → 學到的動力不是架構的必然。
(3) 「模態萃取 vs 觀測演化」問題收尾（§2.3 / §3.7 的呼應）。
(4) 限制之一：day-1 殘響 = manifold shock（流形衝擊）—— 不歸因於物理重力波調整（提出後排除）。
    歸因已依你的提問改寫（詳見 logic/discussion4.3.md）：殘響幾何不是強迫形狀給的，
    是 J（在 off-manifold 點 u0 取的線性化）的結構給的 —— 近緯向對稱背景 → 全球準緯向模態
    （條紋，含遠離強迫處）；陸地/地形等尖銳靜態梯度破壞對稱 → 非條狀錨定異常；
    架構格 → 棋盤格。並先點明背景自身的 shock 被 B 精確吸收（f=0 ⇒ u'≡0）。
    可檢驗區辨：單步出現/不傳播、幾何不隨強迫形狀改變、day-1 振幅標度、白噪聲探針。
(5) 其他限制：渦旋位置混沌、陸地過早長渦度、中緯度過度活躍。
(6) 展望：manifold 探索（你的 Part 2 議程）。
```

## 4.1 What the model has learned

The experiments were designed so that success could not be scripted. The
forcing supplied to Pangu-Weather is a smooth, meridionally symmetric,
time-invariant temperature increment; everything that follows — and each step
of it is a nontrivial dynamical inference — was produced by the learned
operator. The first response is a PV band displaced to the poleward flank of
a symmetric heating, which is what the diabatic PV equation demands of a
fluid on a rotating sphere (Section 3.1); the model was never shown that
equation. The band then destabilizes at the wavenumber and spacing that
barotropic-instability theory selects for such a strip (Section 3.2). The
growth requires, and gets, a two-way wind–moisture coupling, as the
mechanism-denial suite shows by taking it away (Section 3.5). And the
response amplitude is governed by the background state, not the forcing
(Section 3.3) — the signature of a genuine instability of the basic state
rather than a memorized response to heating. Taken together with the steady
linear responses documented by Hakim and Masanam (2024), these results
support the stronger claim: at least for tropical dynamics on synoptic and
planetary scales, the model has internalized dynamical relationships, not
merely climatological correlations.

The cross-model contrast sharpens the point. FCNv2, trained on the same
reanalysis with a different architecture, reproduces the barotropic roll-up
only weakly and requires an order-of-magnitude larger forcing for a
comparable response, with a much weaker moisture pathway. Whatever is
responsible — architecture, training protocol, or the spectral smoothing
tendencies documented for this model class (Bonavita 2024) — the dynamics
recovered by our framework is a property of the individual trained model,
not an inevitability of data-driven forecasting. Dynamical testing of the
kind performed here therefore has discriminating power between models that
headline scores do not.

## 4.2 Mode extraction versus observed evolution

We return to the interpretive question raised in Section 2.3, because it is
the hinge on which the observational comparison turns. Our recurrence holds
the background at $t=0$ forever: there is no wave–mean-flow interaction, and
the iteration is a forced power iteration converging toward the
fastest-growing finite-time structure of the one-step operator about the
basic state — a nonlinear singular vector. The index $n$ counts algorithmic
convergence, not days of weather. The observed November 2024 sequence, by
contrast, is a genuine temporal evolution. We have argued (Section 3.7) that
the comparison between the two is nevertheless meaningful under two explicit
conditions: the comparison is made at the level of converged mode structure,
and the observed background is quasi-stationary over the interval — as the
monsoon trough was during the event week. Under those conditions, nature is
approximately running the fixed-background instability problem that our
algorithm solves, and the agreement in structure (a chain of four vortices
along the trough at several-thousand-kilometer spacing) is evidence about
dynamics, not a coincidence of imagery. Where either condition fails — a
rapidly evolving background, or comparison of intermediate iterates to
intermediate dates — the correspondence should not be pressed, and we have
not pressed it.

## 4.3 Off-manifold artifacts: the day-1 "manifold shock"

The first iteration of every forced experiment exhibits a characteristic
transient: globe-spanning, zonally banded striations — present far outside
the forced sector — together with non-banded anomalies anchored to land,
orography, and coastlines, and grid-scale checkerboard noise. It is tempting
to read the striations as inertia–gravity-wave adjustment to an unbalanced
heating — the physical response a primitive-equation model would produce —
and we considered that reading; but we set it aside, because the
phenomenology does not support it. Physical adjustment is dispersive: it
propagates away from the forcing at identifiable group speeds over a finite
adjustment time. The transient instead appears fully formed within a single
operator application and does not propagate.

The explanation we advance is statistical rather than physical. The trained
operator is reliable only on (a neighborhood of) the manifold
$\mathcal{M}$ of atmospheric states it was fitted to; the forced input
$u_0 + \delta + f$ — a climatological mean plus an idealized heating that no
reanalysis state resembles — lies off that manifold. Note first that the
exact drift removal of Section 2.2 guarantees the background's own
off-manifold correction cannot appear in $u'$ (it is absorbed into $B$
identically); the entire transient lives in the differential response
$M(u_0+\delta)-M(u_0) = \mathbf{J}\delta + \tfrac12\,\delta^\top\mathbf{H}\,
\delta + \cdots$. Off-manifold, *neither term of this expansion is
disciplined by training*: the Jacobian $\mathbf{J}$ is a derivative taken at
a point the network never saw, and the remainder reflects unconstrained
network curvature. The geometry of the transient is therefore set by the
structure of this untrained linearization, not by the shape of the forcing.
Its three components read off directly: the background $u_0$ is nearly
zonally symmetric, so the modes of $\mathbf{J}$ are approximately zonal
harmonics — globally extended bands onto which the global attention
projects even a localized forcing, explaining striations far from the
heated sector; where sharp static features (coastlines, orography) break
that symmetry, the same response anchors locally, explaining the non-banded
land-locked anomalies; and the discrete patch/window architecture
contributes its own fixed-pixel-scale checkerboard. We term this transient
the *manifold shock*. The two readings are distinguishable in principle,
and the distinguishing signatures favor the latter: single-step appearance
versus dispersive timescale; geometry set by the basic state's symmetry and
the model's static sensitivities versus propagation away from the source.
Direct tests — invariance of the striations under changes of forcing shape
and hemisphere, amplitude scaling of the day-1 residue (linear would
implicate $\mathbf{J}$, superlinear the curvature), and a white-noise probe
of $\mathbf{J}$'s preferred modes — are the subject of companion work on
the geometry of DWP state manifolds, and are where we continue the program
sketched in the Introduction.

Practically, the manifold shock is a nuisance signal, and it is one reason
(alongside the mechanisms of Section 3.6) that idealized perturbation
experiments in neural operators must be designed and read with care: some of
what the model returns is dynamics, and some is the geometry of its training
distribution pushing back.

## 4.4 Further limitations

Three further limitations bound our claims. First, the breakdown is
chaotic: exact vortex positions are irreproducible under 0.2 K initial
differences (Section 2.6), so all validation is statistical/structural; this
is a property of the physical problem as much as of the model. Second, the
model grows spurious early vorticity over land within the forced sector,
earlier and stronger than the oceanic character of the process warrants — we
suspect the same land-anchored learned tendencies implicated in the 6-h
noise (Section 3.6) and note it as an open item. Third, the midlatitudes
become more active after nominal day 9 than the tropical confinement of the
forcing would lead one to expect; whether this is a physical teleconnection
(cf. the planetary-wave radiation in Hakim and Masanam 2024) or accumulated
artifact has not been established.

## 4.5 Conclusions

A frozen-background, finite-time nonlinear perturbation framework —
perpetual background re-centering — turns a deep-learning weather model into
an instrument for classical instability analysis. Applied to Pangu-Weather
with an idealized deep-convective ITCZ heating on a JAS climatological basic
state, the framework recovers the complete barotropic ITCZ-breakdown
sequence: diabatically generated PV banding on the poleward flank of the
heating, roll-up into approximately four discrete vortices with realistic
spacing, co-amplifying column moisture, background-controlled growth, and
suppression under moisture denial — and with a structural counterpart in
the November 2024 quadruple-typhoon event. Equally important are the interpretive boundaries
we have drawn: the iteration extracts a nonlinear singular vector rather
than simulating weather; its comparison with observed evolution is licensed
only by background quasi-stationarity and made at the level of converged
structure; and part of the model's response to out-of-distribution forcing
is the geometry of its training manifold rather than atmospheric dynamics.
Within those boundaries, the verdict of the experiment is clear: the
dynamics of ITCZ breakdown is in the machine.
