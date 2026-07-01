"""高斯水平加熱 跑 Pangu — 由 1_run_pangu.py 複製微調（水平改成 2D 高斯）。

與 1_run_pangu.py 唯一差別：水平形狀不用論文式 perturbations_ellipse
（cos 波瓣 × Gaspari-Cohn），改成「分離式 2D 高斯」:
    H(lat,lon) = exp(-(lat-YLAT)^2 / (2 SIG_LAT^2)) * exp(-(dlon)^2 / (2 SIG_LON^2))
    dlon = 最短環繞經度差（含 360 wrap），峰值 1.0 在 (YLAT, XLON)。
高斯寬度預設調成「長得很像」成功的 ellipse(k=8, L=25000km)：
    緯向：ellipse k=8 中心10N → 半高全寬(FWHM)≈15° → SIG_LAT≈6.4°
    經向：ellipse L=25000km GC → FWHM≈150° → SIG_LON≈65°
（你可自行調 0_plot_heating_gauss.py 頂部同名參數預覽，再回來同步這裡。）

方法（與 1_run_pangu.py 完全相同的 semi-linear/make_steady）：
  每步跑 24h Pangu → 把加熱加到溫度(out_pl[2]) → 減掉 mean tendency(穩態背景) → 下一步。
垂直加熱：Deep = sin(π·pn)，1000-200hPa 非零、峰值 600hPa（或 uniform）。
IC：JAS（由 config mean_state_season 控制）。

輸出 output/aiforum_{season}_gauss_{VTYPE}_amp{amp}{_inverse}.h5（檔名加 "gauss" 不覆蓋原檔）：
  u850,v850,z500,tcwv 皆為「擾動」(state - mean_state)，shape (NSTEPS,721,1440)；
  days、shape2d、attr amp。供 2_plot_results.py 自動讀取畫 vort_JAS_gauss_*.png 等。
全核 CPU。
"""
import os
import sys
import numpy as np
import yaml
import h5py
import panguweather_utils as pw
import onnxruntime as ort

km = 1.e3
grav = 9.81

# --- 高斯加熱參數（與 0_plot_heating_gauss.py 完全一致）---
YLAT = 10.0              # 緯向中心
XLON = 195.0            # 經向中心 195E(=165W)
SIG_LAT = 6.4          # 緯向高斯標準差(度) ~ ellipse k=8 的 FWHM
SIG_LON = 65.0         # 經向高斯標準差(度) ~ ellipse L=25000km 的 FWHM
AMPS = (2.5,)          # K/day（同成功設定）
VTYPE = sys.argv[1] if len(sys.argv) > 1 else "Deep"            # Deep | uniform
FLIP = len(sys.argv) > 2 and sys.argv[2] == "inverse"          # 初始場 lat 翻轉

with open("config.yml") as fh:
    config = yaml.safe_load(fh)
levels = np.array(config["levels"], dtype=float)
season = config["mean_state_season"]   # JAS

mean_pl, mean_sfc, lat, lon = pw.fetch_mean_state(config["path_mean"], season=season, zm=False)
mean_pl_dt, mean_sfc_dt = pw.fetch_tendency(config["path_mean"], "24", season=season, zm=False)

# --- inverse 模式：一開始把背景場(IC)+tendency 的 lat 方向 [::-1] 翻轉再丟入 pangu ---
if FLIP:
    mean_pl = mean_pl[:, :, ::-1, :].copy()
    mean_sfc = mean_sfc[:, ::-1, :].copy()
    mean_pl_dt = mean_pl_dt[:, :, ::-1, :].copy()
    mean_sfc_dt = mean_sfc_dt[:, ::-1, :].copy()
    print("*** INVERSE: IC + tendency flipped in lat ([::-1]) ***", flush=True)


# --- 水平形狀：分離式 2D 高斯（峰值 1.0）---
def gaussian_heat(lat1d, lon1d, ylat, xlon, sig_lat, sig_lon):
    ygauss = np.exp(-((lat1d - ylat) ** 2) / (2.0 * sig_lat ** 2))            # (nlat,)
    dlon = ((lon1d - xlon + 180.0) % 360.0) - 180.0                          # 最短環繞經度差
    xgauss = np.exp(-(dlon ** 2) / (2.0 * sig_lon ** 2))                      # (nlon,)
    return (ygauss[:, None] * xgauss[None, :]).astype(np.float64)             # (nlat,nlon)


shape2d = gaussian_heat(lat, lon, YLAT, XLON, SIG_LAT, SIG_LON)   # (721,1440), 峰值~1


# --- 垂直分布：Deep 或 uniform（與 1_run_pangu.py 相同）---
def vertical_profile(name, levels_hpa):
    p = np.asarray(levels_hpa, dtype=float)
    v = np.zeros_like(p)
    mask = (p >= 200) & (p <= 1000)
    if name == "Deep":
        pn = (p[mask] - 200.0) / 800.0
        v[mask] = np.sin(np.pi * pn)
    elif name == "uniform":
        v[mask] = 1.0
    else:
        raise ValueError(f"unknown VTYPE {name}")
    return v


vprof = vertical_profile(VTYPE, levels)
unit3d = (vprof[:, None, None] * shape2d[None, :, :]).astype(np.float32)   # (13,721,1440)

NSTEPS = int(config["nhours"]) // 24
print(f"[GAUSS] VTYPE={VTYPE}; FLIP={FLIP}; NSTEPS(days) = {NSTEPS}; "
      f"center {YLAT:.0f}N/{XLON:.0f}E sig_lat={SIG_LAT}deg sig_lon={SIG_LON}deg; "
      f"vprof nonzero levels {levels[vprof>0].astype(int)}; "
      f"shape max {shape2d.max():.3f}", flush=True)

# --- 背景 + 整層壓力（給 TCWV 用）---
base_z500 = mean_pl[0, 5].astype(np.float64)
base_u850 = mean_pl[3, 2].astype(np.float64)
base_v850 = mean_pl[4, 2].astype(np.float64)
p_pa = levels * 100.0
order = np.argsort(p_pa)


def tcwv(qcol):
    """TCWV (mm) = (1/g)∫q dp，qcol shape (13,721,1440)。"""
    q = qcol[order].astype(np.float64)
    return np.trapz(q, x=p_pa[order], axis=0) / grav


base_tcwv = tcwv(mean_pl[1])

opts = ort.SessionOptions()
opts.intra_op_num_threads = os.cpu_count()
session = ort.InferenceSession(config["path_model"] + "pangu_weather_24.onnx",
                               sess_options=opts, providers=["CPUExecutionProvider"])

for amp in AMPS:
    heat3d = (amp * unit3d).astype(np.float32)
    pl = np.copy(mean_pl)
    sfc = np.copy(mean_sfc)
    u_d, v_d, z_d, w_d = [], [], [], []
    print(f"=== GAUSS {VTYPE} amp={amp} K/day  (max heat {heat3d.max():.3f} K/step) ===", flush=True)
    for t in range(1, NSTEPS + 1):
        out_pl, out_sfc = session.run(None, {"input": pl, "input_surface": sfc})
        out_pl[2] = out_pl[2] + heat3d           # 加熱進溫度（Deep 垂直、高斯水平）
        out_pl = out_pl - mean_pl_dt             # make_steady：扣穩態背景趨勢
        out_sfc = out_sfc - mean_sfc_dt
        pl, sfc = out_pl, out_sfc
        # 存「擾動」場（state - mean_state）
        u_d.append((pl[3, 2].astype(np.float64) - base_u850).astype(np.float32))
        v_d.append((pl[4, 2].astype(np.float64) - base_v850).astype(np.float32))
        z_d.append(((pl[0, 5].astype(np.float64) - base_z500) / grav).astype(np.float32))
        w_d.append((tcwv(pl[1]) - base_tcwv).astype(np.float32))
        print(f"  day {t} done", flush=True)
    suffix = "_inverse" if FLIP else ""
    outf = config["path_output"] + f"aiforum_{season}_gauss_{VTYPE}_amp{amp:g}{suffix}.h5"
    with h5py.File(outf, "w") as h5f:
        h5f.create_dataset("u850", data=np.stack(u_d))
        h5f.create_dataset("v850", data=np.stack(v_d))
        h5f.create_dataset("z500", data=np.stack(z_d))
        h5f.create_dataset("tcwv", data=np.stack(w_d))
        h5f.create_dataset("days", data=np.arange(1, NSTEPS + 1))
        h5f.create_dataset("shape2d", data=shape2d.astype(np.float32))
        h5f.attrs["amp_K_per_day"] = amp
    print(f"  saved {outf}", flush=True)

print("ALL DONE")
