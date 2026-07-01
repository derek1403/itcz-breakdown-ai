"""論文水平加熱（Hakim & Masanam）— 先畫加熱分布，給人看確認後再跑 pangu。

水平：perturbations_ellipse（= cos(k(φ-ylat)) × Gaspari-Cohn(eq.3) in lon），
      k=18, ylat=10 → 緯向單一波瓣嚴格落在 5-15N、峰值 10N；
      xlon=195(=165W)、locRad(L)=10000 km。
垂直：Deep = sin(π·pn), pn=(p-200)/800, 只在 1000-200hPa 非零、峰值約 600hPa。
振幅：本檔只畫「形狀×單位振幅」，實際 amp 在 1_run_pangu.py 掃 1.5 / 3 K/day。

輸出 figs/heating_dist.png。
"""
import numpy as np
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import panguweather_utils as pw

km = 1.e3
# 加熱參數（與 1_run_pangu.py 必須一致）
K_WAVE = 18        # cos 波數：在 ylat 兩側 ±5度 處歸零 (18*5=90deg)
YLAT = 10.0        # 緯向中心 10N
XLON = 195.0       # 經向中心 195E = 165W
L_KM = 15000.      # Gaspari-Cohn 經向影響距離（放寬：10000 -> 15000 km）
LOCRAD = L_KM * km

with open("config.yml") as fh:
    config = yaml.safe_load(fh)
levels = np.array(config["levels"], dtype=float)

# --- 讀網格座標 ---
mean_pl, mean_sfc, lat, lon = pw.fetch_mean_state(config["path_mean"], zm=False)

# --- 水平形狀（峰值 ~1）---
shape2d = pw.perturbations_ellipse(lat, lon, K_WAVE, YLAT, XLON, LOCRAD)   # (721,1440)
print("shape2d max =", float(shape2d.max()), " min =", float(shape2d.min()), flush=True)


# --- Deep 垂直分布（copy 自 src/itcz/experiment/forcing.py::vertical_profile）---
def deep_profile(levels_hpa):
    p = np.asarray(levels_hpa, dtype=float)
    v = np.zeros_like(p)
    mask = (p >= 200) & (p <= 1000)
    pn = (p[mask] - 200.0) / 800.0
    v[mask] = np.sin(np.pi * pn)
    return v


vprof = deep_profile(levels)
klev_peak = int(np.argmax(vprof))   # Deep 峰值層 ≈ 600hPa
print("Deep profile:", dict(zip(levels.astype(int), np.round(vprof, 3))), flush=True)
print("peak level =", int(levels[klev_peak]), "hPa", flush=True)

# 3D 加熱（單位振幅）= Deep(p) × shape(lat,lon)
heat3d = vprof[:, None, None] * shape2d[None, :, :]   # (13,721,1440)

# --- 切面索引 ---
jlat = int(np.argmin(np.abs(lat - YLAT)))   # 10N 緯度列
ilon = int(np.argmin(np.abs(lon - XLON)))   # 195E 經度行

# =================== 畫圖 ===================
fig = plt.figure(figsize=(14, 9))

# (a) 水平地圖：Deep 峰值層
ax1 = fig.add_subplot(2, 2, 1)
im1 = ax1.pcolormesh(lon, lat, heat3d[klev_peak], cmap="hot_r",
                     vmin=0, vmax=1, shading="auto")
ax1.axhline(5, color="c", ls="--", lw=1)
ax1.axhline(15, color="c", ls="--", lw=1)
ax1.axhline(YLAT, color="g", ls=":", lw=1)
ax1.axvline(XLON, color="g", ls=":", lw=1)
ax1.set_xlim(60, 330)
ax1.set_ylim(-15, 35)
ax1.set_title(f"(a) Horizontal shape @ {int(levels[klev_peak])} hPa "
              f"(center {YLAT:.0f}N / {360-XLON:.0f}W)")
ax1.set_xlabel("lon (deg E)"); ax1.set_ylabel("lat (deg)")
fig.colorbar(im1, ax=ax1, shrink=0.8, label="unit heating")

# (b) 垂直分布
ax2 = fig.add_subplot(2, 2, 2)
ax2.plot(vprof, levels, "o-")
ax2.invert_yaxis()
ax2.set_title("(b) Deep vertical profile")
ax2.set_xlabel("unit heating"); ax2.set_ylabel("pressure (hPa)")
ax2.grid(True, alpha=0.3)

# (c) 緯向切面（過中心經度）：看 cos 波瓣是否嚴格 5-15N
ax3 = fig.add_subplot(2, 2, 3)
ax3.plot(lat, shape2d[:, ilon], "-")
ax3.axvline(5, color="c", ls="--", lw=1)
ax3.axvline(15, color="c", ls="--", lw=1)
ax3.axvline(YLAT, color="g", ls=":", lw=1)
ax3.set_xlim(-10, 30)
ax3.set_title(f"(c) Meridional cut @ {XLON:.0f}E (should be 0 outside 5-15N)")
ax3.set_xlabel("lat (deg)"); ax3.set_ylabel("unit heating")
ax3.grid(True, alpha=0.3)

# (d) 經向切面（過 10N）：Gaspari-Cohn 經向衰減
ax4 = fig.add_subplot(2, 2, 4)
ax4.plot(lon, shape2d[jlat, :], "-")
ax4.axvline(XLON, color="g", ls=":", lw=1)
ax4.set_xlim(60, 330)
ax4.set_title(f"(d) Zonal cut @ {YLAT:.0f}N (Gaspari-Cohn, L={L_KM:.0f} km)")
ax4.set_xlabel("lon (deg E)"); ax4.set_ylabel("unit heating")
ax4.grid(True, alpha=0.3)

fig.tight_layout()
out = "figs/heating_dist.png"
fig.savefig(out, dpi=120)
print("saved", out, flush=True)

# --- 文字檢查：5-15N 以外是否全 0 ---
outside = shape2d[(lat < 5) | (lat > 15), :]
print("max |shape| outside 5-15N band =", float(np.abs(outside).max()), flush=True)
print("lat extent where shape>0:",
      float(lat[(shape2d[:, ilon] > 1e-6)].min()), "to",
      float(lat[(shape2d[:, ilon] > 1e-6)].max()), "N", flush=True)
