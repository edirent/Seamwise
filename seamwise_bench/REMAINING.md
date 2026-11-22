# Remaining registered work

Run commands from seamwise_bench/. These are unrun continuations beyond the original campaign budget, not promised completed comparisons. Policies below were selected on validation before final labels opened; do not choose new parameters from the final outcomes. Keep the original planned multiplicity correction and quality target. No new tuning or universal strongest-baseline claim is authorized by these point comparisons alone.

### bb144_p0.015_B4: lsd

Validation mean-based forecast: accuracy 0.436 CPU h; timing 0.312 CPU h; full memory/soaks about 0.357 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_bb144_p0.015_B4_lsd.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

### bb144_p0.015_B4: osd

Validation mean-based forecast: accuracy 0.059 CPU h; timing 0.042 CPU h; full memory/soaks about 0.048 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_bb144_p0.015_B4_osd.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

### surface_d3_p0.003_B4: lsd

Validation mean-based forecast: accuracy 0.029 CPU h; timing 0.021 CPU h; full memory/soaks about 0.024 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_surface_d3_p0.003_B4_lsd.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

### surface_d3_p0.003_B4: osd

Validation mean-based forecast: accuracy 0.007 CPU h; timing 0.005 CPU h; full memory/soaks about 0.005 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_surface_d3_p0.003_B4_osd.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

### surface_d3_p0.003_B4: relay

Validation mean-based forecast: accuracy 0.001 CPU h; timing 0.001 CPU h; full memory/soaks about 0.001 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_surface_d3_p0.003_B4_relay.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

### surface_d3_p0.003_B4: gari

Validation mean-based forecast: accuracy 0.000 CPU h; timing 0.000 CPU h; full memory/soaks about 0.000 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_surface_d3_p0.003_B4_gari.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

### surface_d5_p0.006_B4: lsd

Validation mean-based forecast: accuracy 0.861 CPU h; timing 0.617 CPU h; full memory/soaks about 0.705 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_surface_d5_p0.006_B4_lsd.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

### surface_d5_p0.006_B4: osd

Validation mean-based forecast: accuracy 1.344 CPU h; timing 0.964 CPU h; full memory/soaks about 1.101 CPU h. Hard-shot tails, preparation and research I/O can increase wall time.

```bash
scripts/seamwise-bench freeze --config configs/deferred_surface_d5_p0.006_B4_osd.yaml --manifest results/20261109T191912Z-dataset-43f9bff8/manifest.json
# Substitute the actual new frozen manifest printed above:
scripts/run_final results/NEW_FROZEN_CAMPAIGN/manifest.json
```

Relay/GARI workloads with no valid completed validation point require a newly budgeted validation sweep first. Existing bounded grid, nonconvergence reproducers, and unlaunched trials are preserved. Rerun the full recorded validation matrix with a larger predeclared wall cap in a new config; do not use test labels to select effort.

Large d=9/11/15, T=d/2d stress fixtures were registered but not prepared. Their circuit generation/decode CPU demand has no defensible measured throughput estimate; report UNAVAILABLE rather than extrapolate a near-linear law. To prepare after allocating a new storage/CPU budget, run `PYTHONPATH=python .venv/bin/python -m seamwise_bench.scaling`; the present first-stage implementation deliberately keeps these large proportional-depth cells stress-only, so enabling them requires an explicit new registry/budget revision and model-equivalence gates.
