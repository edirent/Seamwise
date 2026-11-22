# Model, provenance, and implementation audit

The recovered inputs are `../experiments/` and the unified paper is `../manuscript/`.
No historical file or manuscript claim is edited. `evidence/original_sha256.json`
records all 1,065 original file hashes before implementation. Both supplied input
and source manifests verify. See `evidence/pre_rewrite_audit.json` for the small
paired reproduction and exact per-model model checks; this is reused correctness
evidence, not independent accuracy data.

## Model contract

Historical samples were generated with `dem.compile_sampler`, not the circuit
sampler. They remain a separately labeled independent-mechanism DEM experiment.
New validation, timing, and locked test samples are drawn from the saved full
Stim circuit with `compile_detector_sampler(..., separate_observables=True)`.
The decoder receives detector bits only. Fault records and true observables are
never passed into a decoder. Splits use independently declared seeds, with
stable IDs, content hashes, and the exact Stim version in their manifests.

For each audited circuit, regenerating the DEM with `decompose_errors=False,
approximate_disjoint_errors=False` exactly reproduces the saved DEM. Each
flattened error instruction becomes one stable fault column. Detector and
observable targets are XORed, retaining zero-detector logical columns and
different logical tags for identical detector supports. No columns are merged
by this framework. Stim can combine equivalent mechanisms when producing its
DEM; equivalence then concerns the full detector-plus-observable signature.
`evidence/circuit_dem_noise_equivalence.json` additionally verifies the exact
independent-Pauli factorization of every noise-channel type in all 24 historical
circuits. For DEPOLARIZE1 the three independent Pauli rates are
`q=(1-sqrt(1-4p/3))/2`; for DEPOLARIZE2 the fifteen rates are
`q=(1-(1-16p/15)^(1/8))/2`. Explicit XOR-group convolution reproduces the full
channel probability masses to numerical precision. Other noisy operations are
independent binary Pauli/readout flips. Combined with Stim's exact Clifford DEM
conversion (no disjoint approximation) and exact full D/L column checks, this
establishes the stated circuit/DEM decoding-model equivalence for these supported
channels. Historical versus new streams remain different sampled experiments;
no claim rests on matching a few empirical frequencies.

Separators, if present, divide suggested components of ONE correlated mechanism:
the matrix converter XORs their complete joint signature and never samples the
pieces independently. The three initial audited models have no separators or
invisible logical columns; dedicated fixtures cover both conventions. Boundary
faults are degree-one columns, with no artificial syndrome bit. Detector and
observable order is ascending Stim ID, matrices are detector/observable by
fault, and packed hashes use little bit order. New circuit samples have no
sampled-error array. Model-equivalence tests are separate from solver tests.

BB72 and BB144 retain the published bicycle polynomial/check construction in
the recovered generator, with both Bell observable sectors. Their ideal MPP,
data-Pauli and measurement-flip noise is phenomenological; it is not the noisy
ancilla-extraction surface-code noise model. BB distances are provenance labels,
not newly proven minimum distances. No threshold claim follows from this work.

## HUF provenance

The [original paper](https://arxiv.org/html/2403.03272v2) describes HUF and
belief-HUF, including a least-recently-updated scheduling tie rule. The supplied
Python reference instead ties by minimum public cluster label and uses its own
30-iteration residual-BP variant. The port intentionally reproduces that
reference policy. A faithful author executable was not located in the paper's
available links: official HUF status is **UNAVAILABLE**, and both port and Python
are **REFERENCE_REIMPLEMENTATION**. `BeliefFindDecoder` is never relabeled as the
authors' HUF. Publication-algorithm fidelity and fidelity to this frozen reference
are different claims.

## Baseline provenance and compatibility

* [Tesseract](https://github.com/quantumlib/tesseract-decoder) is observable-only
  through the selected public API. Correction validity is UNAVAILABLE. The
  final installed wheel was built from official commit
  `54569b4af741423708922a1c033feb483fc034c1` using explicit Bazel `-c opt`,
  `--jobs=1` and the portable CPU target. Initial and release build logs, wheel
  hashes and local platform retagging are retained. The initial development
  wheel was replaced before admitted measurements. The
  [2026 optimization paper](https://arxiv.org/html/2602.02985v2)
  identifies PRs [25](https://github.com/quantumlib/tesseract-decoder/pull/25),
  [34](https://github.com/quantumlib/tesseract-decoder/pull/34), and
  [57](https://github.com/quantumlib/tesseract-decoder/pull/57). Their actual merge
  revisions and ancestry, rather than the wheel date, are the lineage gate.
  Beam 5 / queue 200000 is retained as a historical anchor; validation also
  tests stronger beams and search settings. No unverified wheel becomes evidence
  of beating the modern optimized implementation.
  Merge ancestry verifies all three optimizations in the actual source build.
  The upstream TODO for detector-invisible logical mechanisms with p>1/2 is
  guarded by an explicit UNSUPPORTED adapter exception; primary models contain
  none of these mechanisms, so this limitation is not silently approximated.
* [LDPC](https://github.com/quantumgizmos/ldpc) 2.4.1 supplies compiled BP-LSD and
  BP-OSD. The C++ headers used internally are checked against the official PyPI
  source archive: all nine shipped headers match byte-for-byte; eleven helper
  headers absent from that archive are supplemented from the pinned official
  git revision. BP uses double precision, parallel normalized min-sum,
  scale .625, 30 iterations for fidelity, one thread, syndrome input. The binding's
  zero-input early return is reproduced. Posterior LLRs are clipped to [-100,100]
  for residual HUF, with base=(LLR<0), residual=s XOR D base, and absolute LLR
  growth costs. The external solver sweep includes stronger supported orders
  and schedules as separately named configurations.
* [Relay-BP](https://github.com/trmue/relay) 0.2.2 successfully built with the
  existing Rust toolchain. The official F64 API receives the complete joint
  D/prior model and returns a fault correction. F32 is a separate precision
  variant. Seed and ensemble effort are explicit. The source reseeds per
  decode, so a fixed declared seed defines a deterministic decoder, rather
  than an undeclared stream shared across shots. Threading is fixed at one;
  `par_decode_batch` is not used.
* [GARI](https://www.nature.com/articles/s41467-026-70556-3) has an
  [official native C implementation](https://github.com/astra-decoders/gari-nms),
  which was compiled without source edits. Its provided preparation assumes
  specific memory-circuit detector conventions and one monitored logical
  sector. The initial compatibility record was therefore unsupported pending
  verification; subsequent checks establish unique X/Z projections and exact
  XOR composition of BOTH D and L for every joint column in the three workloads.
  The adapter constructs the exact augmented graph, keeps original fault priors,
  assigns auxiliary priors 1/2, and verifies unique syndrome extensions and the
  complete observable map. Both full-graph stopping and two correlated-sector
  passes are explicitly labeled adaptations. Each sector pass retains ALL
  detector evidence and joint priors; it is not an X/Z marginal-noise substitution.
  Two-sector ensembles execute sequentially on one core, with twice the stated
  ensemble count in native kernel calls. Ensemble selection uses exact XOR
  marginal weights, a documented adapter choice differing from the example's
  probability-sum heuristic. The published batched scoring function receives
  syndromes and logical matrices, not ground-truth sampled errors; our adapter
  uses the single-kernel prediction API and computes the common full frame.
  Bounded-iteration nonconvergence is logged and can fail correction eligibility;
  successful compilation or model equivalence is not a claim of decoding quality.
* PyMatching is installed transitively but is not eligible on the undecomposed
  hypergraphs. No graphlike projection is used as the principal baseline.

## Native invariants and remaining limits

All online graph, BP, solve, fallback, repair, intrinsic syndrome checks, cost
acceptance, and frame loops are C++. Model preparation creates global/local
maps and all windows once. Mutable workspaces reset each shot. Physical DSU
roots use union-by-size and path compression; public minimum labels determine
ties. For fault j, `missing[j]` is exactly the number of its incidence edges
whose endpoints have different roots. A union scans moved-vertex incidence
and decrements only edges joining those two former components. Each becomes
internal once, and a column activates at zero missing edges. Boundary lists
merge by sorted symmetric difference, preserving incidence event order.

Sparse basis entries hold only their actual detector/fault support IDs, rather
than full-circuit-width bit vectors. Pivot maps are ordered once by structure.
Persistent merges transfer disjoint pivot nodes, residuals, and sparse witnesses;
no previously inserted column is re-eliminated during a merge. An optional packed
uint64 terminal solve uses explicit cluster-local row/fault coordinates. Every
mode retains the same canonical terminal column and pivot policy. Dependent
columns have deterministic zero free variables; neither feasibility nor cost
descent implies maximum likelihood or a correct logical class. Full logical
kernel-image invariants are checked separately with finite enumeration.

No lazy floating-point clock heap, SIMD claim, parallel-band schedule, or
cross-shot posterior warm start is introduced. The production build disables
unsafe reassociation. Diagnostics and histories are enabled only in a separate
pass, including failed local attempts. Scalar capacity/RSS and allocator audits
have distinct meanings; third-party allocator ownership is not inferred from
an RSS subtraction. Any unimplemented accounting is reported unavailable.

The native modes share a full-witness working-algebra oracle contract, followed
by the same canonical terminal reconstruction. Rebuild discards intermediate
pivot/witness states across growth events without doing useless merge work.
Persistence ratios therefore refer to this matched implementation contract;
they are not a claim of an optimum over all possible validity-only rebuilds.
The terminal canonical-basis exchange investigation is an oracle-only finite
study, not a shipped native optimization. Isolated acceptance/binding timers
and per-update logical-frame-change rates are unavailable; aggregate wrapper
intervals, accepted updates and full predicted frames remain available.
