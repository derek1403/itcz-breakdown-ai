"""Diagnostics, vortex tracking, and plotting for ITCZ-breakdown runs.

Relative vorticity and column-vapour integration are linear in the fields, so every
diagnostic is computed directly on the saved perturbation u'_n:

    zeta'  = relative vorticity of (u', v') at 850 hPa
    TCWV'  = column water-vapour anomaly (Pangu: integral q'; FCNv2: tcwv channel)

Produces (mirroring the reference PDF): multi-panel anomaly-vorticity & TCWV maps
across snapshot days, vorticity/TCWV time series, and a forcing-ellipse overlay.

Run:  python scripts/plot_run.py <run_dir> [--model pangu]
"""
from __future__ import annotations

import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm

from ..experiment.forcing import LAT, LON, ellipse_boundary, horizontal_ellipse, sigmas
from ..models.layout import State, get_layout

A_EARTH = 6.371e6  # m


# ---------------------------------------------------------------------------
# diagnostics
# ---------------------------------------------------------------------------
def relative_vorticity(u, v, lat=LAT, lon=LON):
    """Spherical relative vorticity [s^-1] from (u, v) on the lat/lon grid."""
    phi = np.deg2rad(lat)
    lam = np.deg2rad(lon)
    cosphi = np.cos(phi)[:, None]
    cosphi = np.where(np.abs(cosphi) < 1e-6, 1e-6, cosphi)
    dv_dlam = np.gradient(v, lam, axis=1)
    ducos_dphi = np.gradient(u * cosphi, phi, axis=0)
    return (dv_dlam - ducos_dphi) / (A_EARTH * cosphi)


def vort850(state, layout):
    u, v = layout.get_uv(state, 850)
    return relative_vorticity(u, v)


def tcwv_anom(state, layout):
    return layout.tcwv(state)


def _band_mask(band):
    lat_min, lat_max, lon_min, lon_max = band
    mlat = (LAT >= lat_min) & (LAT <= lat_max)
    mlon = (LON >= lon_min) & (LON <= lon_max)
    return mlat[:, None] & mlon[None, :]


def track_max(field2d, band):
    """(value, lat, lon) of the maximum of ``field2d`` within ``band``."""
    mask = _band_mask(band)
    masked = np.where(mask, field2d, -np.inf)
    j, i = np.unravel_index(np.argmax(masked), masked.shape)
    return float(field2d[j, i]), float(LAT[j]), float(LON[i])


# ---------------------------------------------------------------------------
# run-dir loading
# ---------------------------------------------------------------------------
def list_steps(run_dir):
    files = sorted(glob.glob(os.path.join(run_dir, "pert_*.npz")))
    return [int(os.path.basename(f)[5:8]) for f in files]


def load_pert(run_dir, step, model):
    return State.from_npz(os.path.join(run_dir, f"pert_{step:03d}.npz"), model)


def step_for_day(day, step_hours):
    return int(round(day * 24 / step_hours))


# ---------------------------------------------------------------------------
# map helpers
# ---------------------------------------------------------------------------
def _make_ax(fig, pos, extent):
    import cartopy.crs as ccrs
    import cartopy.mpl.ticker as cticker
    ax = fig.add_subplot(*pos, projection=ccrs.PlateCarree(central_longitude=180))
    ax.coastlines(linewidth=0.5)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    # lat/lon tick labels (derived from the extent so any domain works)
    xt = np.arange(extent[0], extent[1] + 1, 30)
    yt = np.arange(extent[2], extent[3] + 1, 15)
    ax.set_xticks(xt, crs=ccrs.PlateCarree())
    ax.set_yticks(yt, crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(cticker.LongitudeFormatter())
    ax.yaxis.set_major_formatter(cticker.LatitudeFormatter())
    ax.tick_params(labelsize=8)
    ax.gridlines(linewidth=0.3, linestyle=":", alpha=0.5)
    return ax


def _domain_extent(pcfg):
    lon_min, lon_max, lat_min, lat_max = pcfg["domain"]
    return [lon_min, (lon_max + 360) if lon_max < 0 else lon_max, lat_min, lat_max]


def _discrete(cmap_name, clim, step, extend="both"):
    """Discrete (cmap, BoundaryNorm, levels) for a double-ended colorbar.

    Color bins every ``step`` over [-clim, clim]; ``extend='both'`` draws the two
    pointed ends for out-of-range values.
    """
    levels = np.arange(-clim, clim + step / 2.0, step)
    cmap = plt.get_cmap(cmap_name)
    norm = BoundaryNorm(levels, ncolors=cmap.N, extend=extend)
    return cmap, norm, levels


# ---------------------------------------------------------------------------
# plots
# ---------------------------------------------------------------------------
def plot_field_panels(run_dir, cfg, field="vort", out=None):
    import cartopy.crs as ccrs
    model = cfg["model"]
    layout = get_layout(model)
    pcfg = cfg["plot"]
    extent = _domain_extent(pcfg)
    days = pcfg["snapshot_days"]
    avail = set(list_steps(run_dir))
    if field == "vort":
        label, scale = r"$\zeta'\times10^{5}$ (s$^{-1}$)", 1e5
        cmap, norm, levels = _discrete("seismic", pcfg["vort_clim"], pcfg.get("vort_step", 1.0))
        ticks = levels[::2]
    else:
        label, scale = r"TCWV (kg m$^{-2}$)", 1.0
        cmap, norm, levels = _discrete("BrBG", pcfg["tcwv_clim"], pcfg.get("tcwv_step", 10.0))
        ticks = levels

    ncol = 2
    nrow = int(np.ceil(len(days) / ncol))
    fig = plt.figure(figsize=(7 * ncol, 2.6 * nrow))
    lonb, latb = ellipse_boundary(cfg["forcing"])
    for k, day in enumerate(days):
        step = step_for_day(day, cfg["step_hours"])
        ax = _make_ax(fig, (nrow, ncol, k + 1), extent)
        ax.set_title(f"{'850hPa vort' if field == 'vort' else 'TCWV'} anomaly  day {day}",
                     fontsize=9)
        ax.plot(lonb, latb, "--", color="orange", lw=1.0, transform=ccrs.PlateCarree())
        if step not in avail:
            ax.text(0.5, 0.5, f"(step {step} missing)", transform=ax.transAxes, ha="center")
            continue
        st = load_pert(run_dir, step, model)
        data = (vort850(st, layout) if field == "vort" else tcwv_anom(st, layout)) * scale
        mesh = ax.pcolormesh(LON, LAT, data, cmap=cmap, norm=norm,
                             shading="auto", transform=ccrs.PlateCarree())
        if field == "vort":
            _, vlat, vlon = track_max(vort850(st, layout), pcfg["track_band"])
            ax.plot(vlon, vlat, "kx", ms=6, transform=ccrs.PlateCarree())
        plt.colorbar(mesh, ax=ax, shrink=0.8, pad=0.02, label=label,
                     extend="both", ticks=ticks)
    fig.tight_layout()
    out = out or os.path.join(run_dir, f"panels_{field}.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[plot] {out}")
    return out


def timeseries(run_dir, cfg):
    """(days, vort_max[s^-1], tcwv_max[kg/m^2]) tracked within the band."""
    model = cfg["model"]
    layout = get_layout(model)
    band = cfg["plot"]["track_band"]
    days, vmax, tmax = [], [], []
    for s in list_steps(run_dir):
        st = load_pert(run_dir, s, model)
        days.append(s * cfg["step_hours"] / 24.0)
        vmax.append(track_max(vort850(st, layout), band)[0])
        tmax.append(track_max(tcwv_anom(st, layout), band)[0])
    return np.array(days), np.array(vmax), np.array(tmax)


def plot_timeseries(run_dirs, labels, cfg, out=None):
    fig, (axv, axt) = plt.subplots(1, 2, figsize=(12, 4.5))
    for rd, lab in zip(run_dirs, labels):
        d, vm, tm = timeseries(rd, cfg)
        axv.plot(d, vm, "-o", ms=3, label=lab)
        axt.plot(d, tm, "-o", ms=3, label=lab)
    axv.set(title="850 hPa Vorticity Anomaly Evolution", xlabel="Time (day)",
            ylabel=r"Vorticity anomaly (s$^{-1}$)")
    axt.set(title="TCWV Anomaly Evolution", xlabel="Time (day)",
            ylabel=r"TCWV anomaly (kg m$^{-2}$)")
    for ax in (axv, axt):
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    out = out or os.path.join(run_dirs[0], "timeseries.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[plot] {out}")
    return out


def plot_vorticity_frame(run_dir, cfg, step, out_dir, domain=(100, 290, 0, 45),
                         vmax=10.0, step_unit=1.0, cmap="seismic"):
    """Single-panel 850-hPa anomaly vorticity (x 1e5) for one step -> one PNG.

    domain = (lon_min, lon_max, lat_min, lat_max) in deg E (70W = 290).
    Discrete ``seismic`` colorbar, bins every ``step_unit``, double-ended (extend
    both); positive vorticity red.
    """
    import cartopy.crs as ccrs
    model = cfg["model"]
    layout = get_layout(model)
    st = load_pert(run_dir, step, model)
    z = vort850(st, layout) * 1e5  # 1e-5 s^-1
    day = step * cfg["step_hours"] / 24.0
    cmap_obj, norm, levels = _discrete(cmap, vmax, step_unit)

    fig = plt.figure(figsize=(9.5, 3.4))
    ax = _make_ax(fig, (1, 1, 1), list(domain))
    mesh = ax.pcolormesh(LON, LAT, z, cmap=cmap_obj, norm=norm,
                         shading="auto", transform=ccrs.PlateCarree())
    ax.set_title(f"{model}  850 hPa $\\zeta'$  day {day:.2f} (step {step})", fontsize=10)
    plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02, extend="both", ticks=levels[::2],
                 label=r"$\zeta'\times10^{5}$ (s$^{-1}$)")
    fig.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"vort_d{day:05.2f}_s{step:03d}.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def plot_vorticity_frames(run_dir, cfg, steps=None, out_dir=None, **kw):
    """Write one vorticity frame per step into ``<run_dir>/vort_frames/``.

    ``steps=None`` -> all saved steps in the run.  Returns the list of PNG paths.
    """
    out_dir = out_dir or os.path.join(run_dir, "vort_frames")
    steps = list_steps(run_dir) if steps is None else steps
    paths = []
    for s in steps:
        p = plot_vorticity_frame(run_dir, cfg, s, out_dir, **kw)
        paths.append(p)
        print(f"[plot] {p}")
    return paths


def plot_background_fields(cfg, out_dir=None, vort_clim=None, tcwv_max=70.0):
    """Plot the *initial background* (u0) 850-hPa relative vorticity and TCWV.

    These are the absolute fields of the climatology/IC that seeds the experiments
    (the ITCZ shear line in vorticity is the barotropic-instability source).  Two
    PNGs are written at the ``outputs/<background>/`` level, alongside the step dirs.
    """
    import cartopy.crs as ccrs
    from .. import config as cfgmod
    model = cfg["model"]
    bg = cfg["background"]
    layout = get_layout(model)
    u0 = State.from_npz(cfgmod.ic_path(cfg, bg, model), model)
    extent = _domain_extent(cfg["plot"])
    out_dir = out_dir or cfgmod.bg_output_dir(cfg, bg)
    paths = []

    # --- 850 hPa relative vorticity (seismic, discrete, double-ended) ---
    u850, v850 = layout.get_uv(u0, 850)
    zeta = relative_vorticity(u850, v850) * 1e5
    clim = vort_clim or cfg["plot"]["vort_clim"]
    cmap, norm, levels = _discrete("seismic", clim, cfg["plot"].get("vort_step", 1.0))
    fig = plt.figure(figsize=(11, 3.4))
    ax = _make_ax(fig, (1, 1, 1), extent)
    mesh = ax.pcolormesh(LON, LAT, zeta, cmap=cmap, norm=norm, shading="auto",
                         transform=ccrs.PlateCarree())
    ax.set_title(f"{bg} initial field  850 hPa relative vorticity ({model})", fontsize=10)
    plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02, extend="both", ticks=levels[::2],
                 label=r"$\zeta\times10^{5}$ (s$^{-1}$)")
    fig.tight_layout()
    p = os.path.join(out_dir, f"ic_vort_{model}.png")
    fig.savefig(p, dpi=130); plt.close(fig); paths.append(p); print(f"[plot] {p}")

    # --- TCWV (sequential, single-ended) ---
    tcwv = layout.tcwv(u0)
    tlev = np.arange(0, tcwv_max + 1, 10.0)
    tcmap = plt.get_cmap("YlGnBu")
    tnorm = BoundaryNorm(tlev, ncolors=tcmap.N, extend="max")
    fig = plt.figure(figsize=(11, 3.4))
    ax = _make_ax(fig, (1, 1, 1), extent)
    mesh = ax.pcolormesh(LON, LAT, tcwv, cmap=tcmap, norm=tnorm, shading="auto",
                         transform=ccrs.PlateCarree())
    ax.set_title(f"{bg} initial field  TCWV ({model})", fontsize=10)
    plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02, extend="max", ticks=tlev,
                 label=r"TCWV (kg m$^{-2}$)")
    fig.tight_layout()
    p = os.path.join(out_dir, f"ic_tcwv_{model}.png")
    fig.savefig(p, dpi=130); plt.close(fig); paths.append(p); print(f"[plot] {p}")
    return paths


def plot_forcing_ellipse(cfg, out=None):
    """Overlay heating amplitude + dashed boundary ellipse on a Pacific map with
    lat/lon axes, to verify it matches the PDF dashed contour."""
    import cartopy.crs as ccrs
    fcfg = cfg["forcing"]
    slat, slon = sigmas(fcfg)
    H = horizontal_ellipse(fcfg["center_lat"], fcfg["center_lon"], slat, slon)
    lonb, latb = ellipse_boundary(fcfg)

    fig = plt.figure(figsize=(12, 3.6))
    ax = _make_ax(fig, (1, 1, 1), [120, 270, 0, 45])
    mesh = ax.pcolormesh(LON, LAT, H, cmap="Reds", shading="auto", vmin=0, vmax=1,
                         transform=ccrs.PlateCarree())
    ax.plot(lonb, latb, "--", color="orange", lw=2.0, transform=ccrs.PlateCarree(),
            label="heating boundary (dashed)")
    ax.plot(fcfg["center_lon"], fcfg["center_lat"], "k*", ms=12,
            transform=ccrs.PlateCarree(), label="center (7.5N, 165W)")
    for lonmark, txt in [(120, "120E"), (195, "165W"), (270, "90W")]:
        ax.plot([lonmark, lonmark], [0, 45], color="gray", lw=0.6, ls="-",
                transform=ccrs.PlateCarree())
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"Heating ellipse  center=({fcfg['center_lat']}N, 165W)  "
                 f"extent 120E->90W  lat half-width {fcfg['lat_halfwidth']} deg")
    plt.colorbar(mesh, ax=ax, shrink=0.8, label="heating amplitude (normalized)")
    fig.tight_layout()
    out = out or os.path.join(cfg["paths"]["output_dir"], "forcing_ellipse.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[plot] {out}")
    return out
