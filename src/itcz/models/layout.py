"""Channel layout, the model-agnostic ``State`` container, and all variable-group
operations needed by the driver / forcing / diagnostics.

The two supported models store their fields completely differently:

* **Pangu**  : two arrays -- ``surface`` (4, 721, 1440) = [msl, u10, v10, t2m] and
  ``upper`` (5, 13, 721, 1440) = [z, q, t, u, v]; pressure levels **1000 -> 50**.
  Has **no** TCWV channel (TCWV is diagnosed by integrating q).
* **FCNv2** : one array (73, 721, 1440); surface[0:8] =
  [10u, 10v, 100u, 100v, 2t, sp, msl, tcwv]; upper blocks u(8:21) v(21:34) z(34:47)
  t(47:60) r(60:73); pressure levels **50 -> 1000**.

Everything that needs to know an index lives here; the driver/forcing never hard-code
channel numbers.  ``get_layout(model)`` returns the right :class:`Layout`.
"""
from __future__ import annotations

import numpy as np

G = 9.80665  # m s^-2, for column water-vapour integration

# Canonical pressure levels in each model's *native* axis order (hPa).
PANGU_LEVELS = np.array([1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50])
FCNV2_LEVELS = np.array([50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000])


# ---------------------------------------------------------------------------
# Model-agnostic state container
# ---------------------------------------------------------------------------
class State:
    """A bundle of named float32 arrays supporting elementwise arithmetic.

    Pangu states hold keys ``{"surface", "upper"}``; FCNv2 states hold ``{"state"}``.
    The driver performs ``u0 + u' + f`` and ``raw - B1`` purely through these ops,
    so it is agnostic to how each model packs its channels.
    """

    __slots__ = ("arrays", "model")

    def __init__(self, arrays: dict[str, np.ndarray], model: str):
        self.arrays = {k: np.asarray(v, dtype=np.float32) for k, v in arrays.items()}
        self.model = model

    def copy(self) -> "State":
        return State({k: v.copy() for k, v in self.arrays.items()}, self.model)

    def zeros_like(self) -> "State":
        return State({k: np.zeros_like(v) for k, v in self.arrays.items()}, self.model)

    @classmethod
    def from_npz(cls, path: str, model: str) -> "State":
        with np.load(path) as d:
            return cls({k: d[k] for k in d.files}, model)

    def save_npz(self, path: str) -> None:
        np.savez_compressed(path, **self.arrays)

    def _binary(self, other, op) -> "State":
        if isinstance(other, State):
            return State({k: op(self.arrays[k], other.arrays[k]) for k in self.arrays}, self.model)
        return State({k: op(v, other) for k, v in self.arrays.items()}, self.model)

    def __add__(self, other):
        return self._binary(other, np.add)

    def __sub__(self, other):
        return self._binary(other, np.subtract)

    def __mul__(self, other):
        return self._binary(other, np.multiply)

    __rmul__ = __mul__


# ---------------------------------------------------------------------------
# Per-model layouts
# ---------------------------------------------------------------------------
class Layout:
    """Base interface; subclasses know the channel packing of one model."""

    model: str
    levels: np.ndarray

    def level_index(self, p_hpa: int) -> int:
        return int(np.where(self.levels == p_hpa)[0][0])

    # implemented per model
    def add_temperature(self, state: State, field3d: np.ndarray) -> None: ...
    def add_moisture(self, state: State, q3d: np.ndarray, bg: State) -> None: ...
    def zero_moisture_perturbation(self, state: State) -> None: ...
    def zero_wind_perturbation(self, state: State) -> None: ...
    def clip_moisture(self, state: State) -> None: ...
    def extract_moisture_only(self, state: State) -> State: ...
    def get_uv(self, state: State, p_hpa: int) -> tuple[np.ndarray, np.ndarray]: ...
    def tcwv(self, state: State) -> np.ndarray: ...
    def temperature_at(self, state: State, p_hpa: int) -> np.ndarray: ...

    @staticmethod
    def _column_tcwv(q3d: np.ndarray, levels_hpa: np.ndarray) -> np.ndarray:
        """TCWV = (1/g) integral q dp  [kg m^-2]; linear in q (works for q')."""
        p = levels_hpa.astype(np.float64) * 100.0  # Pa
        order = np.argsort(p)
        integral = np.trapz(q3d[order].astype(np.float64), p[order], axis=0)
        return (integral / G).astype(np.float32)

    @staticmethod
    def _q_to_dr(q3d: np.ndarray, t3d: np.ndarray, levels_hpa: np.ndarray) -> np.ndarray:
        """Specific-humidity increment (kg/kg) -> relative-humidity increment (%)
        using background temperature: dr = 100*de/es(T), de ~= dq*p/0.622."""
        p = (levels_hpa.astype(np.float64) * 100.0)[:, None, None]
        tc = t3d.astype(np.float64) - 273.15
        es = 611.2 * np.exp(17.67 * tc / (tc + 243.5))  # Pa over water
        de = q3d.astype(np.float64) * p / 0.622
        return (100.0 * de / es).astype(np.float32)


class PanguLayout(Layout):
    model = "pangu"
    levels = PANGU_LEVELS
    MSL, U10, V10, T2M = 0, 1, 2, 3          # surface indices
    Z, Q, T, U, V = 0, 1, 2, 3, 4            # upper variable indices

    def add_temperature(self, state, field3d):
        state.arrays["upper"][self.T] += field3d.astype(np.float32)

    def add_moisture(self, state, q3d, bg):
        state.arrays["upper"][self.Q] += q3d.astype(np.float32)

    def zero_moisture_perturbation(self, state):
        state.arrays["upper"][self.Q] = 0.0

    def zero_wind_perturbation(self, state):
        state.arrays["upper"][self.U] = 0.0
        state.arrays["upper"][self.V] = 0.0
        state.arrays["surface"][self.U10] = 0.0
        state.arrays["surface"][self.V10] = 0.0

    def clip_moisture(self, state):
        q = state.arrays["upper"][self.Q]
        np.clip(q, 0.0, None, out=q)

    def extract_moisture_only(self, state):
        out = state.zeros_like()
        out.arrays["upper"][self.Q] = state.arrays["upper"][self.Q]
        return out

    def get_uv(self, state, p_hpa):
        k = self.level_index(p_hpa)
        return state.arrays["upper"][self.U, k], state.arrays["upper"][self.V, k]

    def temperature_at(self, state, p_hpa):
        return state.arrays["upper"][self.T, self.level_index(p_hpa)]

    def tcwv(self, state):
        return self._column_tcwv(state.arrays["upper"][self.Q], self.levels)


class FCNv2Layout(Layout):
    model = "fcnv2"
    levels = FCNV2_LEVELS
    U10, V10, U100, V100, T2M, SP, MSL, TCWV = range(8)   # surface channels
    U0, V0, Z0, T0, R0 = 8, 21, 34, 47, 60                # upper block starts

    def add_temperature(self, state, field3d):
        state.arrays["state"][self.T0:self.T0 + 13] += field3d.astype(np.float32)

    def add_moisture(self, state, q3d, bg):
        dr = self._q_to_dr(q3d, bg.arrays["state"][self.T0:self.T0 + 13], self.levels)
        state.arrays["state"][self.R0:self.R0 + 13] += dr
        state.arrays["state"][self.TCWV] += self._column_tcwv(q3d, self.levels)

    def zero_moisture_perturbation(self, state):
        state.arrays["state"][self.R0:self.R0 + 13] = 0.0
        state.arrays["state"][self.TCWV] = 0.0

    def zero_wind_perturbation(self, state):
        state.arrays["state"][self.U0:self.U0 + 13] = 0.0
        state.arrays["state"][self.V0:self.V0 + 13] = 0.0
        state.arrays["state"][[self.U10, self.V10, self.U100, self.V100]] = 0.0

    def clip_moisture(self, state):
        r = state.arrays["state"][self.R0:self.R0 + 13]
        np.clip(r, 0.0, 100.0, out=r)
        tcwv = state.arrays["state"][self.TCWV]
        np.clip(tcwv, 0.0, None, out=tcwv)

    def extract_moisture_only(self, state):
        out = state.zeros_like()
        out.arrays["state"][self.R0:self.R0 + 13] = state.arrays["state"][self.R0:self.R0 + 13]
        out.arrays["state"][self.TCWV] = state.arrays["state"][self.TCWV]
        return out

    def get_uv(self, state, p_hpa):
        k = self.level_index(p_hpa)
        s = state.arrays["state"]
        return s[self.U0 + k], s[self.V0 + k]

    def temperature_at(self, state, p_hpa):
        return state.arrays["state"][self.T0 + self.level_index(p_hpa)]

    def tcwv(self, state):
        return state.arrays["state"][self.TCWV]


_LAYOUTS = {"pangu": PanguLayout, "fcnv2": FCNv2Layout}


def get_layout(model: str) -> Layout:
    if model not in _LAYOUTS:
        raise ValueError(f"unknown model {model!r}; choose from {list(_LAYOUTS)}")
    return _LAYOUTS[model]()
