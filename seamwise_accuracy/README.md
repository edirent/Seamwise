# Seamwise logical failure and decoder accuracy study

This is a separate extension of the sealed native benchmark. The original
`seamwise_bench/`, historical `experiments/`, and manuscript are read-only inputs.
The previous 10,000-shot results are now exploratory. New data, diagnostics,
policies, builds, journals, and reports are all under this directory.

Start with [the Chinese research decision](results/RESEARCH_DECISION_ZH.md),
[accuracy](results/ACCURACY_RESULTS.md), [latency/memory](results/LATENCY_RESULTS.md),
and [the frontier](results/PARETO_FRONTIER.png). The quantitative causal evidence
is [failure diagnosis](results/failure_attribution/FAILURE_DIAGNOSIS.md),
[final certificates and intervals](results/failure_attribution/FINAL_ATTRIBUTION.md),
[identical-conditioned-system comparison](results/SOLVER_COMPARISON.md), and
[policy ablation](results/POLICY_ABLATION.md).

The online path remains native C++20, with partitioned initialization,
syndrome-preserving conditional boundary repair, validated selection and logical
frame construction. Python generates data, prepares model-only nullspace moves,
orchestrates fresh workers and scores results offline. Ground-truth faults or
observables are not decoder inputs. The bounded exact solver is an offline
research oracle only. There is no claim that a bounded candidate-class sum is
exact MAP, or that improving the old decoder proves an accuracy-matched advantage
over Tesseract.

## Dependencies and builds

The sibling sealed framework provides official LDPC headers, verified baseline
adapters, native original decoder, pinned official Tesseract/Relay wheels, model
files, and the Python 3.13 environment. Its archive is
`seamwise_bench/artifacts/seamwise_native_research_20261109.tar.gz`, SHA256
`b1f668676e8ae8fda59c8d98596e6c931d05745fe1638d6d3af2c7686d99e3a1`.
Read its README for the original source/wheel installation. This study only added
OR-Tools and its new dependencies; it did not upgrade the existing numerical or
baseline packages. The complete final package inventory is
`evidence/requirements_accuracy.lock`; provenance and exact shared-library hashes
are recorded in `configs/confirmatory_lock.json` and each worker summary.

From the parent directory on the recorded Linux/Python platform:

```bash
seamwise_bench/.venv/bin/python -m pip install -r seamwise_accuracy/evidence/requirements_accuracy.lock
# Preserve the pinned official-source wheel overrides from the old README.
cmake -S seamwise_accuracy -B seamwise_accuracy/build_prod \
  -DCMAKE_BUILD_TYPE=Release \
  -DPython_EXECUTABLE="$PWD/seamwise_bench/.venv/bin/python" \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build seamwise_accuracy/build_prod --parallel 1
ACCURACY_NATIVE_BUILD=build_prod \
  seamwise_bench/.venv/bin/python -m pytest seamwise_accuracy/tests -q
cmake -S seamwise_accuracy -B seamwise_accuracy/build_sanitize \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DACCURACY_SANITIZE=ON \
  -DPython_EXECUTABLE="$PWD/seamwise_bench/.venv/bin/python"
cmake --build seamwise_accuracy/build_sanitize --target accuracy_tests --parallel 1
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 \
  seamwise_accuracy/build_sanitize/accuracy_tests
```

Rebuilding in the delivered recorded directory changes binaries and can break the
immutable execution lock. Prefer `scripts/reproduce_frozen.py` below for an
isolated reproduction. Production uses O3, no fast math, and no FP contraction.
The audit build/P0 binary snapshot is separate and must not be replaced with a
later policy build when replaying historical P0 traces. Sanitizer logs and native
BP/reference tests are correctness evidence, never headline timing.

## Frozen data and experiment structure

`results/new_samples/manifest.json` records full circuit/model hashes and independent
Stim seeds for 512 validation, 1024 timing and 10000 potential confirmatory shots
per primary workload. The actual primary N was fixed at 8000 by validation-only
throughput planning before any confirmatory label access; the fixed component
prefix has 2000 IDs. All original correlated mechanism columns, whole observable
maps and priors are retained. There was no graph transformation.

`configs/confirmatory_lock.json` fixes all policies, sample counts, five-hour cap,
planned comparison count, sources, model-only pool manifest, binaries, and runtime
provenance. Its `first_confirmatory_access: null` and the dataset manifest's
`test_labels_opened: false` describe creation-time state. Actual access is recorded
per confirmatory worker in `truth_access.json`, with the lock hash and UTC time.
Do not edit creation-time manifests to retrospectively describe completion.

Raw outcomes are under the phase paths in `results/P4_run_index.json`. Every job
has a fixed configuration, randomized saved schedule, shot-level latency/failure
journal, correction digest, binary/version hashes, summary, and stdout/error log.
Memory jobs have an explicit instrumented scope and independent raw allocation
and RSS records. The root `results/EXECUTION_LEDGER.json` consolidates all jobs and
stages; its original append-only stage events are retained separately in
`STAGE_EXECUTION_LEDGER.json`. Failed/ineligible baseline attempts and intentional
orchestration failure tests remain visible. Missing jobs are not defeated decoders.

P0/P1 per-shot evidence is at the run paths in
`results/failure_attribution/current_run.json` and
`results/solver_comparison/current_run.json`, including
`failure_oracle_results.jsonl`, native growth supports, exact GF(2) certificates,
quantized optimization bounds, P1 positive witnesses and category intersections.
These diagnostic shots are deliberately stratified, so the refined report uses
finite-population stratum weights and wide exact intervals. Search/exposure/cost
labels overlap and do not identify a unique universal failure cause.

## Reproduction and analysis

The main scripts, in execution order, are:

1. `prepare_data.py`, `run_p0.py`, `report_p0.py` (original audit build).
2. `prepare_pools.py`, `run_p1.py`, `report_p1.py`.
3. `P2_configs.py`, `P2_controls.py`, `report_P2.py`.
4. `P3_configs.py`, `P3_controls.py`, `validation_finalists.py`.
5. `P0_certificates.py` (audit build), `P1_refine_attribution.py`,
   `report_P0_refined.py`, `selected_diagnostics.py`, `smoke_runner.py`.
6. `confirmatory_prepare.py` then `run_confirmatory.py` (production build).
7. `report_P3.py`, `finalize_results.py`, `seal_results.py`.

Stage scripts refuse to overwrite important raw data or the policy lock. Do not
rerun preparation/selection scripts in the delivered sealed directory. Analysis
alone may be repeated after the whole execution finishes:

```bash
OPENBLAS_NUM_THREADS=1 ACCURACY_NATIVE_BUILD=build_prod \
  seamwise_bench/.venv/bin/python seamwise_accuracy/scripts/finalize_results.py
```

For an isolated replay of the frozen configurations and saved samples:

```bash
seamwise_bench/.venv/bin/python seamwise_accuracy/scripts/reproduce_frozen.py \
  --destination /tmp/seamwise_reproduction/seamwise_accuracy
```

The replay copies source/configuration/data to a new tree, links the existing
sealed base as a sibling dependency, rebuilds and runs correctness gates, records
a new local binary/provenance lock and executes the same fixed matrix. It is a
reproduction on already inspected samples, not new confirmatory evidence. A new
scientific confirmation needs new independent seeds and a new prospective lock.
The source-to-original preservation inventory is
`evidence/previous_framework_sha256.json`; the final seal verifies it rather than
relying on a historical statement of immutability.

## Interrupted execution and recovery

The first campaign stopped during d5 Tesseract, after three complete d3 jobs and
a durable 3188-shot prefix. `scripts/recover_confirmatory.py` retains completed
jobs and retries the incomplete job on the full unchanged 8000 IDs using the
original frozen worker. The prefix remains immutable and is excluded as an
independent estimate. The recovery manifest records its digest; final analysis
crosschecks duplicate predictions. Policies, binaries, samples and N never change.
Prior accounted active execution is charged to the original five-hour planning
cap. The old process termination time and lost in-flight work were not recorded;
the prior-time estimate includes a 30-second allowance and is not a certified
upper bound on aggregate historical CPU work. The resumed supervisor enforces its
remaining cap. The inactive calendar interval does not count as computation.

The final archive also embeds the complete sealed base archive under
`base_dependency/`. Extract that base archive into the same parent directory as
`seamwise_accuracy/` before following the original environment installation.
The original base contains both the historical study and the native framework.

Actual-path selection conflicts are counted separately in
[TRAJECTORY_SELECTION.md](results/failure_attribution/TRAJECTORY_SELECTION.md).
Rebuild this derived table with `scripts/report_trajectory_attribution.py`; the
final-incumbent conditional queries and actual earlier selection events have
different scopes and must not silently replace one another.

If a later stage watchdog truncates Tesseract again, the declared budget-only
completion rule permits an accuracy-only checkpoint continuation. Its separate
`scripts/resume_tesseract_accuracy.py` wrapper calls the unchanged frozen decoder
factory and binary, verifies 16 predetermined checkpoint predictions, and decodes
only remaining IDs in the original saved permutation. Every final accuracy ID
appears exactly once. Mixed-process times stay auxiliary; whole-cohort peak RSS
is unavailable. The new orchestration script and all checkpoint hashes are
archived transparently; this does not change the frozen decoder policies. The
checkpoint parser rejects wrong-corpus, duplicate and invalid records and only
ignores an incomplete final JSON write.

The final mechanism follow-up is
[FINAL_ATTRIBUTION.md](results/failure_attribution/FINAL_ATTRIBUTION.md): it unions
P0/P1 certificates with a no-tuning replay of the frozen selected policies on all
84 original diagnostic cases. Run `replay_selected_diagnostics.py` once, then
`report_final_attribution.py`, after benchmarks. `bp_quality_audit.py` produces
[BP_QUALITY.md](results/BP_QUALITY.md) on the same 32 validation syndromes for
each of the eight predeclared BP presets. These are diagnostic follow-ups, not
new policy selection or additional confirmatory samples.
