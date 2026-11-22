# Seamwise native decoder and controlled experiments

This directory extends the recovered Seamwise study without editing historical
results or paper claims. The online production path is C++20: prepared incidence
storage, deterministic weighted growth, rebuild/persistent GF(2), verified native
BP, partition initialization, fallback, syndrome-preserving cost-accepted repair,
and observable-frame construction. Python generates samples, orchestrates fresh
workers, and supplies the frozen correctness oracle.

Read [audit.md](audit.md) before interpreting measurements. Result status and
remaining work are in [RESULTS.md](RESULTS.md). A speedup over the supplied Python
reference is an engineering result; it does not establish an accuracy-matched
advantage over modern native decoders. No historical result is overwritten.

## Build and correctness

The delivered environment is `.venv/`; the source and wheel locks in `evidence/`
are authoritative. On the same Python 3.13/Linux architecture:

```bash
cd seamwise_bench
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
# Install the pinned official-source Tesseract and Relay wheels, overriding
# distribution versions with the same nominal version where necessary.
.venv/bin/python -m pip install --no-deps --force-reinstall \
  evidence/wheels/tesseract_decoder-0.1.1-cp313-cp313-linux_x86_64.whl \
  evidence/wheels/relay_bp-0.2.2-cp313-cp313-linux_x86_64.whl
# In an extracted/moved copy, retain the recorded absolute-path CMake cache
# under a metadata name before configuring the local build:
if [ -f build/CMakeCache.txt ]; then mv build/CMakeCache.txt build/CMakeCache.recorded.txt; fi
scripts/build
scripts/seamwise-bench doctor
scripts/seamwise-bench test-fidelity --config configs/fidelity.yaml
PYTHONPATH=python OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  .venv/bin/python -m pytest tests -q
```

Use `cmake --build build --parallel 1`. The portable release uses `-O3 -DNDEBUG`,
`-fno-fast-math`, and `-ffp-contract=off`; host SIMD is an explicitly separate
`-DSEAMWISE_HOST_SIMD=ON` build. Address/undefined-behavior sanitizer evidence
comes from `build_sanitize/`, never from benchmark executables.

Native revision controls are `build_v1/` (sparse pivot scanning plus official
linked-storage BP), `build_v2/` (indexed sparse reduction), `build_v3/` (contiguous
BP messages), and `build/` (current fair rebuild and read-only prepared storage).
Source snapshots and compile commands are retained. Component switches
`-DSEAMWISE_INDEXED_REDUCTION=OFF` and `-DSEAMWISE_FLAT_BP=OFF` on current source
are component ablations, not exact reconstructions of earlier revisions. To
rebuild an archived revision, overlay its snapshot in an isolated source tree:

```bash
mkdir -p scratch/v1
cp -a cpp scratch/v1/
ln -s "$PWD/vendor" scratch/v1/vendor
ln -s "$PWD/tests" scratch/v1/tests
tar -xzf evidence/native_v1_source.tar.gz -C scratch/v1 --strip-components=1
cmake -S scratch/v1 -B scratch/v1/build -DCMAKE_BUILD_TYPE=Release \
  -DPython_EXECUTABLE="$PWD/.venv/bin/python" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build scratch/v1/build --target _native native_runner --parallel 1
```

Use the corresponding v2/v3 snapshot for those revisions. Both oracle modes always
share BP, graph management, compiler flags, and terminal correction policy.
The optional packed terminal implementation is a measured control, not an
unconditionally selected optimization.

## Frozen data and commands

The completed data preparation is
`results/20261109T191912Z-dataset-43f9bff8/manifest.json`.
It contains three predeclared primary workloads, each with 128 circuit-sampled
validation, 1,024 independent timing, and 10,000 independently seeded locked
test shots. Old DEM samples remain correctness/regression fixtures. Reusing
inputs in process repetitions never increases the independent accuracy N.

```bash
scripts/seamwise-bench prepare --config configs/datasets.yaml
scripts/seamwise-bench run --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json \
  --config configs/smoke.yaml --mode timing
scripts/seamwise-bench validate --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json \
  --config configs/validation.yaml
# Pass the actual validation run directory printed by the preceding command:
.venv/bin/python scripts/select_validation.py results/VALIDATION_RUN_ID
scripts/seamwise-bench freeze --config configs/final.yaml \
  --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Use the frozen campaign manifest printed by freeze. It embeds the selected
# parameters and rejects source/configuration changes.
scripts/seamwise-bench run --manifest results/FROZEN_CAMPAIGN_ID/manifest.json --mode timing
scripts/seamwise-bench run --manifest results/FROZEN_CAMPAIGN_ID/manifest.json --mode accuracy
scripts/seamwise-bench run --manifest results/FROZEN_CAMPAIGN_ID/manifest.json --mode memory
scripts/seamwise-bench analyze --run results/RUN_ID
```

Every invocation allocates a unique directory. Fresh sequential workers pin one
allowed CPU (`SEAMWISE_CPU`, default lowest allowed CPU), one decoder thread, and batch size one.
No benchmark jobs run concurrently. Shot permutations are shared across paired
backends within a repetition; backend order is independently randomized and
saved. Warmup uses the same fixed validation prefix. Output conversion through
the observable frame is timed uniformly. External syndrome validation, sample
generation, hashing, journals, and diagnostics are outside decode timing.
Frozen-manifest status/selection fields describe their creation time; current
completion is recorded in each unique run's `run.json` and execution ledger.

`decode_summary.json` and `shots.jsonl` are atomically committed before memory
auditing. Partial journals, completed prefixes, missing counts, exceptions, stage
budgets, and all statuses survive failures. Completed jobs are never overwritten;
a retry is a new run on the same frozen IDs, not new independent samples.

Additional controlled runs use `configs/engineering.yaml`, `optimization.yaml`,
and `method_ablation.yaml`. Engineering timing is explicitly exploratory with
128 inputs/three processes; the principal native timing corpus uses 1,024 inputs
and seven fresh process repetitions. Kernel/gprof data are diagnostics only.

## Baselines and provenance

Tesseract is built from the pinned official repository with Bazel `-c opt
--jobs=1 --config=wheel`. An explicit `ABI_TAG=cp313` is required for packaging.
The upstream wheel tag defaults to manylinux 2.42; this locally built binary was
retagged `linux_x86_64` for this glibc 2.39 host. That is a local-platform artifact,
not a claim of portable manylinux compatibility. Its source includes the 2026
optimization paper's PRs 25, 34 and 57, verified by commit ancestry.

Relay-BP is built from official commit
`cdfdc996ce55582c4c431f8d8392bcce57175e36`. This includes the per-decode RNG reset
missing from the PyPI 0.2.2 source. A declared fixed deterministic disorder
ensemble is restarted for each shot, avoiding mutable posterior/RNG leakage.
BP-LSD/BP-OSD use official LDPC 2.4.1; internal BP headers match its source tarball.

The official GARI C kernel is compiled without source edits. The adapter verifies
an exact augmented detector model, unchanged original fault priors, auxiliary
constraints, and the full logical-frame map. Its full-graph and two-correlated-
sector stopping adaptations are separately labeled. The two-sector variant uses
two sequential native passes per ensemble element, not a 24-core comparison.
Nonconvergence is retained in bounded validation and excludes operating points
from publication timing; it is not silently treated as a valid correction.

## Statistics and interpretation

`S_port = T_Python_same_policy / T_native_same_policy` requires exact correction
hash equality. `S_persist = T_native_rebuild / T_native_persistent` isolates
persistence with the same optimized frontend. `S_frontier` uses the fastest
eligible native baseline divided by Seamwise time; eligibility is frozen from
validation and tested independently. No finite ratio is inferred from two zero
logical-failure counts.

Logical failure means any observable disagreement per circuit shot; service
failures/invalid corrections are separately retained. Accuracy uses Wilson
intervals and paired discordance cells. Conservative simultaneous exact cell
bounds test a **10% relative noninferiority margin**; that is not identical
accuracy. Strict equality-target bounds are also reported. Fixed final N=10,000
is capped by the declared budget; fewer than roughly 400 failures is explicitly
marked `INSUFFICIENT_PRECISION`. Primary workload aggregation is an equal-weight
geometric mean over the full declared workload set, never a hand-picked maximum.

Timing uncertainty resamples independent sample IDs and paired process
repetitions hierarchically. Mean, median, p95, p99, and maximum are retained;
p99.9 is not claimed. The virtualized/shared host is not represented as bare
metal. No real-time deadline experiment or threshold claim is inferred.

Memory runs use fresh processes, full-corpus RSS/high-water measurements, owned
capacity payloads, a diagnostic glibc allocation-request interposer, and repeated
independent/repeated-syndrome soaks. Requested bytes are not live bytes; capacity
payloads omit allocator overhead and some third-party BP ownership. These are
separate metrics, not an exact backend footprint inferred from RSS differences.
`scripts/build` compiles and calibrates the Linux/glibc interposer separately.
It uses initial-exec TLS to avoid recursive loader allocation while importing
native extensions. The first final memory run's pre-decode worker crashes are
preserved; its repaired rerun uses the same frozen model, policy and sample IDs.

The staged scaling registry includes all historical anchors, independent B/d/T
axes, a distinct logical-gate-layer parameter, proportional-depth cases, BB72 and
BB144, and separate noise classes. First-stage preparation records every stress
exclusion. Fixed-depth results do not establish a threshold.

## Final evidence and archive

`evidence/run_index.json` maps the report to exact raw runs. See
`evidence/backend_capability_matrix.json` for current adapter status (initial
audit failures remain in their chronological evidence), and `REMAINING.md` for
unrun comparison commands with measured throughput estimates.

The final archive includes original files, native/source controls, pinned vendor
source, local official baseline wheels, configs and raw results; it excludes the
virtualenv and build caches. Verify it without extraction:

```bash
python3 scripts/verify_archive.py artifacts/seamwise_native_research_20261109.tar.gz
```

The member manifest and toolchain lock are under `evidence/`; the archive has a
sibling `.sha256` file. Source-wheel baselines require the documented local
platform/Python ABI or a fresh official-source build on another platform.
