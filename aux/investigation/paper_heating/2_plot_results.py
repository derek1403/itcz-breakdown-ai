"""畫 paper_amp<amp>.h5 的結果 — 由 3_plot_vorticity.py 複製微調。

對每個 amp 畫：
  figs/vort_amp<amp>.png  : 850hPa 渦度 day 0/1/4/6/9/12/15（對齊 AI-Forum）
  figs/tcwv_amp<amp>.png  : TCWV 擾動 同樣天數
  figs/timeseries.png     : ITCZ 帶(0-20N,120-270E)內 peak ζ / peak TCWV 隨時間
渦度公式沿用 3_plot_vorticity.py 的球面相對渦度。
"""
import glob
import os
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

LAT = np.linspace(90.0, -90.0, 721)
LON = np.linspace(0.0, 360.0, 1440, endpoint=False)
A_EARTH = 6.371e6

PLOT_DAYS = [0, 1, 4, 6, 9, 12, 15]      # 對齊 AI-Forum
BAND = (0, 20, 120, 270)                  # lat0,lat1,lon0,lon1（找峰值用）


def vorticity(u, v):
    phi = np.deg2rad(LAT)
    lam = np.deg2rad(LON)
    cosphi = np.cos(phi)[:, None]
    cosphi = np.where(np.abs(cosphi) < 1e-6, 1e-6, cosphi)
    dv_dlam = np.gradient(v, lam, axis=1)
    ducos_dphi = np.gradient(u * cosphi, phi, axis=0)
    return (dv_dlam - ducos_dphi) / (A_EARTH * cosphi)


def band_mask():
    la0, la1, lo0, lo1 = BAND
    m = ((LAT >= la0) & (LAT <= la1))[:, None] & ((LON >= lo0) & (LON <= lo1))[None, :]
    return m


def day_index(days, d):
    """回傳該天在陣列的 index；day0 沒存(擾動為0) → None。"""
    if d == 0:
        return None
    idx = np.where(days == d)[0]
    return int(idx[0]) if len(idx) else None


def panel(field_of_day, days, title, fname, cmap, vmin, vmax, cbar_label, step):
    # 離散 colorbar：每 step 一階，看得到微小變化
    levels = np.arange(vmin, vmax + step / 2, step)
    norm = BoundaryNorm(levels, plt.get_cmap(cmap).N, clip=True)
    n = len(PLOT_DAYS)
    ncol = 3
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(6 * ncol, 2.6 * nrow))
    axes = np.array(axes).reshape(-1)
    for i in range(len(axes)):
        ax = axes[i]
        if i >= n:
            ax.axis("off"); continue
        d = PLOT_DAYS[i]
        fld = field_of_day(d)
        im = ax.pcolormesh(LON, LAT, fld, cmap=cmap, norm=norm, shading="auto")
        ax.set_xlim(100, 290); ax.set_ylim(0, 45)
        ax.set_title(f"day {d}", fontsize=10)
        fig.colorbar(im, ax=ax, shrink=0.8, label=cbar_label, ticks=levels[::2])
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(fname, dpi=120)
    plt.close(fig)
    print("saved", fname, flush=True)


def main():
    files = sorted(glob.glob("output/paper_*_amp*.h5"))
    if not files:
        print("no output/paper_*_amp*.h5 yet"); return

    mask = band_mask()
    fig_ts, axts = plt.subplots(1, 2, figsize=(12, 4))

    for f in files:
        with h5py.File(f, "r") as h5:
            u = h5["u850"][:]; v = h5["v850"][:]
            tc = h5["tcwv"][:]; days = h5["days"][:]
            amp = float(h5.attrs["amp_K_per_day"])
        tag = os.path.basename(f).replace("paper_", "").replace(".h5", "")  # e.g. Deep_amp1.5

        # 預先算每天的渦度（×1e5）
        zeta = np.stack([vorticity(u[k], v[k]) * 1e5 for k in range(u.shape[0])])

        def zfield(d):
            idx = day_index(days, d)
            return np.zeros((721, 1440)) if idx is None else zeta[idx]

        def wfield(d):
            idx = day_index(days, d)
            return np.zeros((721, 1440)) if idx is None else tc[idx]

        panel(zfield, days, f"850hPa zeta'  ({tag}, K/day)",
              f"figs/vort_{tag}.png", "seismic", -10, 10,
              r"$\zeta'\times10^{5}$ s$^{-1}$", step=1)
        panel(wfield, days, f"TCWV'  ({tag})",
              f"figs/tcwv_{tag}.png", "BrBG", -45, 45, "TCWV' (mm)", step=3)

        # 時序：ITCZ 帶內 peak
        zpk = [np.nanmax(np.where(mask, zeta[k], -np.inf)) for k in range(zeta.shape[0])]
        wpk = [np.nanmax(np.where(mask, tc[k], -np.inf)) for k in range(tc.shape[0])]
        axts[0].plot(days, zpk, "o-", label=tag)
        axts[1].plot(days, wpk, "o-", label=tag)
        print(f"{tag}: peak zeta {max(zpk):.1f}e-5 (day {days[int(np.argmax(zpk))]}), "
              f"peak TCWV {max(wpk):.1f} (day {days[int(np.argmax(wpk))]})", flush=True)

    axts[0].axhline(47, color="k", ls="--", lw=0.8, label="AI-Forum ~47")
    axts[1].axhline(45, color="k", ls="--", lw=0.8, label="AI-Forum ~45")
    axts[0].set_title("peak 850hPa zeta' in ITCZ band"); axts[0].set_xlabel("day")
    axts[0].set_ylabel(r"$\zeta'\times10^{5}$ s$^{-1}$"); axts[0].legend(); axts[0].grid(alpha=.3)
    axts[1].set_title("peak TCWV' in ITCZ band"); axts[1].set_xlabel("day")
    axts[1].set_ylabel("TCWV' (mm)"); axts[1].legend(); axts[1].grid(alpha=.3)
    fig_ts.tight_layout()
    fig_ts.savefig("figs/timeseries.png", dpi=120)
    print("saved figs/timeseries.png", flush=True)


if __name__ == "__main__":
    main()
