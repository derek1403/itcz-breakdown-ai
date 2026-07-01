# Full-pipeline run report

**0 failed stage(s)** out of 14.


- background: **DJF**, n_days: **16**, amp: **10.0 K/day Deep**, models: ['pangu', 'fcnv2']
- cpu_num: -1 (resolved to all cores)

## Stage status

| stage | status | minutes | detail |
|---|---|---|---|
| load_operator[pangu] | OK | 0.5 |  |
| pangu/step1 | OK | 67.1 |  |
| pangu/step2 | OK | 61.9 |  |
| pangu/seed | OK | 0.1 |  |
| pangu/step3 | OK | 65.3 |  |
| pangu/step4 | OK | 63.9 |  |
| pangu/compare_fig | OK | 8.1 |  |
| load_operator[fcnv2] | OK | 0.5 |  |
| fcnv2/step1 | OK | 42.0 |  |
| fcnv2/step2 | OK | 42.1 |  |
| fcnv2/seed | OK | 0.1 |  |
| fcnv2/step3 | OK | 40.7 |  |
| fcnv2/step4 | OK | 36.2 |  |
| fcnv2/compare_fig | OK | 8.1 |  |

## Comparison figures

### pangu
![pangu](compare_pangu.png)
Step 1 should grow; Step 2 (moisture lock) should be suppressed.

### fcnv2
![fcnv2](compare_fcnv2.png)
Step 1 should grow; Step 2 (moisture lock) should be suppressed.

## Per-run outputs

Each run dir under `outputs/` holds `pert_NNN.npz`, `panels_vort.png`, `panels_tcwv.png`, `timeseries.png`, `config_used.json`.
