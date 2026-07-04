"""QC montage driven by HAND-LABELLED eye positions (tracking/track_eye.md).

The user tracks vortices by eye (labels 1..4, with split/merge sub-labels like
2a/2b) and lists an approximate (lon, lat) per label per day in track_eye.md.
This script, for every day, loads that day's 850 hPa zeta' field, SNAPS each
eye point to the nearest local maximum within --snap_radius, and draws a
Fig.3-style montage so the labelling can be verified:

  hollow circle = the eye (approximate) position as written in the md
  filled star   = the snapped local-max nearby (what the tracker would use)
  thin line     = how far the snap moved (long line => check it)
  text label    = the md label (1, 2a, 2b, 3, 4); colour = base vortex number

If two labels on the same day snap to (almost) the same grid cell the title is
flagged with "COLLISION" so you can decide whether the snap radius was too big.

NOT a paper figure.  Output -> <run_dir>/tracking/eyecheck_montage.png

    python scripts/plot_eyecheck.py [run_dir] [--snap_radius 3.0] [--ncol 4]
        [--eye_file tracking/track_eye.md] [--smooth 1.0]
"""
import argparse
import json
import os
import re

import _bootstrap  # noqa: F401  (puts src/ on sys.path)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.ndimage import gaussian_filter

from itcz.plotting import tracker as T
from itcz.plotting.tracker import LON, LAT, _discrete, _domain_extent, _make_ax
from itcz.models.layout import get_layout

DEFAULT_RUN = "outputs/JAS/step1_pangu_JAS_Deep_2.5Kday"
BASE_COLORS = {1: "tab:blue", 2: "tab:orange", 3: "tab:green", 4: "tab:red"}

_PT = re.compile(
    r"^\*\s*([0-9]+[a-z]?)\s*:\s*\(\s*(\d+(?:\.\d+)?)\s*°?\s*([EW])?\s*,\s*"
    r"(\d+(?:\.\d+)?)\s*°?\s*([NS])?\s*\)")
_DAY = re.compile(r"^#{1,6}\s*day\s*(\d+(?:\.\d+)?)", re.IGNORECASE)


def parse_eye(path):
    """Return {day(float): [(label, lon_east, lat), ...]} from track_eye.md."""
    out, cur = {}, None
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            m = _DAY.match(s)
            if m:
                cur = float(m.group(1))
                out.setdefault(cur, [])
                continue
            m = _PT.match(s)
            if m and cur is not None:
                label, lonv, ew, latv, ns = m.groups()
                lon = float(lonv)
                if ew == "W":
                    lon = 360.0 - lon
                elif ew == "E" and lon < 0:
                    lon = 360.0 + lon
                lat = float(latv) * (-1.0 if ns == "S" else 1.0)
                out[cur].append((label, lon, lat))
    return out


def base_num(label):
    m = re.match(r"(\d+)", label)
    return int(m.group(1)) if m else 0


def snap(zeta_s, zeta_raw, tcwv, lon0, lat0, radius):
    """Snap (lon0,lat0) to the local max of the smoothed field within `radius`
    (cos-lat weighted deg).  Returns (lon, lat, zeta_raw, tcwv, moved_deg)."""
    coslat = np.cos(np.deg2rad(lat0))
    dlon = (LON[None, :] - lon0) * coslat
    dlat = (LAT[:, None] - lat0)
    within = (dlon ** 2 + dlat ** 2) <= radius ** 2
    if not within.any():
        return lon0, lat0, float("nan"), float("nan"), 0.0
    masked = np.where(within, zeta_s, -np.inf)
    j, i = np.unravel_index(np.argmax(masked), masked.shape)
    lon, lat = float(LON[i]), float(LAT[j])
    moved = float(np.hypot((lon - lon0) * coslat, lat - lat0))
    return lon, lat, float(zeta_raw[j, i]), float(tcwv[j, i]), moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default=DEFAULT_RUN)
    ap.add_argument("--eye_file", default=None,
                    help="default: <run_dir>/tracking/track_eye.md")
    ap.add_argument("--snap_radius", type=float, default=3.0,
                    help="search radius for the nearby local max (deg)")
    ap.add_argument("--smooth", type=float, default=1.0,
                    help="gaussian smoothing (grid cells) before finding the peak")
    ap.add_argument("--ncol", type=int, default=4)
    args = ap.parse_args()

    eye_file = args.eye_file or os.path.join(args.run_dir, "tracking", "track_eye.md")
    eye = parse_eye(eye_file)

    with open(os.path.join(args.run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    pcfg = cfg["plot"]
    model = cfg["model"]
    layout = get_layout(model)
    extent = _domain_extent(pcfg)
    cmap, norm, levels = _discrete("seismic", pcfg["vort_clim"], pcfg.get("vort_step", 1.0))

    # only montage days that appear in the eye file (sorted ascending)
    days = sorted(eye.keys())
    ncol = args.ncol
    nrow = int(np.ceil(len(days) / ncol))
    fig = plt.figure(figsize=(5.0 * ncol, 2.4 * nrow))
    axes, mesh = [], None
    snapped_rows = []  # (day, label, lon, lat, zeta, tcwv)

    for k, day in enumerate(days):
        step = T.step_for_day(day, cfg["step_hours"])
        st = T.load_pert(args.run_dir, step, model)
        zeta = np.asarray(T.vort850(st, layout)) * 1e5
        tcwv = np.asarray(T.tcwv_anom(st, layout))
        zeta_s = gaussian_filter(zeta, sigma=args.smooth)

        ax = _make_ax(fig, (nrow, ncol, k + 1), extent)
        axes.append(ax)
        mesh = ax.pcolormesh(LON, LAT, zeta, cmap=cmap, norm=norm,
                             shading="auto", transform=ccrs.PlateCarree())

        placed = []  # snapped (lon,lat) to detect collisions
        collision = False
        for label, lon0, lat0 in eye[day]:
            lon, lat, zval, tw, moved = snap(zeta_s, zeta, tcwv, lon0, lat0, args.snap_radius)
            col = BASE_COLORS.get(base_num(label), "0.3")
            snapped_rows.append((day, label, lon, lat, zval, tw))
            for pl, plon, plat in placed:
                if np.hypot((lon - plon) * np.cos(np.deg2rad(lat)), lat - plat) < 1.0:
                    collision = True
            placed.append((label, lon, lat))
            # eye (hollow) -> snapped (filled star), connected
            ax.plot([lon0, lon], [lat0, lat], "-", color=col, lw=0.8, alpha=0.7,
                    zorder=5, transform=ccrs.PlateCarree())
            ax.scatter([lon0], [lat0], marker="o", s=40, facecolors="none",
                       edgecolors=col, linewidths=1.4, zorder=6, transform=ccrs.PlateCarree())
            ax.scatter([lon], [lat], marker="*", s=170, c=[col], edgecolor="k",
                       linewidths=0.6, zorder=7, transform=ccrs.PlateCarree())
            ax.text(lon + 0.6, lat + 0.6, label, color=col, fontsize=9, fontweight="bold",
                    zorder=8, transform=ccrs.PlateCarree(),
                    path_effects=None)
        ttl = f"day {day:.0f}   n={len(eye[day])}"
        if collision:
            ttl += "  ⚠COLLISION"
        ax.set_title(ttl, fontsize=10, color="crimson" if collision else "k")

    fig.subplots_adjust(left=0.03, right=0.92, top=0.95, bottom=0.03, hspace=0.35, wspace=0.10)
    fig.canvas.draw()
    top = axes[ncol - 1].get_position() if len(axes) >= ncol else axes[0].get_position()
    bot = axes[-1].get_position()
    cax = fig.add_axes([0.935, bot.y0, 0.008, top.y1 - bot.y0])
    cb = fig.colorbar(mesh, cax=cax, extend="both", ticks=levels[::2])
    cb.set_label(r"$\zeta'\times10^{5}$ (s$^{-1}$)")

    outdir = os.path.join(args.run_dir, "tracking")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "eyecheck_montage.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)

    csv = os.path.join(outdir, "eye_snapped.csv")
    with open(csv, "w") as fh:
        fh.write("day,label,lon,lat,zeta_1e5,tcwv\n")
        for day, label, lon, lat, zval, tw in snapped_rows:
            fh.write(f"{day:.0f},{label},{lon:.2f},{lat:.2f},{zval:.2f},{tw:.2f}\n")
    print(f"[eyecheck] {len(days)} days, {len(snapped_rows)} points")
    print(f"[eyecheck] saved {out}")
    print(f"[eyecheck] saved {csv}  (snap_radius={args.snap_radius}, smooth={args.smooth})")


if __name__ == "__main__":
    main()
