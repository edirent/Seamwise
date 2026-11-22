# Prepared-online latency and memory

Primary publication timing uses the independent 1024-ID timing corpus, three fresh processes per configuration, one pinned core (CPU0 on this host), one decoder thread and batch1. Backend order is randomized and saved, with identical per-repetition shot permutations. Warmup uses the same 16 validation syndromes. The clock covers prepared input detector bits through returned logical frame, including Python/native interface and intrinsic decoder work; it excludes model/data loading, preparation, external validity/truth scoring, JSON journals and diagnostics. Source/binary/dependency fingerprints are verified for every phase. No decoder/build/profiler benchmark was run concurrently with these sequential timing workers.

The original native binary is unchanged. Memory instrumentation runs in separate fresh workers with explicit instrumented scope. Accuracy-corpus single-pass timings remain auxiliary, never substituted for missing dedicated timing measurements. Tesseract enters dedicated timing only on workloads that met the frozen validation point-estimate 10% screen (BB144); that screen is not the independent noninferiority test. Its d3/d5 auxiliary timings are retained without an accuracy-qualified speed claim.

| Workload | Decoder | Mean ms | Median ms | p95 ms | p99 ms | Maximum ms |
|---|---|---:|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | original | 0.242392 | 0.055125 | 0.926769 | 1.18342 | 1.4376 |
| surface_d3_p0.003_B4 | selected_combined | 1.17059 | 1.02521 | 2.1922 | 2.98956 | 6.20564 |
| surface_d5_p0.006_B4 | original | 7.52725 | 7.60044 | 10.4379 | 14.8835 | 21.6603 |
| surface_d5_p0.006_B4 | selected_combined | 56.0275 | 63.5872 | 77.4725 | 86.619 | 120.428 |
| bb144_p0.015_B4 | selected_combined | 3.94175 | 3.12481 | 10.1359 | 12.7783 | 32.1621 |
| bb144_p0.015_B4 | baseline_tesseract | 46.0717 | 44.6628 | 62.052 | 76.0627 | 215.311 |
| bb144_p0.015_B4 | original | 15.4817 | 14.6054 | 22.5395 | 30.0897 | 67.3439 |

| Workload | Selected/original mean ratio | Pointwise 95% paired hierarchical bootstrap |
|---|---:|---|
| surface_d3_p0.003_B4 | 4.829 | 4.422–5.268 |
| surface_d5_p0.006_B4 | 7.443 | 7.119–7.777 |
| bb144_p0.015_B4 | 0.2546 | 0.2305–0.2839 |

Ratios use shared sample IDs and resample process blocks plus independent shot IDs (600 bootstrap draws). They describe timing variability for this host, not an accuracy test or a production deadline guarantee. Full process means, p99s, preparation times and maxima are in `latency_memory_analysis.json`. Severe tail or mean regressions remain visible. Fixed K≤16, depth≤2, ≤128 cached moves, and ≤2 conditional solver calls bound added search; the implementation does not hide uncontrolled/exhaustive search in timing. Initialization/fallback BP calls are additional and explicitly outside the repair-call cap.

## Separate memory and soak

Each original/selected pair uses all 512 validation IDs, followed by two cycles of the full independent corpus and 512 repetitions of one fixed syndrome per cycle: 2560 total decode calls per process including the initial 512-ID pass. This stresses reset/reuse but is not a long-duration stability guarantee. Resident pages include interpreter, imported libraries, samples and allocator arenas; RSS changes are not exact decoder ownership. Native capacity values count the implemented owned payload categories, not every allocator or object header. The candidate dense payload is a lower estimate, not a measured peak total. Joint-policy preparation retains duplicated conditional storage and is reported as implemented.

The unchanged calibrated glibc interposer counts calling-thread allocation requests during each full-corpus decode; it does not count every Python allocator event or report live bytes. Instrumentation overhead is excluded from all publication latency.

| Workload | Decoder | Status | Baseline RSS MiB | Prepared RSS MiB | HWM MiB | Owned prepared/workspace payload MiB | Requests/call (mean) | Requested KiB/call (mean) | Soak RSS MiB |
|---|---|---|---:|---:|---:|---|---:|---:|---|
| surface_d3_p0.003_B4 | original | COMPLETE | 108 | 108.5 | 109.7 | 0.9363/0.7881 | 95.72 | 13.74 | 108.7/108.7 |
| surface_d3_p0.003_B4 | selected_combined | COMPLETE | 108.1 | 108.8 | 109.8 | 0.9187/0.8493 | 1717 | 849.2 | 109.1/109.1 |
| surface_d5_p0.006_B4 | original | COMPLETE | 108.7 | 116.5 | 117.7 | 5.872/5.058 | 1668 | 561.4 | 117.7/117.7 |
| surface_d5_p0.006_B4 | selected_combined | COMPLETE | 108.7 | 123.9 | 142.7 | 7.068/7.403 | 1.156e+04 | 3.301e+04 | 142.7/142.7 |
| bb144_p0.015_B4 | selected_combined | COMPLETE | 112.2 | 128.1 | 129.2 | 8.963/8.218 | 71.38 | 127.8 | 128.8/128.8 |
| bb144_p0.015_B4 | original | COMPLETE | 112.5 | 128.4 | 132.2 | 8.963/10.06 | 9283 | 2495 | 131.9/132.2 |

## Uninstrumented primary-worker resident memory

These are fresh accuracy workers on the full fixed primary corpus, not decoder-owned allocation totals and not the separate 512-ID instrumented soak. The interrupted Tesseract attempt is excluded; the complete fixed-N retry is used. Interpreter, data and library residency are included. For an accuracy-only checkpoint continuation, whole-cohort high-water RSS is UNAVAILABLE; resume-process RSS is preserved separately in its raw summary.

| Workload | Decoder | Baseline / prepared / high-water RSS MiB |
|---|---|---|
| surface_d3_p0.003_B4 | original | 109.18/109.93/110.93 |
| surface_d3_p0.003_B4 | baseline_tesseract | 111.73/112.23/112.48 |
| surface_d3_p0.003_B4 | selected_combined | 110.04/110.79/112.04 |
| surface_d5_p0.006_B4 | original | 113.85/121.6/123.35 |
| surface_d5_p0.006_B4 | baseline_tesseract | 118.73/129.98/UNAVAILABLE |
| surface_d5_p0.006_B4 | selected_combined | 114.29/129.54/148.5 |
| bb144_p0.015_B4 | baseline_tesseract | 152.05/169.3/171.8 |
| bb144_p0.015_B4 | selected_combined | 149.8/165.46/166.55 |
| bb144_p0.015_B4 | original | 149.46/165.16/168.91 |

Full memory raw allocation requests, independent/repeated cycle sizes, candidate payload lower estimates and RSS checkpoints are retained per worker. A small number of soak checkpoints cannot establish the absence of slow leaks. Any failed audit is labeled separately and cannot invalidate an already atomically committed decode journal.

## Computation budget

Frozen forecast: 4.005 hours; maximum 5 wall hours (a conservative cap for sequential one-core CPU work). Supervisor elapsed: 4.73 hours. Per-stage paths/statuses, missing counts and parent-watchdog events are in `P4_run_index.json` and the execution ledger. Completed jobs were retained; an interrupted job was retried with the same fixed configuration and IDs as documented below, without outcome-based selection.


Execution recovery: three complete primary jobs were retained from the initial execution. The interrupted 3188-ID Tesseract prefix remains unchanged and is excluded as an independent estimate; the exact same configuration was retried on all fixed 8000 IDs. If a later stage watchdog left another incomplete Tesseract attempt, the budget-only completion rule can continue its remaining fixed IDs in a fresh process after exact checkpoint replay checks; this retains one unique result per ID and is excluded from dedicated timing. Duplicate predictions were crosschecked and never increase N. An estimated 46.6 minutes of prior active execution are charged to the five-hour planning cap; the offline interruption is excluded. The old worker termination time and uncommitted in-flight work were not recorded, so this is accounted active time with a 30-second allowance, not a certified upper bound on all historical CPU work. The resumed supervisor itself enforces its remaining wall cap. Configuration/source/binary/data locks did not change. Accuracy-run timings across execution dates are auxiliary; dedicated timing is measured entirely in fresh paired workers after recovery. See evidence/P4_recovery_plan.json and recovery_prediction_crosscheck.json.
