# Full-pipeline run report

**0 failed stage(s)** out of 15.


- background: **JJA**, n_days: **16**, amp: **10.0 K/day Deep**, models: ['pangu', 'fcnv2']
- cpu_num: -1 (resolved to all cores)

## Stage status

| stage | status | minutes | detail |
|---|---|---|---|
| prep_JJA | OK | 30.3 |  |
| load_operator[pangu] | OK | 0.4 |  |
| pangu/step1 | OK | 60.4 |  |
| pangu/step2 | OK | 64.6 |  |
| pangu/seed | OK | 0.1 |  |
| pangu/step3 | OK | 67.2 |  |
| pangu/step4 | OK | 55.5 |  |
| pangu/compare_fig | OK | 7.8 |  |
| load_operator[fcnv2] | OK | 0.4 |  |
| fcnv2/step1 | OK | 37.2 |  |
| fcnv2/step2 | OK | 38.0 |  |
| fcnv2/seed | OK | 0.2 |  |
| fcnv2/step3 | OK | 35.6 |  |
| fcnv2/step4 | OK | 31.6 |  |
| fcnv2/compare_fig | OK | 7.9 |  |

## Comparison figures

### pangu
![pangu](compare_pangu.png)
Step 1 should grow; Step 2 (moisture lock) should be suppressed.

### fcnv2
![fcnv2](compare_fcnv2.png)
Step 1 should grow; Step 2 (moisture lock) should be suppressed.

## Per-run outputs

Each run dir under `outputs/` holds `pert_NNN.npz`, `panels_vort.png`, `panels_tcwv.png`, `timeseries.png`, `config_used.json`.
