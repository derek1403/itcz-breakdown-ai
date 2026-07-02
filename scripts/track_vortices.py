"""Track discrete ITCZ-breakdown vortices through a run and plot their genealogy.

Detects local maxima of 850 hPa zeta' in the tropical band each day, links them
across days into tracks that may SPLIT (one vortex -> two), and plots:
  (1) a track map (paths, coloured by day),
  (2) zeta' vs time as a branching "tree" (shared trunk that grows branches),
  (3) TCWV' at each vortex centre vs time (same branching).

Children inherit the parent's history up to the split, so a single line visibly
splits into 2, then 4, ... exactly matching the roll-up seen in panels_vort.

    python scripts/track_vortices.py outputs/<run_dir> [--band 5 30 120 220]
       [--peak_min 4] [--nbhd_deg 6] [--max_jump 10] [--min_len 3] [--keep_zeta 6]
"""
import argparse
import json
import os
from collections import defaultdict

import _bootstrap  # noqa: F401
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, maximum_filter

from itcz.models.layout import get_layout
from itcz.plotting import tracker as T
from itcz.plotting.tracker import LAT, LON

DEG = 0.25  # grid spacing


def detect(zeta1e5, tcwv, band, peak_min, nbhd_deg, smooth=2.0):
    """Return list of vortex detections (local maxima of zeta') in the band."""
    lat_min, lat_max, lon_min, lon_max = band
    mask = ((LAT >= lat_min) & (LAT <= lat_max))[:, None] & \
           ((LON >= lon_min) & (LON <= lon_max))[None, :]
    zs = gaussian_filter(zeta1e5, sigma=smooth)
    size = max(3, int(round(nbhd_deg / DEG)))
    mx = maximum_filter(zs, size=size, mode="nearest")
    peaks = (zs >= mx - 1e-9) & (zs >= peak_min) & mask
    dets = []
    for j, i in zip(*np.where(peaks)):
        dets.append({"lon": float(LON[i]), "lat": float(LAT[j]),
                     "zeta": float(zeta1e5[j, i]), "tcwv": float(tcwv[j, i])})
    return dets


def gcdist(a, b):
    """Approx degree distance (cos-lat weighted) between two detections."""
    dlat = a["lat"] - b["lat"]
    dlon = (a["lon"] - b["lon"]) * np.cos(np.deg2rad(0.5 * (a["lat"] + b["lat"])))
    return float(np.hypot(dlat, dlon))


def link(steps_dets, days, max_jump):
    """Link detections across days into tracks that may split. Returns track list."""
    tracks = []
    nid = [0]
    def new_track(pt, parent):
        nid[0] += 1
        tr = {"id": nid[0], "parent": parent, "alive": True, "split": False,
              "points": [pt]}
        tracks.append(tr)
        return tr

    for dets, day in zip(steps_dets, days):
        for d in dets:
            d["pt"] = {"day": day, "lon": d["lon"], "lat": d["lat"],
                       "zeta": d["zeta"], "tcwv": d["tcwv"]}
        alive = [tr for tr in tracks if tr["alive"]]
        # assign each detection to nearest alive track within max_jump
        for d in dets:
            best, bd = None, max_jump
            for tr in alive:
                dd = gcdist(d, tr["points"][-1])
                if dd < bd:
                    bd, best = dd, tr
            d["trk"] = best
        grouped = defaultdict(list)
        for d in dets:
            if d["trk"] is not None:
                grouped[d["trk"]["id"]].append(d)
        for tr in alive:
            ds = grouped.get(tr["id"], [])
            if len(ds) == 0:
                tr["alive"] = False                      # track ends
            elif len(ds) == 1:
                tr["points"].append(ds[0]["pt"])
            else:                                        # SPLIT
                tr["alive"] = False
                tr["split"] = True
                for d in ds:
                    child = {"id": None, "parent": tr["id"], "alive": True,
                             "split": False, "points": list(tr["points"]) + [d["pt"]]}
                    nid[0] += 1
                    child["id"] = nid[0]
                    tracks.append(child)
        for d in dets:                                   # births
            if d["trk"] is None:
                new_track(d["pt"], None)
    return tracks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--band", nargs=4, type=float, default=[5, 30, 120, 220],
                    metavar=("LATMIN", "LATMAX", "LONMIN", "LONMAX"))
    ap.add_argument("--peak_min", type=float, default=4.0, help="zeta' threshold (x1e-5)")
    ap.add_argument("--nbhd_deg", type=float, default=6.0, help="min peak separation (deg)")
    ap.add_argument("--max_jump", type=float, default=10.0, help="max day-to-day move (deg)")
    ap.add_argument("--min_len", type=int, default=3, help="min points to keep a track")
    ap.add_argument("--keep_zeta", type=float, default=6.0, help="keep track if peak zeta>=this")
    ap.add_argument("--start_day", type=float, default=4.0, help="ignore earlier days")
    args = ap.parse_args()

    with open(os.path.join(args.run_dir, "config_used.json")) as fh:
        cfg = json.load(fh)
    model = cfg["model"]
    step_hours = cfg["step_hours"]
    layout = get_layout(model)

    steps = T.list_steps(args.run_dir)
    steps_dets, days = [], []
    for s in steps:
        day = s * step_hours / 24.0
        if day < args.start_day:
            continue
        st = T.load_pert(args.run_dir, s, model)
        zeta = T.vort850(st, layout) * 1e5
        tcwv = np.asarray(T.tcwv_anom(st, layout))
        dets = detect(zeta, tcwv, args.band, args.peak_min, args.nbhd_deg)
        steps_dets.append(dets)
        days.append(day)
        print(f"  day {day:5.1f}: {len(dets)} vortices  "
              f"(peak zeta' {max([d['zeta'] for d in dets], default=0):.1f})")

    tracks = link(steps_dets, days, args.max_jump)
    # leaves = non-split tracks (their ancestry is carried in their own points)
    leaves = [tr for tr in tracks if not tr["split"]
              and len(tr["points"]) >= args.min_len
              and max(p["zeta"] for p in tr["points"]) >= args.keep_zeta]
    leaves.sort(key=lambda tr: tr["points"][0]["day"])
    print(f"[track] {len(tracks)} raw tracks -> {len(leaves)} vortex branches kept")

    # ---- plot: map + zeta genealogy + tcwv genealogy ----
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    colors = plt.get_cmap("tab10")(np.linspace(0, 1, 10))
    fig = plt.figure(figsize=(15, 12))
    banner = T._run_banner(cfg) if hasattr(T, "_run_banner") else os.path.basename(args.run_dir)
    fig.suptitle(f"Vortex tracking / genealogy\n{banner}", fontsize=11)

    axm = fig.add_subplot(3, 1, 1, projection=ccrs.PlateCarree(central_longitude=180))
    axm.add_feature(cfeature.COASTLINE, linewidth=0.5)
    axm.set_extent([args.band[2], args.band[3], args.band[0], args.band[1]], ccrs.PlateCarree())
    gl = axm.gridlines(draw_labels=True, linewidth=0.3, color="0.7"); gl.top_labels = gl.right_labels = False
    for k, tr in enumerate(leaves):
        lons = [p["lon"] for p in tr["points"]]; lats = [p["lat"] for p in tr["points"]]
        axm.plot(lons, lats, "-", color=colors[k % 10], lw=1.3, transform=ccrs.PlateCarree())
        sc = axm.scatter(lons, lats, c=[p["day"] for p in tr["points"]], cmap="viridis",
                         s=18, zorder=5, transform=ccrs.PlateCarree(), vmin=days[0], vmax=days[-1])
    axm.set_title("(a) vortex tracks (dots coloured by day)")
    fig.colorbar(sc, ax=axm, shrink=0.7, label="day", pad=0.02)

    axz = fig.add_subplot(3, 1, 2)
    for k, tr in enumerate(leaves):
        axz.plot([p["day"] for p in tr["points"]], [p["zeta"] for p in tr["points"]],
                 "-o", ms=3, color=colors[k % 10], lw=1.3)
    axz.set(title="(b) 850 hPa zeta' at vortex centres (branching genealogy)",
            xlabel="day", ylabel=r"$\zeta'$ ($\times10^{5}$ s$^{-1}$)")
    axz.grid(alpha=0.3)

    axt = fig.add_subplot(3, 1, 3)
    for k, tr in enumerate(leaves):
        axt.plot([p["day"] for p in tr["points"]], [p["tcwv"] for p in tr["points"]],
                 "-o", ms=3, color=colors[k % 10], lw=1.3)
    axt.set(title="(c) TCWV' at vortex centres (branching genealogy)",
            xlabel="day", ylabel=r"TCWV' (kg m$^{-2}$)")
    axt.grid(alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    outdir = os.path.join(args.run_dir, "tracking")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "vortex_genealogy.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"[track] saved {out}")

    # dump tracks to csv for inspection
    csv = os.path.join(outdir, "vortex_tracks.csv")
    with open(csv, "w") as fh:
        fh.write("branch,day,lon,lat,zeta_1e5,tcwv\n")
        for k, tr in enumerate(leaves):
            for p in tr["points"]:
                fh.write(f"{k},{p['day']:.2f},{p['lon']:.2f},{p['lat']:.2f},"
                         f"{p['zeta']:.2f},{p['tcwv']:.2f}\n")
    print(f"[track] saved {csv}")


if __name__ == "__main__":
    main()
