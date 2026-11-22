# Seamwise native framework: measured results

Original data and manuscript files are unchanged. All measurements are from the same virtualized host, one pinned CPU / decoder thread, batch one; no bare-metal claim. Completed, deferred, failed and partial jobs remain distinct.


## Correctness and provenance gates

The native suite passed 1,968 exhaustive/seeded cases, including 100 exact flat-versus-official BP LLR/iteration comparisons. The final C++ source passed ASan/UBSan/leak checks; 11 Python/model/adapter/watchdog contracts passed. Differential gates require exact corrections, repair decisions and semantic growth IDs, with reversed/shuffled/reset/fresh-worker checks. Independent test rebuild/persistent outputs also match exactly on all 30,000 circuit IDs across the three workloads. See `evidence/postcampaign_integrity.json`: frozen decoder sources and the native module stayed identical through timing, accuracy and the repaired memory pass. Installed official Tesseract/Relay binary members match their pinned local source wheels byte-for-byte (`evidence/installed_official_wheel_equivalence.json`).


## Engineering port

On 128 shared validation IDs per workload and three fresh processes, the equal-workload geometric means are **9.247x** for Python rebuild / native rebuild and **9.885x** for Python persistent / native persistent. Exact correction hashes match. These are exploratory implementation measurements; they exceed the 2x-5x engineering target on this declared cohort. Persistence is measured separately.


| Mode | Workload | Python mean ms | Native mean ms | S_port |
| --- | --- | --- | --- | --- |
| rebuild | bb144_p0.015_B4 | 300.8 | 20.61 | 14.59 |
| rebuild | surface_d3_p0.003_B4 | 2.054 | 0.3388 | 6.062 |
| rebuild | surface_d5_p0.006_B4 | 78.1 | 8.736 | 8.94 |
| persistent | bb144_p0.015_B4 | 210.8 | 11.82 | 17.83 |
| persistent | surface_d3_p0.003_B4 | 1.968 | 0.3208 | 6.136 |
| persistent | surface_d5_p0.006_B4 | 73.01 | 8.269 | 8.829 |


Hierarchical aggregate 95% intervals: rebuild [8.473249994945478, 9.99591998109126], persistent [8.8723898056189, 10.913606371708397]. Simultaneous 98.33% intervals across the three engineering aggregates: rebuild [8.365013223319194, 10.291846072342898], persistent [8.664852464555468, 11.242146734759032]. Workload identities remain fixed, with equal weights; sample IDs and fresh-process repetitions are resampled.



## Native persistence ablation

Prepared-online `S_persist = T_native_rebuild / T_native_persistent`, with the same graph frontend, BP, scheduling, compiler flags, full-witness oracle contract and canonical terminal solve, is **1.207x** geometrically across the full three-workload set. The independent timing corpus has 1,024 IDs and seven fresh process repetitions. It does not add 7,168 independent accuracy samples.


| Workload | S_persist | Pointwise 95% bootstrap interval |
| --- | --- | --- |
| bb144_p0.015_B4 | 1.483 | [1.406, 1.564] |
| surface_d3_p0.003_B4 | 0.9876 | [0.9732, 1.005] |
| surface_d5_p0.006_B4 | 1.201 | [1.138, 1.283] |


Aggregate 95% interval: [1.1761664271437147, 1.2411341145053867]; simultaneous 98.33% interval: [1.173702683256971, 1.2480713205841556]. A ratio below one is a regression. The selected full-method point can use a different repair policy (BB144 repair2); it is not substituted into the repair1 persistence ablation.



| Workload | Backend | Mean ms | Median ms | p95 ms | p99 ms | Max ms |
| --- | --- | --- | --- | --- | --- | --- |
| bb144_p0.015_B4 | native_rebuild | 17.15 | 12.62 | 37.28 | 87.54 | 278.2 |
| bb144_p0.015_B4 | tuned_tesseract | 48.39 | 46.25 | 62.17 | 97.31 | 533.5 |
| bb144_p0.015_B4 | native_persistent | 11.57 | 11.2 | 15.53 | 19.37 | 35.53 |
| bb144_p0.015_B4 | seamwise_selected | 16.29 | 15.46 | 22.75 | 29.84 | 68.89 |
| surface_d3_p0.003_B4 | seamwise_selected | 0.2836 | 0.068 | 1.008 | 1.284 | 1.794 |
| surface_d3_p0.003_B4 | native_rebuild | 0.2828 | 0.06716 | 1.01 | 1.277 | 1.969 |
| surface_d3_p0.003_B4 | native_persistent | 0.2864 | 0.06833 | 1.018 | 1.297 | 1.644 |
| surface_d5_p0.006_B4 | native_persistent | 8.273 | 8.293 | 11.67 | 15.9 | 31.06 |
| surface_d5_p0.006_B4 | native_rebuild | 9.936 | 8.498 | 17.15 | 48.01 | 254.3 |
| surface_d5_p0.006_B4 | seamwise_selected | 8.322 | 8.322 | 11.84 | 15.82 | 28.24 |


| Workload | Persistent/rebuild mean | Persistent/rebuild p99 | Observed mean regression | Observed p99 regression |
| --- | --- | --- | --- | --- |
| bb144_p0.015_B4 | 0.6743 | 0.2212 | False | False |
| surface_d3_p0.003_B4 | 1.013 | 1.015 | True | True |
| surface_d5_p0.006_B4 | 0.8327 | 0.3312 | False | False |


These descriptive regression flags compare pooled latency estimators; they are not individual significance tests. Per-repetition p99 values and hierarchical p99 intervals are retained separately.



## Independent accuracy and frontier gates

Fixed requested N is 10,000 circuit shots per workload, with disjoint validation, timing and test streams. Logical failure is any observable disagreement. Invalid corrections/service failures are separate. Wilson intervals, paired discordance tables and conservative simultaneous exact-cell bounds are retained in analysis.json. The relative noninferiority margin is **10%**, not identical accuracy; strict equality-target bounds are also saved. No finite failure-rate ratio is inferred from two zero counts.


| Workload | Backend | N | Logical failures | Invalid/service | Rate | Wilson 95% | Precision planning |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bb144_p0.015_B4 | native_rebuild | 10000 | 43 | 0 | 0.0043 | [0.003194, 0.005787] | INSUFFICIENT_PRECISION |
| bb144_p0.015_B4 | tuned_tesseract | 10000 | 0 | 0 | 0 | [0, 0.000384] | INSUFFICIENT_PRECISION |
| bb144_p0.015_B4 | native_persistent | 10000 | 43 | 0 | 0.0043 | [0.003194, 0.005787] | INSUFFICIENT_PRECISION |
| bb144_p0.015_B4 | seamwise_selected | 10000 | 42 | 0 | 0.0042 | [0.003109, 0.005672] | INSUFFICIENT_PRECISION |
| surface_d3_p0.003_B4 | native_rebuild | 10000 | 480 | 0 | 0.048 | [0.04398, 0.05237] | PLANNING_TARGET_REACHED |
| surface_d3_p0.003_B4 | native_persistent | 10000 | 480 | 0 | 0.048 | [0.04398, 0.05237] | PLANNING_TARGET_REACHED |
| surface_d3_p0.003_B4 | tuned_tesseract | 10000 | 131 | 0 | 0.0131 | [0.01105, 0.01552] | INSUFFICIENT_PRECISION |
| surface_d3_p0.003_B4 | seamwise_selected | 10000 | 480 | 0 | 0.048 | [0.04398, 0.05237] | PLANNING_TARGET_REACHED |
| surface_d5_p0.006_B4 | native_persistent | 10000 | 1265 | 0 | 0.1265 | [0.1201, 0.1332] | PLANNING_TARGET_REACHED |
| surface_d5_p0.006_B4 | native_rebuild | 10000 | 1265 | 0 | 0.1265 | [0.1201, 0.1332] | PLANNING_TARGET_REACHED |
| surface_d5_p0.006_B4 | seamwise_selected | 10000 | 1265 | 0 | 0.1265 | [0.1201, 0.1332] | PLANNING_TARGET_REACHED |
| surface_d5_p0.006_B4 | tuned_tesseract | 10000 | 313 | 0 | 0.0313 | [0.02806, 0.0349] | INSUFFICIENT_PRECISION |


The observed selected Seamwise / frozen Tesseract logical-failure counts are bb144_p0.015_B4: **42 / 0**, surface_d3_p0.003_B4: **480 / 131**, surface_d5_p0.006_B4: **1265 / 313**. Every completed point uses the same 10,000 circuit IDs within its workload. These negative quality results remain part of the main result.



Secondary prepared-online timing from the complete fixed-N accuracy pass follows. It has one fresh process per point and a different corpus from the seven-repetition primary timing experiment; it does not replace that experiment or establish an eligible frontier speedup.

| Workload | Backend | Secondary mean ms | Secondary p99 ms |
| --- | --- | --- | --- |
| bb144_p0.015_B4 | native_rebuild | 18.3 | 87.63 |
| bb144_p0.015_B4 | tuned_tesseract | 46.64 | 75.75 |
| bb144_p0.015_B4 | native_persistent | 11.27 | 18.85 |
| bb144_p0.015_B4 | seamwise_selected | 15.72 | 29.72 |
| surface_d3_p0.003_B4 | native_rebuild | 0.2838 | 1.295 |
| surface_d3_p0.003_B4 | native_persistent | 0.2756 | 1.26 |
| surface_d3_p0.003_B4 | tuned_tesseract | 1.995 | 10.63 |
| surface_d3_p0.003_B4 | seamwise_selected | 0.2863 | 1.341 |
| surface_d5_p0.006_B4 | native_persistent | 7.913 | 15.91 |
| surface_d5_p0.006_B4 | native_rebuild | 9.924 | 57.69 |
| surface_d5_p0.006_B4 | seamwise_selected | 8.199 | 16.46 |
| surface_d5_p0.006_B4 | tuned_tesseract | 873.1 | 1.401e+04 |


| Workload | 10% quality gate | Eligible reference speed ratio |
| --- | --- | --- |
| bb144_p0.015_B4 | QUALITY_NOT_ESTABLISHED | UNAVAILABLE |
| surface_d3_p0.003_B4 | QUALITY_NOT_ESTABLISHED | UNAVAILABLE |
| surface_d5_p0.006_B4 | QUALITY_NOT_ESTABLISHED | UNAVAILABLE |


No overall strongest-native frontier advantage is asserted. Validation used the official optimized Tesseract build, LDPC BP-LSD/BP-OSD, current official Relay-BP, and the official GARI C kernel with a verified task-specific augmentation. Deferred operating points and incomplete tuning trials remain unresolved rather than counted as defeats. A raw latency ratio cannot repair a failed/inconclusive quality gate.



## Memory, tails and execution reliability

The table separates process baseline, preparation residency, high-water RSS and completed memory audits. The full independent timing corpus has 1,024 shots; allocation requests and independent/repeated-syndrome soaks cover that corpus in separate instrumented passes. This is not a 10,000-shot accuracy-corpus memory claim. Requested allocation bytes are not live bytes; native owned-capacity payloads exclude allocator overhead and some third-party ownership. Memory failures do not erase committed decode results.


| Workload | Backend | Status | Baseline RSS bytes | Prepared RSS bytes | High-water RSS bytes | Full audit available |
| --- | --- | --- | --- | --- | --- | --- |
| bb144_p0.015_B4 | native_rebuild | COMPLETE | 62672896 | 81735680 | 84881408 | True |
| bb144_p0.015_B4 | tuned_tesseract | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| bb144_p0.015_B4 | native_persistent | COMPLETE | 62648320 | 81653760 | 85061632 | True |
| bb144_p0.015_B4 | tuned_osd | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| bb144_p0.015_B4 | tuned_lsd | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| bb144_p0.015_B4 | tuned_gari | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| bb144_p0.015_B4 | tuned_relay | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| bb144_p0.015_B4 | seamwise_selected | COMPLETE | 62672896 | 84344832 | 88801280 | True |
| surface_d3_p0.003_B4 | tuned_relay | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d3_p0.003_B4 | tuned_gari | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d3_p0.003_B4 | native_rebuild | COMPLETE | 62439424 | 63488000 | 65777664 | True |
| surface_d3_p0.003_B4 | native_persistent | COMPLETE | 62590976 | 63115264 | 65777664 | True |
| surface_d3_p0.003_B4 | tuned_lsd | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d3_p0.003_B4 | tuned_tesseract | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d3_p0.003_B4 | tuned_osd | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d3_p0.003_B4 | seamwise_selected | COMPLETE | 62357504 | 63143936 | 65777664 | True |
| surface_d5_p0.006_B4 | tuned_lsd | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d5_p0.006_B4 | native_persistent | COMPLETE | 62607360 | 71782400 | 73879552 | True |
| surface_d5_p0.006_B4 | native_rebuild | COMPLETE | 62664704 | 71839744 | 73936896 | True |
| surface_d5_p0.006_B4 | tuned_relay | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d5_p0.006_B4 | seamwise_selected | COMPLETE | 62410752 | 71585792 | 73945088 | True |
| surface_d5_p0.006_B4 | tuned_osd | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d5_p0.006_B4 | tuned_gari | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |
| surface_d5_p0.006_B4 | tuned_tesseract | UNSUPPORTED | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | False |


| Workload | Backend | Prepared owned payload bytes | Workspace owned payload bytes | Requests / corpus | Requested bytes / corpus | RSS span across 3 soak checkpoints |
| --- | --- | --- | --- | --- | --- | --- |
| bb144_p0.015_B4 | native_rebuild | 8239264 | 8538896 | 91740084 | 4654607244 | 0 |
| bb144_p0.015_B4 | native_persistent | 8239264 | 8538828 | 6625205 | 1456294572 | 0 |
| bb144_p0.015_B4 | seamwise_selected | 9398496 | 10466440 | 9210697 | 2445972164 | 0 |
| surface_d3_p0.003_B4 | native_rebuild | 981768 | 837696 | 122726 | 14617232 | 0 |
| surface_d3_p0.003_B4 | native_persistent | 981768 | 837700 | 94466 | 14112004 | 0 |
| surface_d3_p0.003_B4 | seamwise_selected | 981768 | 837700 | 94466 | 14112004 | 0 |
| surface_d5_p0.006_B4 | native_persistent | 6157456 | 5447458 | 1924667 | 635070364 | 0 |
| surface_d5_p0.006_B4 | native_rebuild | 6157456 | 5447458 | 37785530 | 1496715624 | 0 |
| surface_d5_p0.006_B4 | seamwise_selected | 6157456 | 5447458 | 1924667 | 635070364 | 0 |


Revision allocation controls on the full 128-ID engineering validation corpus: {'COMPLETE': 27}. Their independently instrumented requests, capacities and soak RSS are in `results/20261110T051814Z-memory-a16b7d22/analysis.json`; they are not final latency measurements.



The first final memory run (`20261110T050626Z-memory-5cc48225`) retains nine startup crashes before decoding. Dynamic TLS lookup in the diagnostic malloc hooks was replaced with initial-exec TLS; the known-allocation calibration (3 requests, 140 bytes, 2 explicit frees) and native-extension import pass are retained. This changed only memory instrumentation. The decoder source/binary, frozen policies and samples remained the same for the fresh memory rerun. Counters cover allocation requests on the calling decoder thread and do not report live allocated bytes. Deferred rows marked UNSUPPORTED at the budget-deferral stage do not mean the backend API is unavailable.



Mean and p99 must be assessed per workload from the timing table; no universal tail or memory improvement is inferred from a mean speedup. No per-shot real-time deadline experiment was run. Bulk job timeouts, missing outputs and logical miscorrections have different meanings.



## Validation, scaling and remaining comparisons

Validation ledger: {'COMPLETE': 80, 'DECODE_TIMEOUT': 28}. All 36 method-ablation jobs completed on the same 64 validation IDs per workload, spanning joint/cut/halo/repair with HUF reference, BP-assisted reference and official native LSD families. All 63 initial implementation-control jobs and the additional rebuild-fairness controls completed. See their raw analysis and per-shot files.



The 28 validation DECODE_TIMEOUT ledger entries comprise seven actual decode timeouts and 21 trials not launched after the 1,800-second stage cap. Their stage labels distinguish these cases; unlaunched trials are not measured baseline defeats.



Same-family method ablation: each failure count has denominator 64 validation circuit shots; timing is one process and exploratory. HUF/BPHUF are reference variants, LSD is the verified native LDPC family. Different policy outputs do not qualify as exact implementation optimizations. This small cohort does not establish an independent-test advantage.

| Workload | Local family | Joint failures | Cut failures | Halo1 failures | Repair1 failures | Joint mean ms | Repair1 mean ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bb144_p0.015_B4 | bphuf | 1 | 0 | 1 | 0 | 9.024 | 11.74 |
| bb144_p0.015_B4 | huf | 62 | 61 | 60 | 60 | 96.6 | 81.29 |
| bb144_p0.015_B4 | lsd | 5 | 7 | 8 | 5 | 191.4 | 100.4 |
| surface_d3_p0.003_B4 | bphuf | 3 | 3 | 1 | 2 | 0.3584 | 0.3588 |
| surface_d3_p0.003_B4 | huf | 17 | 17 | 17 | 17 | 0.0295 | 0.04387 |
| surface_d3_p0.003_B4 | lsd | 3 | 6 | 4 | 4 | 0.6357 | 0.5915 |
| surface_d5_p0.006_B4 | bphuf | 12 | 17 | 17 | 11 | 6.603 | 8.175 |
| surface_d5_p0.006_B4 | huf | 19 | 26 | 23 | 24 | 2.273 | 1.981 |
| surface_d5_p0.006_B4 | lsd | 20 | 13 | 17 | 12 | 21.74 | 22.3 |


Scaling measurements and actual N_det/N_fault/incidence/depth/gate counts are in results/20261110T050635Z-validation-7a1015e3/scaling_results.json. These are 16-shot exploratory controls, not threshold evidence. Large proportional-depth stress workloads are explicitly deferred.



Historical audit: 1065 original files unchanged; 5184 correction-identical stored-shot executions across 75 available groups. Missing historical outputs remain unavailable. The old primary BP-assisted point still has 29/256 logical failures in both modes. Reused historical executions add zero independent accuracy samples.



## Measured limiting work

Separate 32-shot validation diagnostic passes retain stage intervals and native gprof call graphs. BP remains the dominant measured work. Fractions below use the sum of native cut/repair/frame wrapper intervals; they exclude Python binding and instrumentation overhead outside those intervals. Nested local stages cannot be added again to wrapper totals.

| Workload | Mode | BP fraction of wrapper intervals | Insertion calls / 32 shots | Root queries / 32 shots | Terminal ms / 32 shots | Ideal bound if all non-BP work vanished |
| --- | --- | --- | --- | --- | --- | --- |
| bb144_p0.015_B4 | rebuild | 0.6422 | 270047 | 325557 | 3.451 | 1.557 |
| bb144_p0.015_B4 | persistent | 0.8109 | 10700 | 325557 | 5.459 | 1.233 |
| surface_d3_p0.003_B4 | rebuild | 0.9168 | 197 | 3821 | 0.06962 | 1.091 |
| surface_d3_p0.003_B4 | persistent | 0.9169 | 138 | 3821 | 0.06585 | 1.091 |
| surface_d5_p0.006_B4 | rebuild | 0.8081 | 85686 | 132718 | 1.292 | 1.237 |
| surface_d5_p0.006_B4 | persistent | 0.8847 | 3206 | 132718 | 1.566 | 1.13 |


These are wrapper-only Amdahl bounds for this diagnostic cohort with BP held fixed; they are not full binding/API bounds or performance forecasts. In particular, the small measured terminal-solve fraction cannot explain a further 2x-5x whole-path gain. New BP/local-solver/repair policies would require a separately frozen accuracy evaluation.



The canonical terminal solve remains in production. Oracle-only canonical-basis investigations, if present, are not native speed claims. Packed terminal, prior revisions, stage/gprof profiles, operation counts and cluster distributions are retained independently. Neither feasible witnesses nor cost descent prove maximum likelihood or the correct logical class.



The finite canonical-basis exchange oracle passed 10216 systems. Naive activation-order witnesses differed from the frozen canonical correction in 1637 cases; exchanges reproduced it in the tested consistent cases. This is an investigation, not a native integrated optimization or a proof of minimum-likelihood decoding.



Completed primary timing, fixed-N accuracy and successful memory workers used 3.174 CPU hours against the predeclared four-hour confirmatory cap. Builds, exploratory controls, gprof and postprocessing have separate budgets/scopes; this is not a four-hour claim for the entire project. See `evidence/compute_accounting.json` for stage records and the failed memory-startup wall cost.



Reconstructed final non-singleton component CDFs, merge-weighted CDFs, per-circuit-shot maxima, terminal rank lists and difficult-shot diagnostic strata are retained under the current profile run (`*_final_components.json`, `*_component_weighted_cdf.png`, `*_runtime_clusters.png`). Aggregate local histories cannot identify every component with its individual circuit shot; that missing map is explicitly labeled, while per-shot maxima and failed-call counts are preserved. Native gprof latency and separate audit-pass sizes provide an explanatory association, not a release-latency fit or near-linearity claim.



## Reproduction and remaining work

[README.md](README.md) gives the build and frozen-run commands; [audit.md](audit.md) records adapter/provenance limits. The run-to-artifact mapping is [evidence/run_index.json](evidence/run_index.json). Additional lifecycle estimates, amortization crossover, p99 hierarchical intervals, exact revision controls, current native profiles, scaling plots and validation-only mean-latency-budget envelopes are in evidence/ and the indexed runs. Validation envelopes use 1/10/100/1000 ms mean budgets and are descriptive; they do not establish test-set superiority or per-shot deadline reliability.

Exact deferred continuation commands and validation-throughput CPU-hour estimates are in [REMAINING.md](REMAINING.md). Nonconvergent Relay/GARI points require a new validation gate before publication timing; their uncompleted tuning grid cannot be counted as a loss. The final source/data/results archive is `artifacts/seamwise_native_research_20261109.tar.gz`, with member integrity hashes and a sibling archive SHA256. Environment caches and VCS object databases are excluded; original source/data/manuscript files are included unchanged.

