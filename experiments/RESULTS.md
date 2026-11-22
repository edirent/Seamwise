# Seamwise controlled circuit pilot

Completed configurations/backends: 136; completed paired HUF comparisons: 37.

HUF and SW are rebuilding/persistent modes of the same new Python HUF reference, inside the complete Seamwise repair1 wrapper. BPHUF/BPSW add the same specified BP-assisted residual preconditioning to those modes. They are not the original authors' HUF executable. Terminal canonicalization is performed in both modes. External baselines are native complete-record decoders. No result establishes SOTA.

| Configuration | Backend | Failures / shots | Mean ms | p95 ms | Sampled process RSS MiB |
|---|---|---:|---:|---:|---:|
| bb144_p0.005_B4 | BPHUF | 0/64 | 134.74 | 209.08 | 136.4 |
| bb144_p0.005_B4 | BPSW | 0/64 | 132.83 | 204.10 | 137.1 |
| bb144_p0.005_B4 | HUF | 2/64 | 224.01 | 376.17 | 126.5 |
| bb144_p0.005_B4 | LSD2 | 0/64 | 13.46 | 21.00 | 74.7 |
| bb144_p0.005_B4 | OSD2 | 0/64 | 959.25 | 1151.50 | 175.5 |
| bb144_p0.005_B4 | SW | 2/64 | 225.91 | 374.91 | 126.5 |
| bb144_p0.005_B4 | Tesseract | 0/64 | 14.75 | 19.29 | 117.4 |
| bb144_p0.015_B4 | BPHUF | 1/64 | 345.78 | 593.74 | 136.9 |
| bb144_p0.015_B4 | BPSW | 1/64 | 287.41 | 453.18 | 137.2 |
| bb144_p0.015_B4 | LSD2 | 8/64 | 208.61 | 932.35 | 77.3 |
| bb144_p0.015_B4 | Tesseract | 0/64 | 57.44 | 66.32 | 116.6 |
| bb72_p0.005_B4 | BPHUF | 1/64 | 36.41 | 73.11 | 101.3 |
| bb72_p0.005_B4 | BPSW | 1/64 | 35.26 | 66.58 | 100.8 |
| bb72_p0.005_B4 | HUF | 10/64 | 73.37 | 134.97 | 96.2 |
| bb72_p0.005_B4 | LSD2 | 3/64 | 6.39 | 7.64 | 71.7 |
| bb72_p0.005_B4 | OSD2 | 0/64 | 150.99 | 202.77 | 99.2 |
| bb72_p0.005_B4 | SW | 10/64 | 76.60 | 156.98 | 95.6 |
| bb72_p0.005_B4 | Tesseract | 0/64 | 4.66 | 7.10 | 104.8 |
| bb72_p0.015_B4 | BPHUF | 7/64 | 94.66 | 224.81 | 101.4 |
| bb72_p0.015_B4 | BPSW | 7/64 | 84.30 | 177.09 | 101.0 |
| bb72_p0.015_B4 | LSD2 | 25/64 | 20.86 | 100.11 | 72.6 |
| bb72_p0.015_B4 | OSD2 | 15/64 | 197.21 | 239.45 | 99.2 |
| bb72_p0.015_B4 | Tesseract | 0/64 | 18.14 | 24.03 | 104.9 |
| distance_surface_d11_p0.003_B4_T3 | BPHUF | 0/64 | 437.22 | 828.11 | 232.8 |
| distance_surface_d11_p0.003_B4_T3 | BPSW | 0/64 | 411.50 | 775.29 | 232.7 |
| distance_surface_d11_p0.003_B4_T3 | HUF | 0/64 | 631.55 | 1621.85 | 206.6 |
| distance_surface_d11_p0.003_B4_T3 | LSD2 | 0/64 | 35.00 | 41.53 | 82.5 |
| distance_surface_d11_p0.003_B4_T3 | SW | 0/64 | 600.47 | 1563.81 | 205.6 |
| distance_surface_d11_p0.003_B4_T3 | Tesseract | 0/64 | 260.44 | 283.04 | 148.5 |
| distance_surface_d5_p0.003_B4_T3 | BPHUF | 0/64 | 18.10 | 56.17 | 93.8 |
| distance_surface_d5_p0.003_B4_T3 | BPSW | 0/64 | 18.25 | 54.99 | 93.7 |
| distance_surface_d5_p0.003_B4_T3 | HUF | 0/64 | 43.65 | 80.66 | 89.5 |
| distance_surface_d5_p0.003_B4_T3 | LSD2 | 0/64 | 3.36 | 5.79 | 70.9 |
| distance_surface_d5_p0.003_B4_T3 | OSD2 | 0/64 | 37.06 | 71.83 | 105.8 |
| distance_surface_d5_p0.003_B4_T3 | SW | 0/64 | 43.72 | 85.16 | 89.5 |
| distance_surface_d5_p0.003_B4_T3 | Tesseract | 0/64 | 14.16 | 22.85 | 100.8 |
| distance_surface_d7_p0.003_B4_T3 | BPHUF | 1/64 | 215.13 | 153.29 | 127.1 |
| distance_surface_d7_p0.003_B4_T3 | BPSW | 1/64 | 150.82 | 147.05 | 126.9 |
| distance_surface_d7_p0.003_B4_T3 | HUF | 1/64 | 164.56 | 423.76 | 115.8 |
| distance_surface_d7_p0.003_B4_T3 | LSD2 | 0/64 | 11.15 | 21.27 | 73.6 |
| distance_surface_d7_p0.003_B4_T3 | OSD2 | 0/64 | 262.90 | 324.08 | 229.3 |
| distance_surface_d7_p0.003_B4_T3 | SW | 1/64 | 157.41 | 427.17 | 116.1 |
| distance_surface_d7_p0.003_B4_T3 | Tesseract | 0/64 | 52.98 | 136.33 | 107.9 |
| distance_surface_d9_p0.003_B4_T3 | BPHUF | 0/64 | 222.29 | 308.04 | 172.6 |
| distance_surface_d9_p0.003_B4_T3 | BPSW | 0/64 | 222.84 | 306.29 | 172.9 |
| distance_surface_d9_p0.003_B4_T3 | HUF | 0/64 | 319.30 | 507.54 | 154.5 |
| distance_surface_d9_p0.003_B4_T3 | LSD2 | 0/64 | 22.12 | 28.80 | 77.7 |
| distance_surface_d9_p0.003_B4_T3 | SW | 0/64 | 313.50 | 491.05 | 154.3 |
| distance_surface_d9_p0.003_B4_T3 | Tesseract | 0/64 | 91.74 | 177.31 | 119.0 |
| scale_surface_d3_p0.003_B16_T3 | BPHUF | 10/64 | 14.88 | 42.42 | 96.3 |
| scale_surface_d3_p0.003_B16_T3 | BPSW | 10/64 | 14.56 | 41.83 | 96.2 |
| scale_surface_d3_p0.003_B16_T3 | HUF | 50/64 | 42.16 | 59.52 | 89.6 |
| scale_surface_d3_p0.003_B16_T3 | LSD2 | 6/64 | 4.42 | 5.81 | 71.2 |
| scale_surface_d3_p0.003_B16_T3 | OSD2 | 3/64 | 76.74 | 110.48 | 120.8 |
| scale_surface_d3_p0.003_B16_T3 | SW | 50/64 | 46.62 | 63.84 | 90.1 |
| scale_surface_d3_p0.003_B16_T3 | Tesseract | 3/64 | 12.25 | 21.00 | 101.2 |
| scale_surface_d3_p0.003_B32_T3 | BPHUF | 17/64 | 31.77 | 66.05 | 124.0 |
| scale_surface_d3_p0.003_B32_T3 | BPSW | 17/64 | 33.86 | 75.53 | 123.9 |
| scale_surface_d3_p0.003_B32_T3 | HUF | 60/64 | 94.66 | 109.16 | 111.3 |
| scale_surface_d3_p0.003_B32_T3 | LSD2 | 25/64 | 10.63 | 13.32 | 74.2 |
| scale_surface_d3_p0.003_B32_T3 | OSD2 | 18/64 | 333.56 | 386.60 | 268.5 |
| scale_surface_d3_p0.003_B32_T3 | SW | 60/64 | 99.79 | 117.74 | 111.5 |
| scale_surface_d3_p0.003_B32_T3 | Tesseract | 5/64 | 29.73 | 58.38 | 107.6 |
| scale_surface_d3_p0.003_B4_T12 | BPHUF | 10/64 | 29.23 | 53.96 | 95.8 |
| scale_surface_d3_p0.003_B4_T12 | BPSW | 10/64 | 28.22 | 49.57 | 95.4 |
| scale_surface_d3_p0.003_B4_T12 | HUF | 47/64 | 31.47 | 38.11 | 89.9 |
| scale_surface_d3_p0.003_B4_T12 | LSD2 | 10/64 | 4.21 | 7.10 | 70.9 |
| scale_surface_d3_p0.003_B4_T12 | OSD2 | 4/64 | 61.19 | 83.05 | 112.7 |
| scale_surface_d3_p0.003_B4_T12 | SW | 47/64 | 32.61 | 39.70 | 90.2 |
| scale_surface_d3_p0.003_B4_T12 | Tesseract | 2/64 | 12.92 | 35.20 | 100.8 |
| scale_surface_d5_p0.003_B8_T10 | LSD2 | 10/64 | 46.94 | 82.51 | 84.5 |
| scale_surface_d5_p0.003_B8_T10 | Tesseract | 3/64 | 236.05 | 499.88 | 141.0 |
| scale_surface_d7_p0.003_B4_T14 | LSD2 | 4/64 | 72.20 | 106.07 | 90.7 |
| scale_surface_d7_p0.003_B4_T14 | Tesseract | 0/64 | 480.11 | 1463.40 | 165.6 |
| surface_d3_p0.001_B4 | BPHUF | 3/64 | 1.06 | 4.27 | 75.3 |
| surface_d3_p0.001_B4 | BPSW | 3/64 | 1.10 | 4.49 | 75.2 |
| surface_d3_p0.001_B4 | HUF | 7/64 | 6.36 | 19.36 | 73.8 |
| surface_d3_p0.001_B4 | LSD2 | 2/64 | 0.30 | 1.21 | 69.1 |
| surface_d3_p0.001_B4 | OSD2 | 2/64 | 1.04 | 6.86 | 72.8 |
| surface_d3_p0.001_B4 | SW | 7/64 | 6.49 | 19.35 | 73.7 |
| surface_d3_p0.001_B4 | Tesseract | 0/64 | 0.80 | 2.42 | 97.1 |
| surface_d3_p0.003_B4 | BPHUF | 2/64 | 1.99 | 6.91 | 75.6 |
| surface_d3_p0.003_B4 | BPSW | 2/64 | 2.05 | 6.99 | 75.4 |
| surface_d3_p0.003_B4 | HUF | 20/64 | 6.22 | 17.67 | 74.0 |
| surface_d3_p0.003_B4 | LSD2 | 2/64 | 0.39 | 1.29 | 69.0 |
| surface_d3_p0.003_B4 | OSD2 | 3/64 | 1.55 | 7.24 | 72.6 |
| surface_d3_p0.003_B4 | SW | 20/64 | 6.68 | 18.91 | 73.7 |
| surface_d3_p0.003_B4 | Tesseract | 2/64 | 2.15 | 8.39 | 97.1 |
| surface_d3_p0.003_B8 | BPHUF | 1/64 | 6.34 | 26.26 | 82.5 |
| surface_d3_p0.003_B8 | BPSW | 1/64 | 6.04 | 25.99 | 82.1 |
| surface_d3_p0.003_B8 | HUF | 31/64 | 16.95 | 28.51 | 79.2 |
| surface_d3_p0.003_B8 | LSD2 | 3/64 | 1.47 | 2.83 | 69.7 |
| surface_d3_p0.003_B8 | OSD2 | 3/64 | 12.81 | 26.39 | 82.7 |
| surface_d3_p0.003_B8 | SW | 31/64 | 16.40 | 27.69 | 78.9 |
| surface_d3_p0.003_B8 | Tesseract | 1/64 | 4.61 | 12.65 | 98.5 |
| surface_d3_p0.006_B4 | BPHUF | 8/64 | 5.29 | 26.55 | 75.9 |
| surface_d3_p0.006_B4 | BPSW | 8/64 | 5.03 | 22.98 | 75.4 |
| surface_d3_p0.006_B4 | HUF | 29/64 | 7.57 | 26.21 | 74.3 |
| surface_d3_p0.006_B4 | LSD2 | 6/64 | 0.91 | 1.79 | 69.1 |
| surface_d3_p0.006_B4 | OSD2 | 6/64 | 4.00 | 7.44 | 72.6 |
| surface_d3_p0.006_B4 | SW | 29/64 | 7.81 | 24.26 | 74.1 |
| surface_d3_p0.006_B4 | Tesseract | 3/64 | 6.46 | 15.16 | 97.3 |
| surface_d5_p0.001_B4 | BPHUF | 0/64 | 25.19 | 70.25 | 111.0 |
| surface_d5_p0.001_B4 | BPSW | 0/64 | 24.78 | 68.06 | 111.3 |
| surface_d5_p0.001_B4 | HUF | 0/64 | 58.71 | 90.73 | 103.2 |
| surface_d5_p0.001_B4 | LSD2 | 0/64 | 4.48 | 9.62 | 72.7 |
| surface_d5_p0.001_B4 | OSD2 | 0/64 | 79.00 | 184.06 | 162.9 |
| surface_d5_p0.001_B4 | SW | 0/64 | 58.07 | 85.04 | 103.9 |
| surface_d5_p0.001_B4 | Tesseract | 0/64 | 7.18 | 17.31 | 104.7 |
| surface_d5_p0.003_B4 | BPHUF | 0/64 | 50.72 | 96.54 | 110.9 |
| surface_d5_p0.003_B4 | BPSW | 0/64 | 49.29 | 99.36 | 111.6 |
| surface_d5_p0.003_B4 | HUF | 3/64 | 90.65 | 219.22 | 103.8 |
| surface_d5_p0.003_B4 | LSD2 | 2/64 | 6.71 | 11.40 | 72.7 |
| surface_d5_p0.003_B4 | OSD2 | 1/64 | 128.06 | 190.04 | 164.0 |
| surface_d5_p0.003_B4 | SW | 3/64 | 89.36 | 215.51 | 103.9 |
| surface_d5_p0.003_B4 | Tesseract | 1/64 | 44.44 | 84.64 | 106.6 |
| surface_d5_p0.003_B8 | BPHUF | 0/64 | 175.77 | 281.83 | 156.4 |
| surface_d5_p0.003_B8 | BPSW | 0/64 | 171.95 | 272.59 | 155.5 |
| surface_d5_p0.003_B8 | HUF | 8/64 | 268.80 | 511.87 | 139.4 |
| surface_d5_p0.003_B8 | LSD2 | 8/64 | 23.02 | 52.91 | 76.9 |
| surface_d5_p0.003_B8 | SW | 8/64 | 265.34 | 509.66 | 138.9 |
| surface_d5_p0.003_B8 | Tesseract | 1/64 | 96.14 | 258.87 | 116.4 |
| surface_d5_p0.006_B4 | BPHUF | 29/256 | 143.39 | 369.52 | 113.1 |
| surface_d5_p0.006_B4 | BPSW | 29/256 | 132.00 | 329.58 | 113.0 |
| surface_d5_p0.006_B4 | LSD2 | 47/256 | 15.05 | 47.81 | 73.2 |
| surface_d5_p0.006_B4 | Tesseract | 10/256 | 169.88 | 432.11 | 113.7 |
| surface_d7_p0.001_B4 | BPHUF | 0/64 | 199.53 | 361.28 | 204.2 |
| surface_d7_p0.001_B4 | BPSW | 0/64 | 200.09 | 345.01 | 204.7 |
| surface_d7_p0.001_B4 | HUF | 0/64 | 317.51 | 409.25 | 181.1 |
| surface_d7_p0.001_B4 | LSD2 | 0/64 | 20.66 | 32.31 | 80.0 |
| surface_d7_p0.001_B4 | SW | 0/64 | 304.08 | 388.15 | 180.4 |
| surface_d7_p0.001_B4 | Tesseract | 0/64 | 37.08 | 62.94 | 126.2 |
| surface_d7_p0.003_B4 | BPSW | 1/64 | 581.48 | 2239.80 | 206.0 |
| surface_d7_p0.003_B4 | LSD2 | 2/64 | 38.31 | 84.14 | 80.4 |
| surface_d7_p0.003_B4 | Tesseract | 0/64 | 223.43 | 728.37 | 126.8 |
| surface_d7_p0.006_B4 | LSD2 | 16/64 | 282.29 | 1351.54 | 82.2 |

## Interpretation

Paired output and merge-history equality is tested directly in paired_audit.json. Native/Python latency differences measure these implementations, not an implementation-independent algorithm ordering. Shared terminal canonicalization makes identical logical performance expected; a change in logical failure would indicate an implementation or policy mismatch.

All completed pilot failure rates have Wilson intervals in summary.csv. A zero count in 64 samples does not establish a zero true error rate. Failed or time-limited runs are NOT included as successful or zero-error runs. Partial journal prefixes are execution telemetry, not unbiased fidelity samples.

Original archived models use identical stored D/L, priors and samples in every backend; new scaling models use the recovered original generator with independently frozen seeds. These are distinct configurations, so a line joining them is not a fitted asymptotic exponent.

Latency is one warm pass per backend, without memory polling. Memory is a separate 1ms RSS-sampled pass over the first four inputs and includes the whole Python process, imported libraries, model and retained diagnostics. Startup, raw durations, output bitstrings, and cluster histories are retained. These are shared-host pilot measurements without three independent timing replicates or affinity isolation.

The primary 256-shot BPHUF/BPSW runs were preallocated 180 seconds per process. The first completed BB144 low-noise runs were allowed a 180-second process budget. After slow high-noise calls, subsequent child processes were capped at 45 seconds, before viewing their outcomes. This is a resource-budget amendment; raw logs retain non-completions. No outcome-dependent sample-count selection is used.

Tesseract (2025), native BP+LSD (published 2025), and stronger-order OSD are measured. Relay-BP was attempted but its native package could not build here (no compatible wheel/Rust toolchain). GARI (2026), ghost protocol (2026), logical-product/observable decoders and IRS remain unmeasured: their circuit/observable adapters have not been verified. They must not be shown as defeated baselines.

## Three-process replication and structural diagnostic

- bb144_p0.015_B4: median paired mean-latency reduction 17.9%; three randomized-order fresh-process runs on the same 64 inputs.
- surface_d5_p0.006_B4: median paired mean-latency reduction 8.0%; three randomized-order fresh-process runs on the same 64 inputs.

Eight-input BB144 diagnostic: 81,639 versus 3,100 basis insertion calls (26.3x fewer). This is a routine-call counter, not a measured word-operation count or end-to-end speedup. Root queries, component allocation and eligibility scans remain substantial in the saved profiles.

Whole-process RSS changes little between oracle modes. The first-64 primary timing repetitions make Tesseract faster than the persistent reference on that subset, while its full-256 mean is larger because the input set differs. These results do not support an unconditional performance ordering. See replication_summary.csv and full per-shot durations.
