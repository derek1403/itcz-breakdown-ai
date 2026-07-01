"""EX vs BL heating x (0.1, 0.5 K/day) — 存「每一天」的 500z 擾動，供看時間演變。
方法同官方 run_heating（赤道120E水平加熱、24h模型、make_steady），只改加熱垂直層：
  BL = 1000-700 hPa (level idx 0:4)；EX = 500-250 hPa (level idx 5:9)。
每個 config 存 output/exbl_<mode>_<amp>.h5：pz(Ndays,721,1440)=500z'、days、heating。
天數 = config['nhours']//24（ohr=24, 24h 模型）。全核 CPU。
"""
import os
import numpy as np
import yaml
import h5py
import panguweather_utils as pw
import onnxruntime as ort

with open("config.yml") as fh:
    config = yaml.safe_load(fh)
grav = 9.81

mean_pl, mean_sfc, lat, lon = pw.fetch_mean_state(config['path_mean'], zm=False)
mean_pl_dt, mean_sfc_dt = pw.fetch_tendency(config['path_mean'], '24', zm=False)

km = 1.e3
shape2d = pw.perturbations_ellipse(lat, lon, 6, 0., 120., 10000.*km)   # 峰值~1
LEV = {"BL": slice(0, 4), "EX": slice(0, 13)}   # BL:1000-700hPa；EX:整層 1000-50hPa(全13層)
NSTEPS = int(config['nhours']) // 24                                    # 天數
print(f"NSTEPS(days) = {NSTEPS}", flush=True)

opts = ort.SessionOptions()
opts.intra_op_num_threads = os.cpu_count()
session = ort.InferenceSession(config['path_model'] + 'pangu_weather_24.onnx',
                               sess_options=opts, providers=["CPUExecutionProvider"])

base500 = mean_pl[0, 5]
for mode in ("EX", "BL"):
    for amp in (0.1, 0.5):
        heat2d = (amp * shape2d).astype(np.float32)
        pl = np.copy(mean_pl); sfc = np.copy(mean_sfc)
        pz_days = []
        print(f"=== {mode} amp={amp} (levels {LEV[mode]}) ===", flush=True)
        for t in range(1, NSTEPS + 1):
            out_pl, out_sfc = session.run(None, {"input": pl, "input_surface": sfc})
            out_pl[2, LEV[mode]] = out_pl[2, LEV[mode]] + heat2d[np.newaxis, :, :]
            out_pl = out_pl - mean_pl_dt
            out_sfc = out_sfc - mean_sfc_dt
            pl, sfc = out_pl, out_sfc
            pz_days.append(((pl[0, 5] - base500) / grav).astype(np.float32))   # 500z' (m)
            print(f"  day {t} done", flush=True)
        outf = config['path_output'] + f'exbl_{mode}_{amp:g}.h5'
        with h5py.File(outf, 'w') as h5f:
            h5f.create_dataset('pz', data=np.stack(pz_days))      # (Ndays,721,1440)
            h5f.create_dataset('days', data=np.arange(1, NSTEPS + 1))
            h5f.create_dataset('heating', data=heat2d)
        print(f"  saved {outf}  pz shape {np.stack(pz_days).shape}", flush=True)

print("ALL DONE")
