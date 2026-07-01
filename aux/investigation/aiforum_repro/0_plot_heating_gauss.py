"""高斯水平加熱 — 畫加熱分布(疊海岸線) + JAS IC 圖。由 0_plot_heating.py 複製微調。

與 0_plot_heating.py 唯一差別：水平形狀改成「分離式 2D 高斯」(取代 perturbations_ellipse)：
    H(lat,lon) = exp(-(lat-YLAT)^2/(2 SIG_LAT^2)) * exp(-(dlon)^2/(2 SIG_LON^2))
    dlon = 最短環繞經度差（含 360 wrap），峰值 1.0 在 (YLAT, XLON)。
寬度預設調成「長得很像」成功的 ellipse(k=8, L=25000km)：SIG_LAT≈6.4°、SIG_LON≈65°。
→ 你可自行調本檔頂部 SIG_LAT/SIG_LON/XLON 預覽，滿意後把同名參數同步到 1_run_pangu_gauss.py。

輸出（檔名都加 _gauss，不覆蓋原檔）：
  figs/heating_dist_gauss.png : (a)加熱(疊海岸線) (b)Deep垂直 (c)緯向切面 (d)JAS TCWV(疊海岸線)
  figs/ic_JAS_gauss.png       : JAS IC = TCWV + 850hPa 風場
"""
import numpy as np
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import panguweather_utils as pw

km = 1.e3
grav = 9.81
YLAT = 10.0        # 緯向中心
XLON = 195.0       # 經向中心 195E(=165W)
SIG_LAT = 6.4      # 緯向高斯標準差(度) ~ ellipse k=8 的 FWHM
SIG_LON = 65.0     # 經向高斯標準差(度) ~ ellipse L=25000km 的 FWHM
AMP_SHOW = 2.5     # K/day

PROJ = ccrs.PlateCarree(central_longitude=180)   # Pacific-centered，同原圖
DATA = ccrs.PlateCarree()

with open("config.yml") as fh:
    config = yaml.safe_load(fh)
levels = np.array(config["levels"], dtype=float)
season = config["mean_state_season"]

mean_pl, mean_sfc, lat, lon = pw.fetch_mean_state(config["path_mean"], season=season, zm=False)
print(f"IC season = {season}", flush=True)


# --- 水平形狀：分離式 2D 高斯（峰值 1.0）---
def gaussian_heat(lat1d, lon1d, ylat, xlon, sig_lat, sig_lon):
    ygauss = np.exp(-((lat1d - ylat) ** 2) / (2.0 * sig_lat ** 2))
    dlon = ((lon1d - xlon + 180.0) % 360.0) - 180.0
    xgauss = np.exp(-(dlon ** 2) / (2.0 * sig_lon ** 2))
    return (ygauss[:, None] * xgauss[None, :]).astype(np.float64)


shape2d = gaussian_heat(lat, lon, YLAT, XLON, SIG_LAT, SIG_LON)


def deep_profile(levels_hpa):
    p = np.asarray(levels_hpa, dtype=float)
    v = np.zeros_like(p)
    mask = (p >= 200) & (p <= 1000)
    pn = (p[mask] - 200.0) / 800.0
    v[mask] = np.sin(np.pi * pn)
    return v


vprof = deep_profile(levels)

p_pa = levels * 100.0
order = np.argsort(p_pa)
tcwv_ic = np.trapz(mean_pl[1][order].astype(np.float64), x=p_pa[order], axis=0) / grav
u850, v850 = mean_pl[3, 2], mean_pl[4, 2]

jlat = int(np.argmin(np.abs(lat - YLAT)))
ilon = int(np.argmin(np.abs(lon - XLON)))

# --- TCWV 色階：低值端白色 ---
tlev = np.arange(0, 75, 5)
_tc = plt.get_cmap("turbo")(np.linspace(0, 1, len(tlev) - 1))
_tc[0] = (1, 1, 1, 1)
CMAP_TCWV = ListedColormap(_tc)
CMAP_TCWV.set_over(plt.get_cmap("turbo")(1.0))
NORM_TCWV = BoundaryNorm(tlev, CMAP_TCWV.N)


def add_map(ax):
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
    ax.set_global()
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="0.5", alpha=0.5)
    gl.top_labels = gl.right_labels = False


# =================== 圖1：加熱分布 ===================
fig = plt.figure(figsize=(16, 9))

# (a) 加熱水平（疊海岸線）
ax1 = fig.add_subplot(2, 2, 1, projection=PROJ)
hlev = np.arange(0, AMP_SHOW + 0.25, 0.25)        # 每 0.25 K/day 一格
hnorm = BoundaryNorm(hlev, plt.get_cmap("Reds").N, clip=False, extend="max")
im1 = ax1.pcolormesh(lon, lat, AMP_SHOW * shape2d, cmap="Reds", norm=hnorm,
                     shading="auto", transform=DATA)
add_map(ax1)
ax1.set_title(f"(a) GAUSS heating ({AMP_SHOW} K/day, center {YLAT:.0f}N/{XLON:.0f}E, "
              f"sig {SIG_LAT}/{SIG_LON} deg)")
fig.colorbar(im1, ax=ax1, shrink=0.6, label="heating (K/day)", ticks=hlev,
             orientation="horizontal", pad=0.05)

# (b) Deep 垂直分布
ax2 = fig.add_subplot(2, 2, 2)
ax2.plot(vprof, levels, "o-"); ax2.invert_yaxis()
ax2.set_title("(b) Deep vertical profile")
ax2.set_xlabel("unit heating"); ax2.set_ylabel("pressure (hPa)")
ax2.grid(True, alpha=0.3)

# (c) 緯向切面（過中心經度）
ax3 = fig.add_subplot(2, 2, 3)
ax3.plot(lat, shape2d[:, ilon], "-")
ax3.axvline(YLAT, color="g", ls=":", lw=1); ax3.axvline(0, color="0.6", lw=0.6)
ax3.set_xlim(-20, 40)
ax3.set_title(f"(c) Meridional cut @ {XLON:.0f}E (sig_lat={SIG_LAT} deg, center {YLAT:.0f}N)")
ax3.set_xlabel("lat (deg)"); ax3.set_ylabel("unit heating"); ax3.grid(True, alpha=0.3)

# (d) JAS IC TCWV（疊海岸線）
print(lon.shape, lat.shape, tcwv_ic.shape)
ax4 = fig.add_subplot(2, 2, 4, projection=PROJ)
im4 = ax4.pcolormesh(lon, lat, tcwv_ic, cmap=CMAP_TCWV, norm=NORM_TCWV,
                     shading="auto", transform=DATA)
add_map(ax4)
ax4.set_title(f"(d) {season} IC: TCWV")
fig.colorbar(im4, ax=ax4, shrink=0.6, label="TCWV (kg m$^{-2}$)", ticks=tlev,
             extend="max", orientation="horizontal", pad=0.05)

fig.tight_layout()
fig.savefig("figs/heating_dist_gauss.png", dpi=120)
print("saved figs/heating_dist_gauss.png", flush=True)

# =================== 圖2：JAS IC（TCWV + 850 風）===================
fig2 = plt.figure(figsize=(11, 6))
axi = fig2.add_subplot(1, 1, 1, projection=PROJ)
imi = axi.pcolormesh(lon, lat, tcwv_ic, cmap=CMAP_TCWV, norm=NORM_TCWV,
                     shading="auto", transform=DATA)
st = 22
q = axi.quiver(lon[::st], lat[::st], u850[::st, ::st], v850[::st, ::st],
               transform=DATA, scale=400, width=0.0015, color="k")
axi.quiverkey(q, 0.9, 1.03, 10, "10 m/s", labelpos="E")
add_map(axi)
axi.set_title(f"{season} climatology mean state (TCWV + 850 hPa wind)")
fig2.colorbar(imi, ax=axi, shrink=0.7, label="Total column water vapor (kg m$^{-2}$)",
              ticks=tlev, extend="max")
fig2.tight_layout()
fig2.savefig("figs/ic_JAS_gauss.png", dpi=130)
print("saved figs/ic_JAS_gauss.png", flush=True)

# --- 文字檢查 ---
nz = shape2d[:, ilon] > 1e-3
print("lat extent where shape>1e-3:", float(lat[nz].min()), "to", float(lat[nz].max()), "N", flush=True)
nzlon = shape2d[jlat, :] > 1e-3
print("lon extent where shape>1e-3:", float(lon[nzlon].min()), "to", float(lon[nzlon].max()), "E", flush=True)
print(f"IC TCWV @ ({YLAT:.0f}N,{XLON:.0f}E) = {tcwv_ic[jlat, ilon]:.1f} kg/m2", flush=True)
