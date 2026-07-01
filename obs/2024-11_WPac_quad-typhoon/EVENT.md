# Observed ITCZ / monsoon-trough breakdown — West Pacific, 5–14 November 2024

**The "four typhoons in a row" event** — the clearest 2020–2026 HIMAWARI analog of the model's
barotropic 2→4 vortex roll-up (`investigation/aiforum_repro/figs/vort_JAS_Deep_amp2.5.png`,
day 9 → day 15).

In early–mid November 2024 the West Pacific monsoon trough / near-equatorial convergence band
broke down into **four discrete tropical-cyclone vortices** strung W–E along ~13–18°N. The
Japan Meteorological Agency noted it was the **first time since records began in 1951** that four
named tropical cyclones coexisted in the basin in November; NASA's EPIC/DSCOVR imaged all four
simultaneously near **00:55 UTC on 11 Nov 2024**.

## The four vortices (W → E along the trough)
| Storm | PAGASA name | Position ~11 Nov 00Z | Notes |
|-------|-------------|----------------------|-------|
| **Yinxing** | Marce | ~17°N 115°E (SCS) | hit N. Philippines 7 Nov, weakening over the SCS, dissipated ~12 Nov |
| **Toraji** | Nika | ~17°N 122°E (Luzon) | compact eye, landfall NE Luzon 11 Nov |
| **Usagi** | Ofel | ~14°N 130°E | rapidly intensified to **super typhoon** by 13 Nov |
| **Man-yi** | Pepito | ~13°N 145°E | intense eye, later struck the Philippines ~17 Nov |

## Day-by-day roll-up (00Z) — maps onto the model
Search/Read band: tropical WPac **~108–163°E, 0–25°N** (crop box of the 1024² full disk = `(120,280,820,575)`).

| Date 00Z | Observed state | Model analog |
|----------|----------------|--------------|
| 6–7 Nov | Yinxing (SCS) + a disorganised monsoon-trough convective band east of the Philippines → **~2 incipient vortices + band** | ~ day 9 |
| 8–9 Nov | band discretises; Yinxing + Toraji + Usagi (forming) → **~3 vortices** | ~ day 12 |
| **10–11 Nov** | **four discrete cyclonic vortices lined up** along ~13–18°N (Yinxing, Toraji, Usagi, Man-yi) | **~ day 15** |
| 12–14 Nov | vortices march WNW and **drift poleward** while intensifying (Usagi → super typhoon) | post day-15 |

This is the real-atmosphere counterpart of barotropic **vortex roll-up** of an elongated
ITCZ/monsoon-trough vorticity strip into a chain of discrete vortices
(Guinn & Schubert 1993; Nieto Ferreira & Schubert 1997; Wang & Magnúsdóttir 2005, 2006).

## Files
- `composite_20241107.png`, `composite_20241109.png`, `composite_20241111.png`, `composite_20241113.png` — per-key-day **WV | IR** side-by-side (cropped WPac, labelled).
- `rollup_IR_Nov06-13.jpg` — 8-panel cropped IR montage showing the full 2→4 roll-up (**money figure**).
- `evolution_WV_Nov04-16.jpg` — 13-panel full-disk WV evolution.
- `fulldisk/YYYYMMDD_00Z_{wv,ir}.jpg` — raw 00Z full-disk HIMAWARI jpgs, 5–14 Nov (WV `fdk_wvp`, IR colour `fdk_ir1_mb`).

## Source & how to re-crawl (PCCU / ASRAD HIMAWARI catalog)
URL pattern (verified, downloads anonymously):
```
https://asrad.pccu.edu.tw/catalog/sslsat/{YYYY}/{MM}/{DD}/{YYYYMMDD}_{HHMM}.sslsat.{PRODUCT}.jpg
```
`HHMM=0000` for 00Z; products `fdk_wvp` (water vapour), `fdk_ir1_mb` (IR colour),
`fdk_ir1_gry` (IR grey), `fdk_vis_gry` (visible). Full 10-min cadence is available.
Exact key-day links:
- 11 Nov WV: `https://asrad.pccu.edu.tw/catalog/sslsat/2024/11/11/20241111_0000.sslsat.fdk_wvp.jpg`
- 11 Nov IR: `https://asrad.pccu.edu.tw/catalog/sslsat/2024/11/11/20241111_0000.sslsat.fdk_ir1_mb.jpg`
- (swap the date `2024/11/DD` + `20241111` for 07/09/13 Nov.)

## References
- Guinn, T. A., and W. H. Schubert, 1993: Hurricane spiral bands. *J. Atmos. Sci.*, **50**, 3380–3403.
- Nieto Ferreira, R., and W. H. Schubert, 1997: Barotropic aspects of ITCZ breakdown. *J. Atmos. Sci.*, **54**, 261–285.
- Wang, C.-C., and G. Magnúsdóttir, 2005/2006: ITCZ breakdown in three-dimensional flows / observed cases (QuikSCAT). *J. Atmos. Sci.* / *Mon. Wea. Rev.*
- NASA Earth Observatory, "Typhoons Line Up in the Western Pacific" (11 Nov 2024 EPIC/DSCOVR image).
