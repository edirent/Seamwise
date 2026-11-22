# P2 BP and stronger-solver validation

New independent validation inputs, first 128 of the fixed 512-ID validation stream. These are tuning results, not confirmatory accuracy. Original and default-config copied native corrections must match exactly.

| Workload | Point | Failures /128 | Invalid | Mean ms | p99 ms |
|---|---|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | band_osd2 | 4 | 0 | 0.7594 | 4.343 |
| surface_d3_p0.003_B4 | band_lsd2 | 4 | 0 | 0.5091 | 2.83 |
| surface_d3_p0.003_B4 | baseline_tesseract | 3 | 0 | 1.872 | 11.03 |
| surface_d3_p0.003_B4 | baseline_gari | 1 | 1 | 0.2533 | 7.253 |
| surface_d3_p0.003_B4 | bp_norm05 | 4 | 0 | 0.66 | 2.946 |
| surface_d3_p0.003_B4 | bp_norm08 | 7 | 0 | 0.3096 | 1.811 |
| surface_d3_p0.003_B4 | baseline_relay | 2 | 0 | 0.3241 | 2.706 |
| surface_d3_p0.003_B4 | baseline_lsd | 1 | 0 | 7.091 | 38.52 |
| surface_d3_p0.003_B4 | baseline_osd | 2 | 0 | 1.94 | 7.283 |
| surface_d3_p0.003_B4 | original | 4 | 0 | 0.254 | 1.136 |
| surface_d3_p0.003_B4 | bp_damp08 | 3 | 0 | 0.2783 | 2.025 |
| surface_d3_p0.003_B4 | bp_norm10 | 6 | 0 | 0.3349 | 2.274 |
| surface_d3_p0.003_B4 | band_osd0 | 4 | 0 | 0.4928 | 2.584 |
| surface_d3_p0.003_B4 | bp_reference | 4 | 0 | 0.2727 | 1.413 |
| surface_d3_p0.003_B4 | bp_serial | 1 | 0 | 6.969 | 49.46 |
| surface_d3_p0.003_B4 | bp_iter60 | 6 | 0 | 0.4571 | 2.253 |
| surface_d3_p0.003_B4 | bp_norm08_30 | 9 | 0 | 0.1959 | 1.142 |
| surface_d5_p0.006_B4 | bp_serial | 14 | 0 | 420.6 | 575.3 |
| surface_d5_p0.006_B4 | bp_norm10 | 24 | 0 | 16.24 | 24.46 |
| surface_d5_p0.006_B4 | band_osd0 | 22 | 0 | 16.02 | 22.58 |
| surface_d5_p0.006_B4 | baseline_osd | 12 | 0 | 385.5 | 482.6 |
| surface_d5_p0.006_B4 | band_lsd2 | 21 | 0 | 15.83 | 26 |
| surface_d5_p0.006_B4 | baseline_lsd | 14 | 0 | 254.1 | 338 |
| surface_d5_p0.006_B4 | bp_damp08 | 19 | 0 | 14.93 | 25.83 |
| surface_d5_p0.006_B4 | bp_norm08 | 16 | 0 | 17.01 | 29.88 |
| surface_d5_p0.006_B4 | original | 21 | 0 | 7.485 | 14.54 |
| surface_d5_p0.006_B4 | bp_reference | 21 | 0 | 9.932 | 18.97 |
| surface_d5_p0.006_B4 | baseline_tesseract | 7 | 0 | 604.3 | 5059 |
| surface_d5_p0.006_B4 | bp_norm05 | 18 | 0 | 19.94 | 27.36 |
| surface_d5_p0.006_B4 | bp_iter60 | 22 | 0 | 18.93 | 24.13 |
| surface_d5_p0.006_B4 | bp_norm08_30 | 18 | 0 | 8.978 | 14.53 |
| bb144_p0.015_B4 | baseline_lsd | 11 | 0 | 142.5 | 668.7 |
| bb144_p0.015_B4 | bp_reference | 0 | 0 | 18.57 | 38.6 |
| bb144_p0.015_B4 | bp_serial | 0 | 0 | 32.93 | 109.8 |
| bb144_p0.015_B4 | bp_norm08 | 0 | 0 | 27.42 | 35.07 |
| bb144_p0.015_B4 | baseline_osd | 17 | 0 | 19.24 | 40.26 |
| bb144_p0.015_B4 | bp_damp08 | 0 | 0 | 3.608 | 11.96 |
| bb144_p0.015_B4 | band_osd0 | 1 | 0 | 37.23 | 65.69 |
| bb144_p0.015_B4 | band_lsd2 | 1 | 0 | 154.6 | 701.1 |
| bb144_p0.015_B4 | original | 0 | 0 | 15.76 | 36.65 |
| bb144_p0.015_B4 | bp_norm10 | 0 | 0 | 22.49 | 32.85 |
| bb144_p0.015_B4 | bp_norm05 | 0 | 0 | 16.91 | 31.71 |
| bb144_p0.015_B4 | baseline_tesseract | 0 | 0 | 46.98 | 72.38 |
| bb144_p0.015_B4 | bp_norm08_30 | 0 | 0 | 16.04 | 23.61 |
| bb144_p0.015_B4 | bp_iter60 | 0 | 0 | 31.74 | 44.69 |

Bit-serial is the official LDPC variable-serial update, not a falsely labeled check-layered implementation. The additional parallel 60-iteration control isolates iteration from schedule; the 30-iteration normalization08 control isolates scale. The damped implementation matches an independent ordered-message reference exactly on finite-LLR fixtures; official serial LLRs also match exactly. Native ASan/UBSan/leak tests exercise damped and serial syndrome/reset cases.

No graph representation, mechanism priors or observable map was changed. Existing GARI remains a separately audited exact augmentation; unsupported/uncompleted operating points are not counted as defeated. Multi-start candidate proposals and adaptive repair are a subsequent bounded stage, justified by P0/P1 search/selection evidence and the remaining P2 validation errors.
