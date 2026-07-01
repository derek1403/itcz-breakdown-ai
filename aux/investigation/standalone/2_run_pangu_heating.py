"""
獨立、好讀版：用 Pangu 跑「ITCZ 加熱」實驗（pre-M re-centering）。
純 for 迴圈、只有 function、沒有 class。
在 /LeibnizHD1/pc/AI_model/pangu 下執行： python 2_run_pangu_heating.py

算法（理論正確的 pre-M）：
    B = M(u0)                            # 背景一步漂移（凍結）
    u'_0 = 0
    for n = 1..N:
        f_n = 加熱(前 7 天) 否則 0
        A   = u0 + u'_{n-1} + f_n        # 每步錨回穩態 u0，加熱加在「輸入端」
        u'_n = M(A) - B                  # 扣掉常數漂移
        存 u'_n 在 850hPa 的 (u,v)
M = Pangu 一步(6 小時)。本版用最佳設定：均勻垂直加熱(1000-250hPa)、不做 moisture clip。
"""
import numpy as np
import onnxruntime as ort

# ---------- 固定格點 / 參數 ----------
LAT = np.linspace(90.0, -90.0, 721)            # 90N -> 90S
LON = np.linspace(0.0, 360.0, 1440, endpoint=False)  # 0 -> 359.75E
LEVELS = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100, 50]  # Pangu 層序

STEP_HOURS   = 6        # 用 6 小時的 Pangu
N_DAYS       = 16       # 總長 16 天
FORCING_DAYS = 7        # 前 7 天加熱，之後關掉
AMP_K_PER_DAY = 1.5     # 加熱率 (K/day)；每步加 = 1.5 * 6/24 = 0.375 K

# 加熱橢圓（地理範圍 5-15N, 125E-95W）→ 中心(10N,195E)、半寬(5,70)、sigma=半寬/2
C_LAT, C_LON = 10.0, 195.0
SIG_LAT, SIG_LON = 5.0 / 2.0, 70.0 / 2.0


# ---------- function：Pangu 一步 ----------
def pangu_step(session, upper, surface):
    # upper:(5,13,721,1440)  surface:(4,721,1440)  都是 float32
    out_upper, out_surface = session.run(
        None, {"input": upper.astype(np.float32),
               "input_surface": surface.astype(np.float32)})
    return out_upper.astype(np.float32), out_surface.astype(np.float32)


# ---------- function：做每步的加熱場（只加在溫度 T 上）----------
def build_heating(amp_per_step):
    # 水平：高斯橢圓 (721,1440)
    dlat = (LAT - C_LAT)[:, None]
    dlon = (((LON - C_LON + 180.0) % 360.0) - 180.0)[None, :]   # 經度繞圈差
    gauss = np.exp(-0.5 * (dlat / SIG_LAT) ** 2 - 0.5 * (dlon / SIG_LON) ** 2)
    # 垂直：均勻，1000-250hPa 給 1，其餘 0
    heat = np.zeros((5, 13, 721, 1440), dtype=np.float32)       # 只有 T(index 2) 非零
    for k in range(13):
        if 250 <= LEVELS[k] <= 1000:
            heat[2, k] = amp_per_step * gauss
    return heat


# ---------- 主程式（for 迴圈）----------
def main():
    # 預設用 CPU（我們驗證過的方式，最穩）。GPU 記憶體夠的話可改成
    # providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    providers = ["CPUExecutionProvider"]
    session = ort.InferenceSession("models/pangu_weather_6.onnx", providers=providers)
    print("providers in use:", session.get_providers())

    # 初始場
    u0_upper   = np.load("data/ic_upper.npy")     # (5,13,721,1440)
    u0_surface = np.load("data/ic_surface.npy")   # (4,721,1440)

    N  = int(round(N_DAYS * 24 / STEP_HOURS))       # 總步數 = 64
    Nf = int(round(FORCING_DAYS * 24 / STEP_HOURS)) # 加熱步數 = 28
    amp_per_step = AMP_K_PER_DAY * STEP_HOURS / 24.0
    heat = build_heating(amp_per_step)

    # 背景一步漂移 B = M(u0)
    B_upper, B_surface = pangu_step(session, u0_upper, u0_surface)

    # 擾動從 0 開始
    pert_upper   = np.zeros_like(u0_upper)
    pert_surface = np.zeros_like(u0_surface)

    for n in range(1, N + 1):
        # 前 Nf 步加熱，之後關掉
        if n <= Nf:
            A_upper = u0_upper + pert_upper + heat
        else:
            A_upper = u0_upper + pert_upper
        A_surface = u0_surface + pert_surface   # 加熱只加在 T，地面場不變

        out_upper, out_surface = pangu_step(session, A_upper, A_surface)
        pert_upper   = out_upper   - B_upper
        pert_surface = out_surface - B_surface

        # 存 850hPa 的擾動 (u,v)，給畫圖用。850hPa = LEVELS index 2；u=upper[3], v=upper[4]
        u850 = pert_upper[3, 2]
        v850 = pert_upper[4, 2]
        np.save("output/pert_%03d.npy" % n, np.stack([u850, v850]).astype(np.float32))
        print("step %2d/%d  day %.2f  done" % (n, N, n * STEP_HOURS / 24.0))

    print("finished. 每步的 850hPa (u,v) 擾動存在 output/pert_XXX.npy")


if __name__ == "__main__":
    main()
