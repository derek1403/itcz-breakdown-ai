"""論文水平加熱（Hakim & Masanam）跑 Pangu — 由 run_heating_exbl.py 複製微調。

方法（與論文/官方 run_heating 相同的 semi-linear/make_steady）：
  每步跑 24h Pangu → 把加熱加到溫度(out_pl[2]) → 減掉 mean tendency(穩態背景) → 下一步。
水平加熱：perturbations_ellipse(lat,lon, k=18, ylat=10, xlon=195, L=10000km)
          = cos(18(φ-10)) 嚴格 5-15N 單波瓣 × Gaspari-Cohn(eq.3) 經向衰減，中心 165W。
垂直加熱：Deep = sin(π·pn)，1000-200hPa 非零、峰值 600hPa。
振幅掃描：amp = 1.5, 3.0 K/day（與 24h 模型 → K/step 等值）。

每個 amp 存 output/paper_amp<amp>.h5：
  u850,v850,z500,tcwv 皆為「擾動」(state - mean_state)，shape (NSTEPS,721,1440)；
  days、shape2d、attr amp。供 2_plot_results.py 畫 day 0/1/4/6/9/12/15。
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

# --- 加熱參數（與 0_plot_heating.py 完全一致）---
K_WAVE = 18
YLAT = 10.0
XLON = 195.0
L_KM = 15000.              # Gaspari-Cohn 經向影響距離（放寬：10000 -> 15000 km）
LOCRAD = L_KM * km
AMPS = (0.75, 1.0)         # K/day（微調讓 ζ 落在 ~47）
VTYPE = sys.argv[1] if len(sys.argv) > 1 else "Deep"   # Deep | uniform

with open("config.yml") as fh:
    config = yaml.safe_load(fh)
levels = np.array(config["levels"], dtype=float)

mean_pl, mean_sfc, lat, lon = pw.fetch_mean_state(config["path_mean"], zm=False)
mean_pl_dt, mean_sfc_dt = pw.fetch_tendency(config["path_mean"], "24", zm=False)

# --- 水平形狀 ---
shape2d = pw.perturbations_ellipse(lat, lon, K_WAVE, YLAT, XLON, LOCRAD)   # (721,1440), 峰值~1


# --- 垂直分布：Deep(copy 自 forcing.py) 或 uniform(論文用法：1000-200hPa 等值)---
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
print(f"VTYPE={VTYPE}; NSTEPS(days) = {NSTEPS}; "
      f"vprof nonzero levels {levels[vprof>0].astype(int)}; "
      f"shape max {shape2d.max():.3f}", flush=True)

# --- 背景 + 整層壓力（給 TCWV 用，由低到高壓積分）---
base_z500 = mean_pl[0, 5].astype(np.float64)
base_u850 = mean_pl[3, 2].astype(np.float64)
base_v850 = mean_pl[4, 2].astype(np.float64)
p_pa = levels * 100.0                       # hPa -> Pa
order = np.argsort(p_pa)                     # 由小到大壓力


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
    print(f"=== {VTYPE} amp={amp} K/day  (max heat {heat3d.max():.3f} K/step) ===", flush=True)
    for t in range(1, NSTEPS + 1):
        out_pl, out_sfc = session.run(None, {"input": pl, "input_surface": sfc})
        out_pl[2] = out_pl[2] + heat3d           # 加熱進溫度（Deep 垂直、5-15N 水平）
        out_pl = out_pl - mean_pl_dt             # make_steady：扣穩態背景趨勢
        out_sfc = out_sfc - mean_sfc_dt
        pl, sfc = out_pl, out_sfc
        # 存「擾動」場（state - mean_state）
        u_d.append((pl[3, 2].astype(np.float64) - base_u850).astype(np.float32))
        v_d.append((pl[4, 2].astype(np.float64) - base_v850).astype(np.float32))
        z_d.append(((pl[0, 5].astype(np.float64) - base_z500) / grav).astype(np.float32))
        w_d.append((tcwv(pl[1]) - base_tcwv).astype(np.float32))
        print(f"  day {t} done", flush=True)
    outf = config["path_output"] + f"paper_{VTYPE}_L{L_KM:g}_amp{amp:g}.h5"
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
