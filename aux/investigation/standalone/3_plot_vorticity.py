"""
獨立、好讀版：給一串 npy（每個是某一步的 850hPa (u,v) 擾動），算渦度、畫在一起。
在 /LeibnizHD1/pc/AI_model/pangu 下執行：

  方法A：直接編輯下面的 FILES 清單，然後  python 3_plot_vorticity.py
  方法B：python 3_plot_vorticity.py output/pert_004.npy output/pert_036.npy ...

每個 npy 形狀 = (2,721,1440)，[0]=u850, [1]=v850（由 2_run_pangu_heating.py 存的）。
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LAT = np.linspace(90.0, -90.0, 721)
LON = np.linspace(0.0, 360.0, 1440, endpoint=False)
A_EARTH = 6.371e6   # 地球半徑(m)

# ---- 方法A：在這裡列出要畫的檔案（對應 day 1,4,6,9,12,15 = step 4,16,24,36,48,60）----
FILES = [
    "output/pert_004.npy",   # day 1
    "output/pert_016.npy",   # day 4
    "output/pert_024.npy",   # day 6
    "output/pert_036.npy",   # day 9
    "output/pert_048.npy",   # day 12
    "output/pert_060.npy",   # day 15
]


# ---- function：球面相對渦度 zeta = (1/(a cosφ)) [ ∂v/∂λ - ∂(u cosφ)/∂φ ] ----
def vorticity(u, v):
    phi = np.deg2rad(LAT)
    lam = np.deg2rad(LON)
    cosphi = np.cos(phi)[:, None]
    cosphi = np.where(np.abs(cosphi) < 1e-6, 1e-6, cosphi)   # 避免極點除以 0
    dv_dlam = np.gradient(v, lam, axis=1)
    ducos_dphi = np.gradient(u * cosphi, phi, axis=0)
    return (dv_dlam - ducos_dphi) / (A_EARTH * cosphi)


def main():
    files = sys.argv[1:] if len(sys.argv) > 1 else FILES

    n = len(files)
    ncol = 2
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(7 * ncol, 2.6 * nrow))
    axes = np.array(axes).reshape(-1)

    for i in range(len(axes)):
        ax = axes[i]
        if i >= n:
            ax.axis("off")
            continue
        uv = np.load(files[i])              # (2,721,1440)
        z = vorticity(uv[0], uv[1]) * 1e5   # 單位 1e-5 s^-1
        im = ax.pcolormesh(LON, LAT, z, cmap="seismic", vmin=-10, vmax=10, shading="auto")
        # 只看太平洋一帶 100E-290E(=70W), 0-45N（可自行改）
        ax.set_xlim(100, 290)
        ax.set_ylim(0, 45)
        ax.set_title(files[i], fontsize=8)
        fig.colorbar(im, ax=ax, shrink=0.8, label=r"$\zeta'\times10^{5}$ (s$^{-1}$)")

    fig.tight_layout()
    out = "output/vort_panels.png"
    fig.savefig(out, dpi=120)
    print("saved", out)


if __name__ == "__main__":
    main()
