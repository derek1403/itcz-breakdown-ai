"""重現 AI-Forum 原作加熱 — 畫加熱分布(疊海岸線) + JAS IC 圖，對照原始圖。

對照原圖：
  related_paper/horizontal_heating.png : deep convective, 2.5 K/day, center 10N
  related_paper/IC.png                 : 1979-2019 JAS climatology (TCWV+850wind)

水平：perturbations_ellipse(lat,lon, k=6, ylat=10, xlon=180, L=12000km)
      = cos(6(φ-10))（broad，約 -5~25N）× Gaspari-Cohn(eq.3) 經向衰減，中心換日線 180E。
垂直：Deep = sin(π·pn)，1000-200hPa 非零、峰值 600hPa（deep convective）。
振幅：2.5 K/day。 IC：JAS（由 config mean_state_season 控制）。

輸出：
  figs/heating_dist.png : (a)加熱(疊海岸線) (b)Deep垂直 (c)緯向切面 (d)JAS TCWV(疊海岸線)
  figs/ic_JAS.png       : JAS IC = TCWV + 850hPa 風場（比照 IC.png）
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
K_WAVE = 8         # broad 緯向（約 -5~25N）
YLAT = 10.0
XLON = 195.0       # 經向中心 195E(=165W)，使範圍對稱於 60E~330E
L_KM = 25000.      # 半寬 135° → 60E 到 330E(=30W) 歸零
LOCRAD = L_KM * km
AMP_SHOW = 2.5     # K/day

PROJ = ccrs.PlateCarree(central_longitude=180)   # Pacific-centered，同原圖
DATA = ccrs.PlateCarree()

with open("config.yml") as fh:
    config = yaml.safe_load(fh)
levels = np.array(config["levels"], dtype=float)
season = config["mean_state_season"]

mean_pl, mean_sfc, lat, lon = pw.fetch_mean_state(config["path_mean"], season=season, zm=False)
print(f"IC season = {season}", flush=True)

shape2d = pw.perturbations_ellipse(lat, lon, K_WAVE, YLAT, XLON, LOCRAD)


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

# --- TCWV 色階：低值端白色（每 5 kg/m² 一格，最低格白色 + turbo）---
tlev = np.arange(0, 75, 5)                       # 0,5,...,70
_tc = plt.get_cmap("turbo")(np.linspace(0, 1, len(tlev) - 1))
_tc[0] = (1, 1, 1, 1)                            # 最低格設白色
CMAP_TCWV = ListedColormap(_tc)
CMAP_TCWV.set_over(plt.get_cmap("turbo")(1.0))   # >70 用 turbo 最深色（箭頭）
NORM_TCWV = BoundaryNorm(tlev, CMAP_TCWV.N)


def add_map(ax):
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
    ax.set_global()
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="0.5", alpha=0.5)
    gl.top_labels = gl.right_labels = False


# =================== 圖1：加熱分布 ===================
fig = plt.figure(figsize=(16, 9))

# (a) 加熱水平（疊海岸線，比照 horizontal_heating.png）
ax1 = fig.add_subplot(2, 2, 1, projection=PROJ)
hlev = np.arange(0, AMP_SHOW + 0.25, 0.25)        # 每 0.25 K/day 一格
hnorm = BoundaryNorm(hlev, plt.get_cmap("Reds").N, clip=False, extend="max")
im1 = ax1.pcolormesh(lon, lat, AMP_SHOW * shape2d, cmap="Reds", norm=hnorm,
                     shading="auto", transform=DATA)
add_map(ax1)
ax1.set_title(f"(a) deep convective heating ({AMP_SHOW} K/day, center {YLAT:.0f}N/{XLON:.0f}E)")
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
ax3.set_title(f"(c) Meridional cut @ {XLON:.0f}E (k={K_WAVE}, center {YLAT:.0f}N)")
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
fig.savefig("figs/heating_dist.png", dpi=120)
print("saved figs/heating_dist.png", flush=True)

# =================== 圖2：JAS IC（TCWV + 850 風，比照 IC.png）===================
fig2 = plt.figure(figsize=(11, 6))
axi = fig2.add_subplot(1, 1, 1, projection=PROJ)
imi = axi.pcolormesh(lon, lat, tcwv_ic, cmap=CMAP_TCWV, norm=NORM_TCWV,
                     shading="auto", transform=DATA)
st = 22   # 風場抽稀
q = axi.quiver(lon[::st], lat[::st], u850[::st, ::st], v850[::st, ::st],
               transform=DATA, scale=400, width=0.0015, color="k")
axi.quiverkey(q, 0.9, 1.03, 10, "10 m/s", labelpos="E")
add_map(axi)
axi.set_title(f"{season} climatology mean state (TCWV + 850 hPa wind)")
fig2.colorbar(imi, ax=axi, shrink=0.7, label="Total column water vapor (kg m$^{-2}$)",
              ticks=tlev, extend="max")
fig2.tight_layout()
fig2.savefig("figs/ic_JAS.png", dpi=130)
print("saved figs/ic_JAS.png", flush=True)

# --- 文字檢查 ---
nz = shape2d[:, ilon] > 1e-6
print("lat extent where shape>0:", float(lat[nz].min()), "to", float(lat[nz].max()), "N", flush=True)
nzlon = shape2d[jlat, :] > 1e-6
print("lon extent where shape>0:", float(lon[nzlon].min()), "to", float(lon[nzlon].max()), "E", flush=True)
print(f"IC TCWV @ (10N,180E) = {tcwv_ic[jlat, ilon]:.1f} kg/m2", flush=True)
