# Seamwise: controlled oracle ablation and circuit-scaling pilot

This archive contains real saved circuit/noise samples, code, raw outcomes, measured durations, process-memory data, and full cluster histories. The manuscript treats the persistent conditional oracle as part of Seamwise. No separate method brand is needed. Related external work remains cited. Nothing in this archive establishes unconditional SOTA.

## Reproduce

Experiments require Linux/WSL with `/proc` and SIGALRM; the paper compiles independently in Overleaf. Install Python 3.12 dependencies: numpy, scipy, matplotlib, stim==1.16.0, ldpc==2.4.1, tesseract-decoder==0.1.1.dev20261102041404. Exact installed versions and source hashes are in environment.json.

- `python run.py --child MODEL HUF 64`: rebuilding reference HUF inside full repair1.
- `python run.py --child MODEL SW 64`: persistent conditional HUF inside the identical wrapper.
- `python run.py --child MODEL Tesseract 64`: native full-record Tesseract.
- `python run.py --child MODEL LSD2 64`: native full-record BP+LSD, combination-sweep order 2.
- `python run.py --child MODEL OSD2 64`: native full-record BP+OSD, combination-sweep order 2.
- `python run.py --suite`: sequential pilot across all included configurations; primary d5,p=.006 requests 256 shots.
- `python summarize.py`: verify matched output/merge traces, produce summary.csv, paired_audit.json, RESULTS.md and scaling plots.

Child processes have a 45-second total budget. The first low-noise BB144 measurements preceded this budget amendment and had a 180-second limit. Run logs and partial JSONL journals remain available. Partial prefixes are NOT used for unbiased logical-failure estimates. The fixed requested sample count is not selected based on logical outcomes.

## Input provenance

The data and research generator were recovered from Boundary_Repair_Reproducibility_v2.zip, version 3 (Library id libfile_95131ac5ea1881919a5992adc68f3716). Original D/L, priors, full circuit DEMs, and samples were copied without modification. Per-run matrix/sample hashes identify exact reuse. New `scale_` models were generated with the original `research/models.py` circuit construction, preserving its noise rules and Bell observables. Their seed/model descriptions are in each model.json.

## Interpret correctly

`HUF` is a newly authored reference implementation of the stated weighted boundary-growth rule, not the original authors' software. `SW` changes only the local oracle to merge-persistent algebra. Both use identical deterministic terminal canonicalization. Therefore identical logical performance is the intended exact-oracle control, not evidence that persistence improves decoding accuracy. These references have no BP-assisted weighting and use Python global bitsets, full component scans, and retained diagnostic histories. They are not optimized native decoders.

Latency includes each complete repair call (cut, fallback, local solving, acceptance) for HUF/SW. Native external methods decode the complete joint detector record. Setup is separate, one warmup is excluded, and timing has no memory polling. Memory is whole-process RSS sampled separately every 1ms on the first four inputs, not backend-only live storage. Native code vs Python and process/import overhead make performance comparisons implementation-specific. This pilot has one timing pass, not three independent repetitions.

Tesseract returns logical observables through the measured interface. Its logical failures are directly scored, but the stored `invalid` field is not a syndrome-certificate audit for that observable-only interface; summary.csv records it as unavailable. HUF and LDPC correction vectors are syndrome audited.

Relay-BP installation was attempted but unavailable without a compatible wheel/Rust toolchain. GARI, ghost, logical-product decoding and IRS are relevant additional baselines; no adapter for them was validated in this run. Do not label these as measured or defeated. The 2026 baseline requirement remains incomplete.

See RESULTS.md for completed data and measured limitations. Raw measurements should govern the paper's positioning, including negative and censored results.

## BP-assisted oracle control

`BPHUF` and `BPSW` are an additional, explicitly specified residual-HUF variant. The same 30-iteration native BP runs first; a converged BP correction returns directly. Otherwise its posterior hard decision is removed from the syndrome, absolute posterior log-odds set nonnegative growth costs, and terminal columns are ordered by those costs. The rebuilding and persistent modes then solve the same residual system and restore that hard decision. This is a new reference variant, not a claim of reproducing every implementation detail of the published belief-HUF software. `python run_bp_suite.py` runs these two modes sequentially after the main suite.

Cluster-history limitation: intermediate histories of infeasible local initialization calls are not retained. Their elapsed time remains inside the measured complete repair call, but the cluster CDF covers only recorded completed solver calls (including feasible fallbacks and BP early exits). Do not interpret it as an exhaustive distribution over all attempted calls.

## Timing replication and diagnostics

After both suites finish, `python run_repeats.py` runs three independently initialized, sequential randomized-order timing replicates of BPHUF, BPSW and Tesseract on the first 64 primary-case inputs and the 64 high-noise BB144 inputs. This deliberately reuses inputs: it adds timing replication, not independent logical-accuracy samples. The primary 256-shot BP-oracle runs have a preallocated 180-second budget. `python profile_reference.py` performs a separate cProfile structural-work diagnostic on eight fixed high-noise BB144 inputs in BP-assisted mode; its instrumented times are never substituted for uninstrumented benchmark durations.

The process budget includes setup, warmup, the timed sample pass, and the separate memory pass. A missing final summary can therefore result from interruption during memory instrumentation even after some or all timed inputs completed; it is not a declaration of decoding infeasibility. All per-shot journals are retained for that distinction.
