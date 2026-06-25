"""Build the paper base state: 0000 UTC 1979-2019 DJF ERA5 time average.

Reproduces the initial condition of Hakim & Masanam (2024), "Dynamical Tests of a
Deep Learning Weather Prediction Model" (their x-bar = the 0000 UTC 1979-2019 DJF
ERA5 time mean).

Differences from the existing ``DJF`` IC (diurnal mean, 1991-2020):
  * **0000 UTC only** (valid_time index 0 of each monthly-by-hour file),
  * **1979-2019** (calendar-year D/J/F months; 41 years),
  * **day-weighted** month average (true per-00Z-timestep time mean).

1980-2019 monthly files come from the shared ERA5_monthly_global archive; the
missing **1979** Dec/Jan/Feb are downloaded (00:00 only) into the PROJECT folder
``data_raw/`` (the shared data dir is never modified). Output ICs:
``ic/u0_paperDJF_{pangu,fcnv2}.npz``.

    python scripts/prep_paper_djf.py [--no_download]
"""
import argparse
import calendar
import os
from concurrent.futures import ProcessPoolExecutor

import _bootstrap  # noqa: F401
import numpy as np
import xarray as xr

from itcz import config as cfgmod
from itcz.data import prep

BG = "paperDJF"
YEARS = range(1979, 2020)          # 1979..2019 inclusive (calendar D/J/F)
MONTHS = (12, 1, 2)
RAW = os.path.join(cfgmod.PROJECT_ROOT, "data_raw")   # 1979 downloads (in-project)

# CDS names (match the shared archive's download script)
UPPER_CDS = {"z": "geopotential", "q": "specific_humidity", "r": "relative_humidity",
             "t": "temperature", "u": "u_component_of_wind", "v": "v_component_of_wind"}
SURFACE_CDS = {"u10": "10m_u_component_of_wind", "v10": "10m_v_component_of_wind",
               "t2m": "2m_temperature", "msl": "mean_sea_level_pressure",
               "sp": "surface_pressure", "u100": "100m_u_component_of_wind",
               "v100": "100m_v_component_of_wind", "tcwv": "total_column_water_vapour"}
LEVELS = ["1000", "925", "850", "700", "600", "500", "400",
          "300", "250", "200", "150", "100", "50"]


def _raw_combined(kind, month):
    """One combined (all-vars) 00Z file per kind per 1979 month, in the project."""
    return os.path.join(RAW, f"{kind}_1979_{month:02d}.nc")


def download_1979():
    """Download the 1979 D/J/F 0000 UTC fields (combined per kind/month) into RAW."""
    import cdsapi
    os.makedirs(RAW, exist_ok=True)
    c = cdsapi.Client()
    for m in MONTHS:
        # upper
        p = _raw_combined("upper", m)
        if not (os.path.exists(p) and os.path.getsize(p) > 1024):
            print(f"[paperDJF] download upper 1979-{m:02d} 00Z -> {p}")
            c.retrieve("reanalysis-era5-pressure-levels-monthly-means", {
                "product_type": ["monthly_averaged_reanalysis_by_hour_of_day"],
                "data_format": "netcdf", "download_format": "unarchived",
                "variable": list(UPPER_CDS.values()), "pressure_level": LEVELS,
                "year": ["1979"], "month": [f"{m:02d}"], "time": ["00:00"],
            }, p)
        # surface
        p = _raw_combined("surface", m)
        if not (os.path.exists(p) and os.path.getsize(p) > 1024):
            print(f"[paperDJF] download surface 1979-{m:02d} 00Z -> {p}")
            c.retrieve("reanalysis-era5-single-levels-monthly-means", {
                "product_type": ["monthly_averaged_reanalysis_by_hour_of_day"],
                "data_format": "netcdf", "download_format": "unarchived",
                "variable": list(SURFACE_CDS.values()),
                "year": ["1979"], "month": [f"{m:02d}"], "time": ["00:00"],
            }, p)
    print("[paperDJF] 1979 download complete")


def _path(kind, var, year, month, data_base):
    """1979 -> combined file in RAW; else the per-variable shared archive file."""
    if year == 1979:
        return _raw_combined(kind, month)
    return prep._monthly_path(data_base, kind, var, year, month)


def _avg_one(args):
    """Day-weighted 00Z mean of one (kind, var) over all DJF 1979-2019 months."""
    kind, var, data_base = args
    acc, wsum, n = None, 0.0, 0
    for y in YEARS:
        for m in MONTHS:
            p = _path(kind, var, y, m, data_base)
            if not os.path.exists(p):
                continue
            with xr.open_dataset(p) as ds:                  # 00Z = valid_time index 0
                f = np.asarray(ds[var].isel(valid_time=0).values, dtype=np.float64)
            w = calendar.monthrange(y, m)[1]                # days in month -> weight
            acc = w * f if acc is None else acc + w * f
            wsum += w
            n += 1
    if n == 0:
        raise FileNotFoundError(f"no files for {kind}/{var}")
    return kind, var, (acc / wsum).astype(np.float32), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no_download", action="store_true")
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args()
    cfg = cfgmod.load_config()
    data_base = cfg["paths"]["era5_monthly_dir"]

    if not args.no_download:
        download_1979()

    tasks = [("upper", v, data_base) for v in prep.UPPER_VARS] + \
            [("surface", v, data_base) for v in prep.SURFACE_VARS]
    print(f"[paperDJF] averaging {len(tasks)} vars, 00Z DJF {YEARS.start}-{YEARS.stop-1}, "
          f"day-weighted, {args.workers} workers")
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(_avg_one, tasks))

    fields = {"upper": {}, "surface": {}}
    for kind, var, arr, n in results:
        fields[kind][var] = arr
        print(f"[paperDJF]   {kind}/{var}: {n} month-fields")

    prep.save_ic(cfg, fields, BG)
    prep.summarize_ic(cfg, BG, "pangu")
    prep.summarize_ic(cfg, BG, "fcnv2")
    print(f"[paperDJF] done -> ic/u0_{BG}_{{pangu,fcnv2}}.npz")


if __name__ == "__main__":
    main()
