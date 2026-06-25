"""
一次性：把 mean_DJF.h5 轉成 Pangu 要的兩個 npy（初始場 IC）。
在 /LeibnizHD1/pc/AI_model/pangu 下執行： python 1_h5_to_npy.py

mean_DJF.h5 內容：
  mean_pl : (5,13,721,1440)  = [z,q,t,u,v] x 13 層 x lat x lon   -> Pangu 的 "input"(upper)
  mean_sfc: (4,721,1440)     = [msl,u10,v10,t2m]                  -> Pangu 的 "input_surface"
  lat 90->-90, lon 0->359.75, levels 1000->50   （正好就是 Pangu 的格式，不用動）
"""
import h5py
import numpy as np

f = h5py.File("data/mean_DJF.h5", "r")
upper   = np.array(f["mean_pl"],  dtype=np.float32)   # (5,13,721,1440)
surface = np.array(f["mean_sfc"], dtype=np.float32)   # (4,721,1440)
f.close()

np.save("data/ic_upper.npy",   upper)     # 餵 Pangu 的 "input"
np.save("data/ic_surface.npy", surface)   # 餵 Pangu 的 "input_surface"
print("saved data/ic_upper.npy",   upper.shape)
print("saved data/ic_surface.npy", surface.shape)
