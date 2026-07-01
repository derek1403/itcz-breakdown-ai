# obs/ — Observational evidence of ITCZ / monsoon-trough breakdown (HIMAWARI 00Z)

Real-satellite counterparts of the project's modelled **barotropic ITCZ breakdown** — an
elongated ITCZ/monsoon-trough vorticity strip rolling up into a chain of discrete cyclonic
vortices. These support the Pangu repro in
`investigation/aiforum_repro/figs/vort_JAS_Deep_amp2.5.png`, where the 850 hPa ζ′ band along
~8–15°N evolves from **~2 vortices + a vorticity band (day 9)** into **~4 discrete vortices
(day 15)** that drift WNW and poleward over ~6 days.

Source: **PCCU / ASRAD HIMAWARI full-disk catalog** (the site the user linked). Full-disk HIMAWARI
covers the **West/Central Pacific (~80–200°E)**, which is exactly the model domain, so every case
here is a **WPac monsoon-trough breakdown**. Imagery is **water vapour (`fdk_wvp`)** combined with
**IR (`fdk_ir1_mb`)** as a WV|IR composite — IR matching the GOES-IR approach of
Nieto Ferreira & Schubert (1997).

## Events (ranked)

### ★ `2024-11_WPac_quad-typhoon/` — 5–14 Nov 2024 (PRIMARY)
**Four typhoons lined up** (Yinxing, Toraji, Usagi, Man-yi) — the cleanest 2→4 roll-up of the
period; first November on record (since 1951) with four coexisting WPac TCs; NASA EPIC imaged all
four on 11 Nov. Key 00Z days **7 → 9 → 11 → 13 Nov** map onto model day 9 → 12 → 15.
Best single figure: `rollup_IR_Nov06-13.jpg`. See its `EVENT.md`.

### `2023-09_WPac_triple-plus/` — 30 Aug – 6 Sep 2023 (SECONDARY)
Active monsoon trough breaking into **Saola + Haikui + Kirogi** (+ Yun-yeung forming east).
Simultaneous multi-vortex breakdown, but more N–S spread. See its `EVENT.md`.

## Per-event contents
- `EVENT.md` — narrative, dated vortex list, model-day mapping, exact re-crawl URLs, references.
- `rollup_IR_*.jpg` — cropped tropical-WPac IR montage (the roll-up at a glance).
- `composite_YYYYMMDD.png` — per-key-day **WV | IR** side-by-side, cropped & labelled.
- `evolution_*` — full-disk daily montage (Nov 2024 WV).
- `fulldisk/YYYYMMDD_00Z_{wv,ir}.jpg` — raw 00Z full-disk jpgs.

## ASRAD URL pattern (verified, downloads anonymously)
```
https://asrad.pccu.edu.tw/catalog/sslsat/{YYYY}/{MM}/{DD}/{YYYYMMDD}_{HHMM}.sslsat.{PRODUCT}.jpg
```
- `HHMM` = `0000` for 00Z (10-min cadence available; fall back to 0010/0050 if a slot is missing).
- `PRODUCT` ∈ `fdk_wvp` (water vapour), `fdk_ir1_mb` (IR colour), `fdk_ir1_gry` (IR grey),
  `fdk_vis_gry` (visible). `fdk_` = full disk; `lcc_` = regional (Lambert) crops also exist.
- Archive verified available **2020–2026**.

## Reproduce
Fetch + montage helpers used to build this folder live in the session scratchpad
(`fetch.py`, `crop_montage.py`, `build_obs.py`); the crop box for the tropical WPac is
`(120,280,820,575)` on the 1024×1024 disk. Re-run with any date window / product to extend.

## References
- Guinn, T. A., and W. H. Schubert, 1993: Hurricane spiral bands. *J. Atmos. Sci.*, **50**, 3380–3403.
- Nieto Ferreira, R., and W. H. Schubert, 1997: Barotropic aspects of ITCZ breakdown. *J. Atmos. Sci.*, **54**, 261–285.
- Wang, C.-C., and G. Magnúsdóttir, 2005/2006: ITCZ breakdown — 3-D flows & observed (QuikSCAT) cases.
