"""Unit tests for the driver math (Perpetual Background Re-centering) and the
locking primitives -- run WITHOUT loading any real model.

    python tests/test_driver_math.py        # plain asserts, exits non-zero on failure

Uses a tiny synthetic grid (monkeypatching forcing.LAT/LON) and a mock linear
operator with known behaviour, so the recurrence and channel zeroing are checked
exactly.
"""
import os
import sys
import tempfile

import numpy as np

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, _SRC)

from itcz.experiment import forcing  # noqa: E402

# --- shrink the grid for fast exact arithmetic ------------------------------
NY, NX = 6, 8
forcing.LAT = np.linspace(20.0, -20.0, NY)
forcing.LON = np.linspace(150.0, 210.0, NX)

from itcz import config as cfgmod                     # noqa: E402
from itcz.experiment import driver                    # noqa: E402
from itcz.models.layout import State, get_layout      # noqa: E402
from itcz.models.operators import Operator            # noqa: E402

LAY = get_layout("pangu")
NZ = len(LAY.levels)


def _rand_u0():
    rng = np.random.default_rng(0)
    upper = rng.random((5, NZ, NY, NX), dtype=np.float32)
    upper[LAY.Q] += 0.01
    surface = rng.random((4, NY, NX), dtype=np.float32)
    return State({"surface": surface, "upper": upper}, "pangu")


class ScaleOp(Operator):
    """M(x) = alpha * x  (so B1 = alpha*u0)."""
    model = "pangu"

    def __init__(self, alpha):
        super().__init__()
        self.alpha = alpha

    def step(self, state):
        return state * self.alpha


class CoupleOp(Operator):
    """M(x) = x with out.q = x.q + k*x.t (generates a moisture perturbation)."""
    model = "pangu"

    def __init__(self, k=0.1):
        super().__init__()
        self.k = k

    def step(self, state):
        out = state.copy()
        out.arrays["upper"][LAY.Q] = state.arrays["upper"][LAY.Q] + self.k * state.arrays["upper"][LAY.T]
        return out


def _base_cfg(tmp):
    return cfgmod.load_config({
        "model": "pangu", "background": "test", "step_hours": 6,
        "paths": {"ic_dir": tmp, "output_dir": tmp},
        "driver": {"n_days": 1.0, "forcing_days": 1.0, "save_every": 1},  # 4 steps
    })


def _write_u0(cfg, u0):
    os.makedirs(cfg["paths"]["ic_dir"], exist_ok=True)
    u0.save_npz(cfgmod.ic_path(cfg, "test", "pangu"))


def test_recentering_math():
    """u'_1 = alpha*f ; u'_2 = alpha*(1+alpha)*f for M=alpha*x, persistent heating."""
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _base_cfg(tmp)
        _write_u0(cfg, _rand_u0())
        alpha = 0.5
        cfg["experiment"] = {"name": "math", "forcing_type": "heating",
                             "persistent": True, "lock": "none", "seed_npz": None}
        rd = driver.run(cfg, operator=ScaleOp(alpha))
        f = forcing.heating_forcing(LAY, cfg)
        u1 = State.from_npz(os.path.join(rd, "pert_001.npz"), "pangu")
        u2 = State.from_npz(os.path.join(rd, "pert_002.npz"), "pangu")
        exp1, exp2 = f * alpha, f * (alpha * (1.0 + alpha))
        for k in ("surface", "upper"):
            assert np.allclose(u1.arrays[k], exp1.arrays[k], atol=1e-6), f"u1 {k}"
            assert np.allclose(u2.arrays[k], exp2.arrays[k], atol=1e-6), f"u2 {k}"
        u0p = State.from_npz(os.path.join(rd, "pert_000.npz"), "pangu")
        assert np.all(u0p.arrays["upper"] == 0) and np.all(u0p.arrays["surface"] == 0)
    print("OK test_recentering_math")


def test_moisture_lock():
    """Moisture perturbation nonzero unlocked, exactly zero when locked."""
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _base_cfg(tmp)
        _write_u0(cfg, _rand_u0())
        cfg["experiment"] = {"name": "nolock", "forcing_type": "heating",
                             "persistent": True, "lock": "none", "seed_npz": None}
        rd = driver.run(cfg, operator=CoupleOp())
        q1 = State.from_npz(os.path.join(rd, "pert_001.npz"), "pangu").arrays["upper"][LAY.Q]
        assert np.any(np.abs(q1) > 1e-6), "expected nonzero moisture perturbation unlocked"

        cfg["experiment"] = {"name": "lock", "forcing_type": "heating",
                             "persistent": True, "lock": "moisture", "seed_npz": None}
        rd = driver.run(cfg, operator=CoupleOp())
        for s in (1, 2, 3, 4):
            q = State.from_npz(os.path.join(rd, f"pert_{s:03d}.npz"), "pangu").arrays["upper"][LAY.Q]
            assert np.all(q == 0.0), f"moisture not locked at step {s}"
    print("OK test_moisture_lock")


def test_wind_lock_and_primitives():
    st = _rand_u0()
    LAY.zero_wind_perturbation(st)
    assert np.all(st.arrays["upper"][LAY.U] == 0) and np.all(st.arrays["upper"][LAY.V] == 0)
    assert np.all(st.arrays["surface"][LAY.U10] == 0) and np.all(st.arrays["surface"][LAY.V10] == 0)
    st2 = _rand_u0()
    mo = LAY.extract_moisture_only(st2)
    assert np.allclose(mo.arrays["upper"][LAY.Q], st2.arrays["upper"][LAY.Q])
    assert np.all(mo.arrays["upper"][LAY.Z] == 0)
    assert np.allclose(LAY.tcwv(st2 * 2.0), 2.0 * LAY.tcwv(st2), rtol=1e-5)
    print("OK test_wind_lock_and_primitives")


def test_clip_moisture():
    st = _rand_u0()
    st.arrays["upper"][LAY.Q, 0, 0, 0] = -5.0
    t_before = st.arrays["upper"][LAY.T].copy()
    LAY.clip_moisture(st)
    assert st.arrays["upper"][LAY.Q].min() >= 0.0
    assert np.array_equal(st.arrays["upper"][LAY.T], t_before)
    print("OK test_clip_moisture")


if __name__ == "__main__":
    test_recentering_math()
    test_moisture_lock()
    test_wind_lock_and_primitives()
    test_clip_moisture()
    print("\nALL TESTS PASSED")
