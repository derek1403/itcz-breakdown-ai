# Repo 結構 — 中繼站 (tree.md)

本檔是專案結構的**中繼站**：只列關鍵 `.py / .md / config`（不含圖片與大型資料），
並指向每個資料夾自己的 `README.md`。**各部分的完整說明交給該資料夾的 README**，這裡只給一句用途 + 連結。

> 重新產生：
> ```bash
> tree --dirsfirst --noreport -P '*.py|*.md|*.yml|*.yaml|*.json' --prune \
>   -I '__pycache__|ref|ic|outputs|obs|data_raw|output|figs|full_run|vort_frames|.git'
> ```

---

## 頂層資料夾用途

| 路徑 | 用途 | 詳細 |
|------|------|------|
| `src/itcz/` | 主套件：資料處理 `data/`、模型 `models/`、實驗 `experiment/`、診斷 `plotting/` | 見 [README §4](README.md#4-code-map--完整結構見-treemd) |
| `scripts/` | thin CLI 入口：`prep_*`（建背景 IC）、`run_step{1..4}`（四步實驗，支援 `--exp <spec>`）、`resume_run`（延長/暖啟動任一 run）、`plot_*`（出圖） | 見 [README §3](README.md) |
| `ic/` | 產出的背景場 `u0_<bg>_<model>.npz`（大檔，不入 git） | — |
| `outputs/` | 依背景分組 `outputs/<bg>/`。**新 per-experiment layout**：`outputs/<bg>/<spec>/{config.yaml, step1..4}`（spec 名＝`<model><sh>_<heat>_<amp>Kday_<method>`）；JAS 已遷移，其餘背景仍為舊扁平 `step<N>_<model>_<bg>_...`。每個 stepN 內含 `pert_NNN.npz` + 圖 + `config_used.json` | 見 [README §8.1](README.md) |
| `obs/` | 觀測對照資料與說明 | [obs/README.md](obs/README.md) |
| `aux/` | 非主要部分歸檔（見下） | — |
| `aux/investigation/` | 排查與試錯的完整歷史（為何早期對不上 AI-Forum、逐項排除、最終在 `aiforum_repro/` 重現成功） | [aux/investigation/README.md](aux/investigation/README.md) |
| `aux/verification/` | 驗證 harness、圖與自己的 README（forcing ellipse、TCWV 一致性、operator 單步健全性） | [aux/verification/README.md](aux/verification/README.md) |
| `aux/tests/` | driver 數學 + locking 單元測試（mock operator，不載真模型） | — |
| `aux/related_paper/` | 參考文獻與原作設定圖（`AI-Forum.pdf`、`IC.png`、`horizontal_heating.png`） | — |
| `aux/pending_decisions/` | 尚待決策的事項與階段狀態 | [aux/pending_decisions/README.md](aux/pending_decisions/README.md) |
| `aux/data_raw/` | 下載的原始資料（1979 等；只讀不改） | — |

> `ic/ outputs/ obs/ aux/data_raw/ aux/investigation/ref/` 等大型資料/圖片目錄在下方骨架中**略去不展開**。

---

## 程式 / 文件骨架

```
.
├── aux
│   ├── investigation
│   │   ├── aiforum_repro                 # ✅ 成功重現 AI-Forum 的定案腳本（JAS/2.5K/Deep）
│   │   │   ├── 0_plot_heating_gauss.py
│   │   │   ├── 0_plot_heating.py
│   │   │   ├── 1_run_pangu_djf.py
│   │   │   ├── 1_run_pangu_gauss.py
│   │   │   ├── 1_run_pangu.py
│   │   │   ├── 2_plot_results.py
│   │   │   ├── config.yml
│   │   │   ├── panguweather_utils.py
│   │   │   ├── 歷程.md
│   │   │   └── 結果.md
│   │   ├── paper_heating
│   │   │   ├── 0_plot_heating.py
│   │   │   ├── 1_run_pangu.py
│   │   │   ├── 2_plot_results.py
│   │   │   ├── 3_plot_vorticity.py
│   │   │   ├── config.yml
│   │   │   ├── panguweather_utils.py
│   │   │   └── run_heating_exbl.py
│   │   ├── standalone                    # 可攜單檔腳本（h5→npy、跑 Pangu 加熱、畫渦度）
│   │   │   ├── 1_h5_to_npy.py
│   │   │   ├── 2_run_pangu_heating.py
│   │   │   └── 3_plot_vorticity.py
│   │   ├── ALGORITHM_AND_SETUP.md
│   │   ├── check_orientation.py
│   │   ├── compare_ic.py
│   │   ├── compare_smoothing.py
│   │   ├── FINDINGS_AND_EXPERIMENTS.md
│   │   ├── ic_smooth.py
│   │   ├── plot_2d_maps.py
│   │   ├── README.md
│   │   ├── refine_forcing.py
│   │   ├── replot_smoothed.py
│   │   ├── sweep_fcnv2_amp.py
│   │   ├── sweep_fcnv2_fast.py
│   │   ├── 進度報告0625_1450.md
│   │   ├── 進度報告0625_1545.md
│   │   ├── 進度報告0625_1700_垂直加熱.md
│   │   └── 進度報告0625_總整理.md         # 對外討論看這份大統整
│   ├── pending_decisions
│   │   ├── phase2_status.md
│   │   └── README.md
│   ├── tests
│   │   └── test_driver_math.py
│   └── verification
│       ├── data_integrity_JJA.md
│       ├── README.md
│       └── run_verification.py
├── scripts
│   ├── _bootstrap.py                     # 把 src/ 放上 sys.path
│   ├── build_remaining_backgrounds.py
│   ├── plot_background.py
│   ├── plot_run.py
│   ├── plot_vorticity_frames.py
│   ├── prep_annual.py
│   ├── prep_djf.py
│   ├── prep_enso.py
│   ├── prep_jas.py                       # ✅ validated headline IC（JAS）
│   ├── prep_jja.py
│   ├── prep_paper_djf.py
│   ├── prep_ragasa.py
│   ├── run_full_pipeline.py
│   ├── run_step1.py
│   ├── run_step2.py
│   ├── run_step3.py
│   ├── run_step4.py
│   └── resume_run.py                    # 延長/暖啟動任一 run（讀其 config_used.json，續跑到 --n_days）
├── src
│   └── itcz
│       ├── data
│       │   ├── __init__.py
│       │   └── prep.py                   # ERA5 -> model-IC
│       ├── experiment
│       │   ├── driver.py                 # Perpetual Background Re-centering；4-step 變體
│       │   ├── forcing.py                # 加熱（分離式 2D 高斯）+ 垂直分布 + 水氣強迫
│       │   └── __init__.py
│       ├── models
│       │   ├── vendor
│       │   │   ├── fourcastnetv2         # vendored SFNO net（權重外部讀取）
│       │   │   │   ├── activations.py
│       │   │   │   ├── contractions.py
│       │   │   │   ├── __init__.py
│       │   │   │   ├── layers.py
│       │   │   │   └── sfnonet.py
│       │   │   └── __init__.py
│       │   ├── __init__.py
│       │   ├── layout.py                 # State 容器 + 各模型通道排列、locking、q<->r、TCWV
│       │   └── operators.py              # Pangu(ONNX) & FCNv2(torch) -> M.step()
│       ├── plotting
│       │   ├── __init__.py
│       │   └── tracker.py                # 渦度/TCWV 診斷、渦旋追蹤、地圖、時間序列
│       ├── config.py
│       └── __init__.py
├── config.yaml                           # 所有路徑/參數（validated 預設：JAS/2.5K/Deep）
└── README.md
```
