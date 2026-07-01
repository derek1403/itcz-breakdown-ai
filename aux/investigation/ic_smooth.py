"""User idea #4: would Gaussian-smoothing the IC reduce the spurious early land/
topography vorticity? Plot the IC 850-hPa vorticity and TCWV, RAW vs Gaussian-smoothed
at several sigmas, and save smoothed IC npz(s) for a follow-up run.

Smoothing is applied to EVERY 2-D field of the IC (all upper vars x levels + surface),
lon-wrap aware, then vorticity/TCWV are diagnosed from the smoothed state.

    python investigation/ic_smooth.py [--save_sigma 2]
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter
import cartopy.crs as ccrs

from itcz import config as cfgmod
from itcz.models.layout import State, get_layout
from itcz.plotting.tracker import LAT, LON, vort850, tcwv_anom, _make_ax, _discrete

DOMAIN = [100, 290, 0, 45]
SIGMAS = [0, 1, 2, 4]


def smooth_state(st, sigma):
    if sigma <= 0:
        return st
    out = st.copy()
    for k, arr in out.arrays.items():
        a = arr.reshape(-1, arr.shape[-2], arr.shape[-1])
        for i in range(a.shape[0]):
            a[i] = gaussian_filter(a[i], sigma=(sigma, sigma), mode=("nearest", "wrap"))
        out.arrays[k] = a.reshape(arr.shape)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save_sigma", type=float, default=2.0)
    args = ap.parse_args()
    cfg = cfgmod.load_config({"model": "pangu", "background": "paperDJF"})
    lay = get_layout("pangu")
    u0 = State.from_npz(cfgmod.ic_path(cfg, "paperDJF", "pangu"), "pangu")
    figdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs", "ic_smooth")
    os.makedirs(figdir, exist_ok=True)

    cmap_v, norm_v, lev_v = _discrete("seismic", 10.0, 1.0)
    fig = plt.figure(figsize=(11, 2.4 * len(SIGMAS)))
    for k, s in enumerate(SIGMAS):
        st = smooth_state(u0, s)
        z = vort850(st, lay) * 1e5
        ax = _make_ax(fig, (len(SIGMAS), 1, k + 1), DOMAIN)
        mesh = ax.pcolormesh(LON, LAT, z, cmap=cmap_v, norm=norm_v, shading="auto", transform=ccrs.PlateCarree())
        ax.set_title(f"IC 850hPa vorticity  {'RAW' if s==0 else f'smoothed sigma={s:g} (~{s*0.25:.2f} deg)'}", fontsize=9)
        plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02, extend="both", ticks=lev_v[::2])
    fig.tight_layout()
    p1 = os.path.join(figdir, "ic_vort_raw_vs_smoothed.png"); fig.savefig(p1, dpi=120); plt.close(fig)
    print(f"[ic_smooth] {p1}")

    # TCWV (full field, BrBG)
    cmap_t, norm_t, lev_t = _discrete("BrBG", 60.0, 10.0)
    fig = plt.figure(figsize=(11, 2.4 * len(SIGMAS)))
    for k, s in enumerate(SIGMAS):
        st = smooth_state(u0, s)
        w = lay.tcwv(st)  # full-column water vapour of the IC
        ax = _make_ax(fig, (len(SIGMAS), 1, k + 1), DOMAIN)
        mesh = ax.pcolormesh(LON, LAT, w, cmap="YlGnBu", shading="auto", vmin=0, vmax=60, transform=ccrs.PlateCarree())
        ax.set_title(f"IC TCWV  {'RAW' if s==0 else f'smoothed sigma={s:g}'}", fontsize=9)
        plt.colorbar(mesh, ax=ax, shrink=0.85, pad=0.02)
    fig.tight_layout()
    p2 = os.path.join(figdir, "ic_tcwv_raw_vs_smoothed.png"); fig.savefig(p2, dpi=120); plt.close(fig)
    print(f"[ic_smooth] {p2}")

    # save one smoothed IC for a follow-up run
    s = args.save_sigma
    sm = smooth_state(u0, s)
    out_npz = os.path.join(cfg["paths"]["ic_dir"], f"u0_paperDJFsm{s:g}_pangu.npz")
    sm.save_npz(out_npz)
    print(f"[ic_smooth] saved smoothed IC (sigma={s:g}) -> {out_npz}")


if __name__ == "__main__":
    main()
