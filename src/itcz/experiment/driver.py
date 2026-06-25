"""Finite-time nonlinear perturbation driver -- *Perpetual Background Re-centering*.

Core iteration (see README).  With frozen one-step drift ``B1 = M(u0)`` and given
``u'_0``, for n = 1 .. N:

    A_n   = u0 + u'_{n-1} + f_n        # state fed to M, always anchored to steady u0
    A_n   = clip_moisture(A_n)         # enforce q>=0 / 0<=r<=100% before M
    u'_n  = M(A_n) - B1                # peel the constant one-step model drift
    u'_n  = LOCK(u'_n)                 # variant-specific channel zeroing

The four stages are expressed as an ``experiment`` config block:

    forcing_type : "heating" | "moisture" | "none"
    persistent   : bool   -- if False, forcing is off after ``forcing_days``
    lock         : "none" | "moisture" | "wind"
    seed_npz     : path to a moisture-only initial perturbation (Steps 3/4) or None
"""
from __future__ import annotations

import json
import os

from .. import config as cfgmod
from . import forcing as forcing_mod
from ..models.layout import State, get_layout
from ..models.operators import Operator, load_operator


def _build_forcing(layout, cfg, u0):
    ftype = cfg["experiment"]["forcing_type"]
    if ftype == "heating":
        return forcing_mod.heating_forcing(layout, cfg)
    if ftype == "moisture":
        return forcing_mod.moisture_forcing(layout, u0, cfg)
    if ftype == "none":
        return forcing_mod.zero_state(layout)
    raise ValueError(f"unknown forcing_type {ftype!r}")


def _apply_lock(layout, pert: State, lock: str) -> None:
    if lock == "moisture":
        layout.zero_moisture_perturbation(pert)
    elif lock == "wind":
        layout.zero_wind_perturbation(pert)
    elif lock != "none":
        raise ValueError(f"unknown lock {lock!r}")


def run(cfg: dict, operator: Operator | None = None) -> str:
    """Execute one experiment and return its output directory."""
    model = cfg["model"]
    layout = get_layout(model)
    exp = cfg["experiment"]

    u0_path = cfgmod.ic_path(cfg, cfg["background"], model)
    if not os.path.exists(u0_path):
        raise FileNotFoundError(
            f"background state not found: {u0_path}\nrun the matching prep script first.")
    u0 = State.from_npz(u0_path, model)

    op = operator or load_operator(cfg)
    f_base = _build_forcing(layout, cfg, u0)

    if exp.get("seed_npz"):
        u_prev = layout.extract_moisture_only(State.from_npz(exp["seed_npz"], model))
    else:
        u_prev = u0.zeros_like()

    N = cfgmod.n_steps(cfg)
    Nf = cfgmod.forcing_steps(cfg)
    persistent = bool(exp.get("persistent", False))
    lock = exp.get("lock", "none")
    save_every = cfg["driver"].get("save_every", 1)

    run_dir = os.path.join(cfgmod.bg_output_dir(cfg), exp["name"])
    os.makedirs(run_dir, exist_ok=True)
    _stamp(run_dir, cfg)

    print(f"[driver] {exp['name']}: model={model} background={cfg['background']} "
          f"N={N} steps ({cfg['driver']['n_days']}d), forcing<= {Nf} steps, lock={lock}")

    B1 = op.step(u0)                              # frozen one-step background drift
    u_prev.save_npz(os.path.join(run_dir, "pert_000.npz"))
    for n in range(1, N + 1):
        f_n = f_base if (persistent or n <= Nf) else f_base.zeros_like()
        A = u0 + u_prev + f_n
        layout.clip_moisture(A)                  # physical-bound safeguard before M
        u_n = op.step(A) - B1
        _apply_lock(layout, u_n, lock)
        if n % save_every == 0 or n == N:
            u_n.save_npz(os.path.join(run_dir, f"pert_{n:03d}.npz"))
        u_prev = u_n
        if n % 4 == 0:
            print(f"[driver]   day {n * cfg['step_hours'] / 24:.2f} (step {n}/{N}) done")

    print(f"[driver] finished -> {run_dir}")
    return run_dir


def make_moisture_seed(step1_run_dir: str, model: str, day: int, out_path: str,
                       step_hours: int = 6) -> str:
    """Extract the moisture-only perturbation at ``day`` from a Step-1 run
    (initializes Steps 3/4)."""
    step = int(round(day * 24 / step_hours))
    src = os.path.join(step1_run_dir, f"pert_{step:03d}.npz")
    if not os.path.exists(src):
        raise FileNotFoundError(f"{src} (need Step 1 output at day {day})")
    layout = get_layout(model)
    seed = layout.extract_moisture_only(State.from_npz(src, model))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    seed.save_npz(out_path)
    print(f"[driver] moisture seed (day {day}) -> {out_path}")
    return out_path


def _stamp(run_dir: str, cfg: dict) -> None:
    with open(os.path.join(run_dir, "config_used.json"), "w") as fh:
        json.dump(cfg, fh, indent=2, default=str)
