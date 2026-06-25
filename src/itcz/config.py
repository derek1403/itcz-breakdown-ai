"""Configuration loading and path resolution for the ITCZ-breakdown project.

Centralizes all knowledge of *where things live* so no other module hard-codes a
path. ``load_config`` reads ``config.yaml`` (at the project root), applies optional
overrides, and resolves project-relative output paths to absolute paths.
"""
from __future__ import annotations

import copy
import os

import yaml

# src/itcz/config.py  ->  project root is three levels up
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")


def _deep_update(base: dict, override: dict) -> dict:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
    return base


def load_config(overrides: dict | None = None, path: str | None = None) -> dict:
    """Load the YAML config, merge ``overrides``, and resolve write-paths."""
    with open(path or _CONFIG_PATH) as fh:
        cfg = yaml.safe_load(fh)
    if overrides:
        _deep_update(cfg, copy.deepcopy(overrides))
    for key in ("ic_dir", "output_dir"):
        p = cfg["paths"][key]
        if not os.path.isabs(p):
            cfg["paths"][key] = os.path.join(PROJECT_ROOT, p)
    return cfg


def ic_path(cfg: dict, background: str, model: str) -> str:
    """Absolute path of the prepared background-state npz for (background, model)."""
    return os.path.join(cfg["paths"]["ic_dir"], f"u0_{background}_{model}.npz")


def bg_output_dir(cfg: dict, background: str | None = None) -> str:
    """Per-background output directory: ``outputs/<background>/`` (created on demand).

    All run dirs, seeds, and initial-field figures for a background live here.
    """
    bg = background or cfg["background"]
    d = os.path.join(cfg["paths"]["output_dir"], bg)
    os.makedirs(d, exist_ok=True)
    return d


def n_steps(cfg: dict) -> int:
    """Total number of model steps for the configured integration length."""
    return int(round(cfg["driver"]["n_days"] * 24 / cfg["step_hours"]))


def forcing_steps(cfg: dict) -> int:
    """Number of leading steps for which the forcing is active."""
    return int(round(cfg["driver"]["forcing_days"] * 24 / cfg["step_hours"]))
