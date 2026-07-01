# Data-integrity note: JJA climatology source files

During the first full-pipeline run, JJA preparation aborted on a **corrupt ERA5
source file**. A scan of all 1260 JJA files (1991–2020, months 6/7/8, 14 variables)
found exactly one bad file:

| file | issue |
|------|-------|
| `data/ERA5_monthly_global/upper/relative_humidity/2014/ERA5_monthly_upper_r_2014_08.nc` | **truncated**: 23.1 MB vs ~493 MB median; raises `NetCDF: HDF error (-101)` even when opened standalone |

This is a pre-existing problem with the source data file (not caused by this code or
by parallel reads — it fails to open single-threaded too). All other 1259 files are
healthy (sizes consistent with their per-variable medians; all open successfully).

## Handling

`itcz.data.prep._avg_one` now **skips unreadable/missing months** (logging each) and
only errors if a variable has *zero* readable files. Effect here:

* The JJA **relative-humidity** climatology averages **89 of 90** months (missing
  Aug-2014). This is negligible for a 30-year mean.
* `r` is used **only by FCNv2**; **Pangu is unaffected** (it carries specific
  humidity `q`, whose 90 files are all healthy).

No other variable or month is affected. If the source file is later re-downloaded,
nothing else needs to change — the month will simply be included again.
