# 4. Discussion and Conclusions

```說明
討論章。內容：
(1) 這些結果對「AI 模式學到了什麼」的意涵 —— 不是背答案：對稱加熱 → 北偏 PV 帶（守恆律的要求）、
    正壓捲渦、風–水氣耦合，都是設計上沒有餵給它的。
(2) 兩模式對比 —— FCNv2 水氣路徑弱很多 → 學到的動力不是架構的必然。
(3) 「模態萃取 vs 觀測演化」問題收尾（§2.3 / §3.7 的呼應）。
(4) 限制之一：day-1 緯向條紋 = manifold shock（流形衝擊）—— 依你的指示，不歸因於物理重力波調整
    （只提出來排除），主論述是 out-of-distribution 輸入離開訓練資料流形 𝓜，Taylor 餘項由網路
    曲率主導而非流體動力，第一步把狀態「投影」回流形時甩出高頻雜訊；並給出可檢驗的區辨特徵
    （單步出現、錨定於強迫幾何 vs 頻散、傳播）。
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
(Section 3.3a) — the signature of a genuine instability of the basic state
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

The first iteration of every forced experiment exhibits globe-spanning,
zonally banded striations in the perturbation fields. It is tempting to read these as
inertia–gravity-wave adjustment to an unbalanced heating — the physical
response a primitive-equation model would produce — and we considered that
reading; but we set it aside, because the phenomenology does not support it.
Physical adjustment is dispersive: it propagates away from the forcing at
identifiable group speeds over a finite adjustment time. The striations
instead appear fully formed within a single operator application, anchored to
the geometry of the forcing, and do not propagate.

The explanation we advance is statistical rather than physical. The trained
operator is reliable only on (a neighborhood of) the manifold
$\mathcal{M}$ of atmospheric states it was fitted to; the forced input
$u_0 + \delta + f$ — a climatological mean plus an idealized heating that no
reanalysis state resembles — lies off that manifold. Off-manifold, the
Taylor expansion of Section 2.2 is dominated not by dynamics but by
unconstrained network curvature: the remainder
$\tfrac12\,\delta^\top\mathbf{H}\,\delta + \cdots$ reflects how the network
happens to extrapolate, which no training signal disciplined. The first
application of $M$ then acts, in effect, as a projection of the state back
toward $\mathcal{M}$, shedding the off-manifold component of the input as
structured, high-frequency residue — zonally banded because the forcing
itself is zonally elongated. We term this transient the *manifold shock*.
The two readings are distinguishable in principle, and the distinguishing
signatures favor the latter: single-step appearance versus dispersive
timescale; anchoring to the forcing geometry versus propagation away from
it. A quantitative version of this test — sweeping the perturbation
amplitude and measuring the departure from linear scaling as a direct probe
of manifold curvature — is the subject of companion work on the geometry of
DLWP state manifolds, and is where we continue the program sketched in the
Introduction.

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
suppression under moisture denial — at amplitudes matching the reference
experiment, and with a structural counterpart in the November 2024
quadruple-typhoon event. Equally important are the interpretive boundaries
we have drawn: the iteration extracts a nonlinear singular vector rather
than simulating weather; its comparison with observed evolution is licensed
only by background quasi-stationarity and made at the level of converged
structure; and part of the model's response to out-of-distribution forcing
is the geometry of its training manifold rather than atmospheric dynamics.
Within those boundaries, the verdict of the experiment is clear: the
dynamics of ITCZ breakdown is in the machine.
