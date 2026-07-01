"""Forcing generation for the ITCZ-breakdown experiments.

Builds the per-step forcing increment ``f`` (a :class:`~layout.State`) that the
driver adds to the assembled state each step:

* :func:`heating_forcing`   -- diabatic heating into the temperature field (Step 1/2).
* :func:`moisture_forcing`  -- specific-humidity source into the moisture field (Step 4).

Physical-assumption note (also in the run README and driver):
    The discrete thermal/moisture pulse added each 6-h step (e.g. +2.5 K for a
    10 K/day rate) approximates the *continuous* diabatic heating / moistening rate
    over that step -- the modeling premise of the finite-time perturbation method.

Horizontal structure -- the heating ellipse (the dashed contour of Guinn &
Schubert / the reference PDF) is specified by its *geographic extent*:

    center (center_lat, center_lon) and half-widths (lat_halfwidth, lon_halfwidth)

so the dashed boundary passes through, e.g., center_lon +/- lon_halfwidth.  With the
PDF defaults that is 165W center reaching 120E on the west and 90W on the east.
The Gaussian sigmas are derived as ``halfwidth / edge_sigmas`` so the boundary
ellipse sits at ``edge_sigmas`` standard deviations.
"""
from __future__ import annotations

import numpy as np

from ..models.layout import Layout, State

# 0.25-degree global grid shared by both models.
LAT = np.linspace(90.0, -90.0, 721)
LON = np.linspace(0.0, 360.0, 1440, endpoint=False)


def sigmas(fcfg: dict) -> tuple[float, float]:
    """(sigma_lat, sigma_lon) in degrees derived from the ellipse extent."""
    edge = fcfg.get("edge_sigmas", 2.0)
    return fcfg["lat_halfwidth"] / edge, fcfg["lon_halfwidth"] / edge


def _dlon(lon, lon0):
    """Signed longitude difference, wrapping across the date line, in degrees."""
    return ((lon - lon0 + 180.0) % 360.0) - 180.0


def horizontal_ellipse(center_lat, center_lon, sigma_lat, sigma_lon):
    """Unit-amplitude Gaussian ellipse on the model grid, shape (721, 1440)."""
    dlat = (LAT - center_lat)[:, None]
    dlon = _dlon(LON, center_lon)[None, :]
    return np.exp(-0.5 * (dlat / sigma_lat) ** 2 - 0.5 * (dlon / sigma_lon) ** 2)


def ellipse_boundary(fcfg: dict, n: int = 361):
    """Parametric (lon, lat) of the dashed boundary ellipse through the extent.

    Returns lon in [0, 360).  This is the contour at ``edge_sigmas`` sigma, i.e.
    it passes through center +/- (lon_halfwidth, lat_halfwidth).
    """
    th = np.linspace(0.0, 2.0 * np.pi, n)
    lon = (fcfg["center_lon"] + fcfg["lon_halfwidth"] * np.cos(th)) % 360.0
    lat = fcfg["center_lat"] + fcfg["lat_halfwidth"] * np.sin(th)
    return lon, lat


def vertical_profile(heat_type: str, levels_hpa: np.ndarray) -> np.ndarray:
    """Normalized vertical heating shape V(p), nonzero only 200-1000 hPa, in the
    same level order as ``levels_hpa`` (model-native)."""
    p = np.asarray(levels_hpa, dtype=float)
    v = np.zeros_like(p)
    mask = (p >= 200) & (p <= 1000)
    pn = (p[mask] - 200.0) / 800.0
    if heat_type == "Deep":
        v[mask] = np.sin(np.pi * pn)
    elif heat_type == "Stratiform":
        v[mask] = np.sin(2.0 * np.pi * pn)
    elif heat_type == "Shallow":
        v[mask] = (np.sin(np.pi * pn) - np.sin(2.0 * np.pi * pn)) / np.sqrt(2.0)
    elif heat_type == "uniform":
        # constant over 1000-200 hPa (incl. low levels) -> drives low-level
        # moisture convergence; investigation raised TCWV ~30 -> ~45 with DJF ICs.
        v[mask] = 1.0
    else:
        raise ValueError(f"unknown heat_type {heat_type!r}")
    return v


def _unit_field(layout: Layout, fcfg: dict) -> np.ndarray:
    """3-D unit forcing field V(p) (x) H(lat,lon), shape (nlev, 721, 1440)."""
    slat, slon = sigmas(fcfg)
    v = vertical_profile(fcfg["heat_type"], layout.levels)
    h = horizontal_ellipse(fcfg["center_lat"], fcfg["center_lon"], slat, slon)
    return (v[:, None, None] * h[None, :, :]).astype(np.float32)


def zero_state(layout: Layout) -> State:
    """An all-zero state in the model's native layout (grid size from LAT/LON)."""
    ny, nx, nz = len(LAT), len(LON), len(layout.levels)
    if layout.model == "pangu":
        arrays = {"surface": np.zeros((4, ny, nx), np.float32),
                  "upper": np.zeros((5, nz, ny, nx), np.float32)}
    else:
        arrays = {"state": np.zeros((73, ny, nx), np.float32)}
    return State(arrays, layout.model)


def heating_forcing(layout: Layout, cfg: dict) -> State:
    """Per-step diabatic-heating forcing f (temperature only).

    Per-step amplitude = rate(K/day) * step_hours/24  (e.g. 10 K/day -> +2.5 K / 6 h).
    """
    fcfg = cfg["forcing"]
    amp_per_step = fcfg["amp_K_per_day"] * cfg["step_hours"] / 24.0
    f = zero_state(layout)
    layout.add_temperature(f, amp_per_step * _unit_field(layout, fcfg))
    return f


def moisture_forcing(layout: Layout, u0: State, cfg: dict) -> State:
    """Per-step moisture forcing f (specific-humidity source), Step 4.

    Amplitude is a specific-humidity rate (kg/kg per day); ``layout.add_moisture``
    converts it to each model's moisture variables using the background ``u0``.
    """
    fcfg = cfg["forcing"]
    amp_per_step = fcfg["moist_amp_qday"] * cfg["step_hours"] / 24.0
    f = zero_state(layout)
    layout.add_moisture(f, amp_per_step * _unit_field(layout, fcfg), bg=u0)
    return f
