"""Shared ERA5 -> model-IC machinery for building background states u0.

Reads existing local ERA5 netCDF (no downloads, no writes outside the project),
averages the requested season/day, and packs the fields into each model's native
layout, saved as compressed npz under ``ic/``.

Grid already matches both models (0.25 deg, 721x1440, lat 90->-90, lon 0->359.75);
the monthly/daily pressure axis is 1000->50 hPa = Pangu order, FCNv2 needs 50->1000
so its level axis is flipped on pack.
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import xarray as xr

from .. import config as cfgmod

UPPER_FOLDERS = {
    "z": "geopotential", "q": "specific_humidity", "r": "relative_humidity",
    "t": "temperature", "u": "u_component_of_wind", "v": "v_component_of_wind",
}
SURFACE_FOLDERS = {
    "msl": "mean_sea_level_pressure", "u10": "10m_u_component_of_wind",
    "v10": "10m_v_component_of_wind", "t2m": "2m_temperature",
    "sp": "surface_pressure", "tcwv": "total_column_water_vapour",
    "u100": "100m_u_component_of_wind", "v100": "100m_v_component_of_wind",
}
UPPER_VARS = list(UPPER_FOLDERS)
SURFACE_VARS = list(SURFACE_FOLDERS)


def _monthly_path(base, kind, var, year, month):
    folder = (UPPER_FOLDERS if kind == "upper" else SURFACE_FOLDERS)[var]
    return os.path.join(base, kind, folder, str(year),
                        f"ERA5_monthly_{kind}_{var}_{year}_{month:02d}.nc")


def _daily_path(base, kind, var, year, month, day):
    folder = (UPPER_FOLDERS if kind == "upper" else SURFACE_FOLDERS)[var]
    return os.path.join(base, kind, folder, str(year),
                        f"ERA5_{kind}_{var}_{year}_{month:02d}_{day:02d}.nc")


def _field_from_file(path, var, hour_index=None):
    """(level,lat,lon) or (lat,lon); diurnal mean unless hour_index selects a time."""
    with xr.open_dataset(path) as ds:
        da = ds[var]
        da = da.isel(valid_time=hour_index) if hour_index is not None else da.mean("valid_time")
        return np.asarray(da.values, dtype=np.float32)


def _avg_one(args):
    """Worker: mean of one (kind, var) over the (year, month) pairs. Picklable.

    Robust to missing/corrupt source files: such months are skipped (and reported)
    rather than aborting the whole climatology -- one bad month out of dozens is
    negligible for a multi-decadal mean.
    """
    base, kind, var, pairs = args
    acc, n, skipped = None, 0, []
    for y, m in pairs:
        p = _monthly_path(base, kind, var, y, m)
        if not os.path.exists(p):
            skipped.append((kind, var, y, m, "missing"))
            continue
        try:
            f = _field_from_file(p, var)
        except Exception as e:                       # corrupt/unreadable NetCDF
            skipped.append((kind, var, y, m, f"read_error:{type(e).__name__}"))
            continue
        acc = f if acc is None else acc + f
        n += 1
    if n == 0:
        raise FileNotFoundError(f"no readable monthly files for {kind}/{var}")
    return kind, var, (acc / n).astype(np.float32), n, skipped


def season_fields_pairs(cfg, pairs, n_workers=None):
    """Average each variable over an explicit list of ``(year, month)`` pairs.

    Parallelized across the 14 (kind, var) tasks with a process pool.  ``n_workers``
    defaults to ``cpu_num`` (resolving -1 to all cores), capped at the task count.
    """
    base = cfg["paths"]["era5_monthly_dir"]
    tasks = [(base, "upper", v, pairs) for v in UPPER_VARS] + \
            [(base, "surface", v, pairs) for v in SURFACE_VARS]
    if n_workers is None:
        n = cfg.get("cpu_num", 0)
        n_workers = os.cpu_count() if not n or n < 0 else int(n)
    n_workers = max(1, min(n_workers, len(tasks)))

    out = {"upper": {}, "surface": {}}
    print(f"[prep] averaging {len(tasks)} variables over {len(pairs)} months "
          f"with {n_workers} workers")
    if n_workers == 1:
        results = [_avg_one(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            results = list(ex.map(_avg_one, tasks))
    all_skipped = []
    for kind, var, arr, n, skipped in results:
        out[kind][var] = arr
        all_skipped += skipped
        flag = f"  (skipped {len(skipped)})" if skipped else ""
        print(f"[prep]   {kind}/{var}: averaged {n} monthly files{flag}")
    if all_skipped:
        print(f"[prep] WARNING: skipped {len(all_skipped)} unreadable/missing months:")
        for kind, var, y, m, why in all_skipped:
            print(f"[prep]   - {kind}/{var} {y}-{m:02d}: {why}")
    out["_skipped"] = all_skipped
    return out


def season_fields(cfg, years, months, n_workers=None):
    return season_fields_pairs(cfg, [(y, m) for y in years for m in months], n_workers)


def djf_pairs(years):
    """DJF labelled YR uses Dec(YR-1), Jan(YR), Feb(YR)."""
    pairs = []
    for yr in years:
        pairs += [(yr - 1, 12), (yr, 1), (yr, 2)]
    return pairs


def day_fields(cfg, year, month, day, hour=0):
    base = cfg["paths"]["era5_daily_dir"]
    out = {"upper": {}, "surface": {}}
    for kind, varlist in (("upper", UPPER_VARS), ("surface", SURFACE_VARS)):
        for var in varlist:
            p = _daily_path(base, kind, var, year, month, day)
            if not os.path.exists(p):
                raise FileNotFoundError(p)
            out[kind][var] = _field_from_file(p, var, hour_index=hour)
            print(f"[prep]   {kind}/{var}: {os.path.basename(p)} @ {hour:02d}Z")
    return out


def _pack_pangu(fields):
    u, s = fields["upper"], fields["surface"]
    upper = np.stack([u["z"], u["q"], u["t"], u["u"], u["v"]], axis=0).astype(np.float32)
    surface = np.stack([s["msl"], s["u10"], s["v10"], s["t2m"]], axis=0).astype(np.float32)
    return {"surface": surface, "upper": upper}


def _pack_fcnv2(fields):
    u, s = fields["upper"], fields["surface"]
    flip = lambda a: a[::-1]  # 1000..50 -> 50..1000 (FCNv2 order)
    blocks = [
        s["u10"][None], s["v10"][None], s["u100"][None], s["v100"][None],
        s["t2m"][None], s["sp"][None], s["msl"][None], s["tcwv"][None],
        flip(u["u"]), flip(u["v"]), flip(u["z"]), flip(u["t"]), flip(u["r"]),
    ]
    state = np.concatenate(blocks, axis=0).astype(np.float32)
    assert state.shape == (73, 721, 1440), state.shape
    return {"state": state}


def save_ic(cfg, fields, background_name):
    """Pack ``fields`` for both models and write ``ic/u0_{bg}_{model}.npz``."""
    os.makedirs(cfg["paths"]["ic_dir"], exist_ok=True)
    written = []
    for model, packer in (("pangu", _pack_pangu), ("fcnv2", _pack_fcnv2)):
        path = cfgmod.ic_path(cfg, background_name, model)
        np.savez_compressed(path, **packer(fields))
        written.append(path)
        print(f"[prep] wrote {path}")
    return written


def summarize_ic(cfg, background_name, model="pangu"):
    """Print sanity ranges of a packed IC (units / level order / magnitudes)."""
    from ..models import layout as L
    st = L.State.from_npz(cfgmod.ic_path(cfg, background_name, model), model)
    lay = L.get_layout(model)
    print(f"\n[prep] sanity {background_name}/{model}:")
    for k, a in st.arrays.items():
        print(f"  {k}: shape={a.shape} min={a.min():.3g} max={a.max():.3g} mean={a.mean():.3g}")
    t850 = lay.temperature_at(st, 850)
    u850, v850 = lay.get_uv(st, 850)
    print(f"  T850 [K] {t850.min():.1f}..{t850.max():.1f}; "
          f"|wind850| max {np.hypot(u850, v850).max():.1f} m/s; "
          f"TCWV [kg/m2] {lay.tcwv(st).min():.1f}..{lay.tcwv(st).max():.1f}")
