# Execution checkpoint (2026-11-09)

User request is the full native research framework in attachment
`/home/edirent/.codex/attachments/067aca13-bca4-4a3e-9af4-1bf84d3d3bdb/Pasted text.txt`.
Continue autonomously; no subagents authorized. All original files in
`experiments/` and `manuscript/` must remain unchanged. Baseline/paper claims
must remain honest; do not turn nonconvergence, censoring, or exploratory timing
into scientific superiority.

New code is entirely in `seamwise_bench/`. Use `.venv/bin/python` (3.13), and
`scripts/seamwise-bench`, which sets OMP/BLAS/Rayon threads to one. Primary
benchmarks run sequentially pinned to CPU 0. Do not run builds, tests, or other
benchmark jobs concurrently with active measurement workers.

At this checkpoint the active job is validation, tool exec session **96109**.
Its log is `evidence/validation.log`; directory is
`results/20261109T192007Z-validation-a4186940`. It started 19:20 UTC and has a
predeclared 1,800-second total campaign budget. 108 planned jobs: six points per
family (Tesseract, LSD, OSD, Relay, Seamwise variants, GARI), three workloads,
128 shared validation shots. Each job caps preparation/decode separately.
Some strong Tesseract beam-50 points already timed out; keep every prefix.

Current authoritative dataset is
`results/20261109T191912Z-dataset-43f9bff8/manifest.json` (128 validation,
1,024 timing, 10,000 locked test per workload). Test labels have NOT been
opened. Old dataset `20261109T184703Z-dataset-c226b8eb` has retired exploratory
timing samples after its four-shot smoke influenced Relay diagnosis; see
`evidence/retired_timing_corpus.json`. Validation and test seeds are unchanged.

Successful all-six-backend smoke is
`results/20261109T191925Z-validation-f96f703d`, log `smoke_validation.log`.
An earlier performance smoke stopped correctly on Relay nonconvergence and is
retained in `results/20261109T191616Z-timing-54395d09`.

Native core: C++20 complete growth/BP/cut/fallback/repair/cost/frame path;
union-by-size with canonical minimum public labels, incidence-driven missing
edge accounting, incremental boundary symmetric difference, sparse support-local
basis/witnesses, fixed reference terminal solve, optional packed local terminal.
Current build has exact contiguous-message BP. `build_v1` and `build_v2` preserve
previous binaries/source archives. Native tests: 1,968 exhaustive/random cases,
plus 100 flat-vs-official BP LLR checks; ASan/UBSan/leak checks pass. Python
contracts currently eight passed, and a new separate model-equivalence fixture
has been added but should be run after validation. Fidelity includes exact
corrections, repair decisions, growth sizes, and semantic merge IDs via a derived
in-memory oracle; original reference files are untouched. Latest gate is PASS,
`results/20261109T191112Z-fidelity-a9398148`.

Official external builds are installed:
- Tesseract commit `54569b4af741423708922a1c033feb483fc034c1`, Bazel `-c opt`,
  portable wheel, ancestry to optimization PRs 25/34/57 verified. Initial
  fastbuild took 927s; explicit opt rebuild 443s. Original upstream wheel's
  manylinux_2_42 tag was correctly retagged local linux_x86_64 (host glibc 2.39).
- Relay commit `cdfdc996ce55582c4c431f8d8392bcce57175e36`, native Rust release.
  PyPI 0.2.2 lacks per-decode RNG reset; current official source includes it.
  Both original/source wheels are preserved. Fixed deterministic ensemble
  restart is explicit. Low effort can return `success=False`; validation logs
  this separately from implementation bugs and excludes invalid points.
- LDPC 2.4.1 headers match PyPI source. F64 normalized min-sum, .625, parallel,
  30 iterations for exact port; stronger iteration/order/schedules in validation.
- GARI unmodified official C kernel, separate `_gari` binding. Exact augmented
  graph/D/L/prior map verified (unique X/Z projections and logical XOR images).
  Full-graph and two correlated-sector stopping adaptations labeled; both
  sectors retain ALL detector evidence/joint priors. Two-sector ensembling is
  sequential `2*ensemble` kernel calls on one core. BB144 nonconvergence remains
  severe even strong settings; retain negative results and exclude failed
  correction points from publication timing. Do not claim generic GARI defeat.

Audit outputs: original 1,065-file hashes, historical manifest verification,
small saved-output reproduction, 24-circuit exact noise factorization proof,
provenance matrices/logs in `evidence/`; `audit.md` and README explain boundaries.
Old profile data are diagnostic. Native v2 profiles (`*profiles*`) identify BP as
dominant (~72% gprof BB144), motivating contiguous BP. Need profile current
compiled revision separately before final report.

Scaling preparation is complete in
`results/20261109T190227Z-scaling-c07d24f0`: 30 unique models, 5 aliases, 24 old
anchors, 6 large proportional-depth stress cases deferred. All B={2..64},
d={3..15} fixed T, T={3,6,12,24} fixed logical layers, logical layers independent
of T, and BB72/144 are represented. 16 circuit-sampled exploratory validation
shots per prepared scaling model. Scaling decode measurements still needed.

Outstanding work after validation:
1. Inspect all validation records. Fix `scripts/select_validation.py` to choose
   fastest quality-eligible baseline within each family (not merely minimum
   failure count then latency); preserve strongest quality reference separately
   if needed. Handle missing/nonconvergent/timed-out families explicitly.
2. Estimate CPU hours from actual validation. Full 10k/7-repeat matrix with slow
   OSD/Relay can exceed 4h cap. Predeclare feasible final primary/deferred jobs
   BEFORE opening test. Preserve fixed N=10k, every excluded job/reason, exact
   remaining commands and measured CPU-hour estimates. Do not silently shrink N
   or claim strongest-baseline victory if comparison remains incomplete.
3. One justified fairness improvement to implement after validation: rebuild
   currently calls `Basis::merge` even though it immediately reconstructs at the
   end of the growth event. Skip merging discarded pivot/witness state in rebuild
   mode, retaining inserted-column ownership; test exact outputs. Preserve
   current build as v3 and add v3-v4 ablation. Also finish native capacity metrics
   (current payload omits BP arrays), and optional diagnostic detector/fault/
   incidence cluster sizes. Do not edit C++ while a fidelity process is running.
4. Before long runs, strengthen analysis guards for model/sample hashes and
   actual binary fingerprints across jobs/repetitions; record external binary
   fingerprints per worker, not nominal version alone. Validate allowed Python
   reference families/iteration count (the frozen oracle is only HUF/BPHUF30).
5. Build/fidelity/contracts after any native change; native sanitizer current v3
   passes. Run `scripts/historical_regression.py` on old outputs (budget 600s)
   and keep all unavailable historical cases explicit.
6. Execute engineering (`configs/engineering.yaml`, 128 timing IDs x3, clearly
   exploratory), optimization controls, method ablation, native primary timing
   (1,024 IDs x7), feasible independent fixed-N accuracy, fresh-worker full timing
   corpus memory/soak pass, and scaling pilot. No concurrent benchmark jobs.
7. Freeze before final: CLI freeze works with dataset manifest + final config and
   `selection_record`; run accepts resulting frozen campaign manifest and rejects
   code/config drift. Source hash includes all Python files under python/;
   postprocessing scripts can be authored under scripts/ without changing it.
8. Analyze, generate RESULTS.md, short Chinese memo, Pareto/scaling/cluster plots,
   final source/dependency locks, all stage ledgers, and self-contained archive
   with integrity hashes. Verify every original hash again. No memory-folder
   writes (user did not ask for memory update).

Expected conclusions must answer separately S_port, S_persist, eligible S_frontier,
p99/memory/accuracy/service tradeoffs, and actual 2025-26 backend status. Relative
noninferiority margin is 10%, paired simultaneous exact-cell bounds. Rare/zero
counts remain insufficient precision/inconclusive. No threshold/deadline claim.
