# Failure attribution: exploratory evidence

P0 run: `results/failure_attribution/20261110T085943Z`. 84 stratified diagnostic shots; native trace final corrections matched the unchanged archived decoder on all 84 shots. No invalid correction or model/numerical mismatch was observed in these checks; this is not a proof that every untested model/numerical issue is absent.

The old final-test corpus is now exploratory only. Truth is used solely for offline scoring and correct-class oracle constraints. Production proposal calls receive syndrome/conditioned detector targets, model priors and decoder-visible states only. New independent validation/timing/confirmatory streams were generated before policy changes.

## Full paired historical outcomes

| Workload | N | Both correct | Seamwise only wrong | Tesseract only wrong | Both wrong |
|---|---:|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | 10000 | 9486 | 383 | 34 | 97 |
| surface_d5_p0.006_B4 | 10000 | 8631 | 1056 | 104 | 209 |
| bb144_p0.015_B4 | 10000 | 9958 | 42 | 0 | 0 |

Exact sample-ID pairing, Wilson intervals and paired discordance confidence bounds are retained in `results/failure_attribution/20261110T085943Z/paired_outcomes.json`. Aggregate differences were not used to infer cell counts.

## Initial P0 classification (superseded by refined certificates)

Counts below concern sampled Seamwise failures only, with overlapping labels. Radius1/radius2 queries use the SAME incumbent final state; original production radius is one on surface and two on BB144. All primaries have B=4/core=2, hence one seam and combined radius1+radius2 equals radius2. No independent combined-band sample is invented.

| Workload | Radius | Sampled failures | Unreachable | Cheaper correct class found | Cost blocking certified | Missing correct direction in growth exposure | Correct proposal cost-rejected | Cost explanation unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | 1 | 16 | 2 | 3 | 0 | 14 | 0 | 11 |
| surface_d3_p0.003_B4 | 2 | 16 | 0 | 1 | 0 | 15 | 1 | 15 |
| surface_d5_p0.006_B4 | 1 | 16 | 0 | 0 | 0 | 15 | 3 | 16 |
| surface_d5_p0.006_B4 | 2 | 16 | 0 | 0 | 0 | 11 | 1 | 16 |
| bb144_p0.015_B4 | 1 | 12 | 0 | 0 | 0 | 10 | 0 | 12 |
| bb144_p0.015_B4 | 2 | 12 | 0 | 0 | 0 | 8 | 2 | 12 |

`exposed_logical_change_rank` is the logical kernel image supported by columns activated inside actual HUF growth components, an algebraic upper bound on what that growth support exposes. It is not the number of candidates enumerated. REACH_EXPOSURE_LIMITED requires the specific true mismatch direction to be absent from this image while present in the full band image. Rank deficit alone is not called proof of a logical failure cause. A larger exposed rank does not prove an inexpensive correct correction exists.

SEARCH_LIMITED requires an explicitly verified correct-class solution with strictly lower configuration cost. ACCEPTANCE_LIMITED requires a certified cost lower bound excluding strict descent. CP-SAT OPTIMAL refers to a floor-quantized integer objective; real-cost upper/lower bounds include its quantization error and a conservative floating summation allowance. Incomplete optimization is FEASIBLE_NOT_PROVEN_OPTIMAL/TIME_LIMIT, never infeasibility. Tiny brute-force tests verify feasibility, optimum and bound containment. See https://developers.google.com/optimization/cp/cp_solver/ and https://github.com/google/or-tools/blob/stable/ortools/sat/cp_model.proto .

Pointwise finite-population interval estimates are in `classification_estimates.json`. The enriched failure/control corpus is not an unweighted estimate of population logical failure probability. Cost categories overlap exposure/selection categories; no forced exclusive causal explanation is asserted when certificates are missing.

## Actual repair selection events

| Workload | Radius | Diagnostic shots | Correct proposal rejected while incumbent wrong | Correct incumbent changed to wrong class |
|---|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | 1 | 32 | 0 | 0 |
| surface_d3_p0.003_B4 | 2 | 32 | 1 | 0 |
| surface_d5_p0.006_B4 | 1 | 32 | 3 | 0 |
| surface_d5_p0.006_B4 | 2 | 32 | 1 | 0 |
| bb144_p0.015_B4 | 1 | 20 | 0 | 0 |
| bb144_p0.015_B4 | 2 | 20 | 2 | 5 |

These are actual decisions in the native radius-specific traces, not aggregate subtraction. Controls include randomly selected successes and all available outcome types. Rejected correct proposals alone do not prove no cheaper correct-class solution exists. Correct incumbents harmed by a lower-cost proposal demonstrate configuration-cost/logical-outcome disagreement on those shots, not an exact posterior-MAP theorem.

## Actionable next experiments

The audit supplies positive search-limitation witnesses on surface d3, shows missing growth-supported logical directions, and records correct candidates rejected by cost descent and correct incumbents harmed by accepted lower-cost proposals. Therefore compare stronger conditional solvers and a bounded class-diverse candidate pool, and separately test monotone-cost versus truncated logical-class support selection. Do not assume more search or a wider band must improve accuracy. The cost optimum remains unresolved for most larger problems under the two-second cap; acceptance restrictions cannot yet be assigned a dominant population fraction.

Representative IDs and complete correction/candidate/oracle certificates are in the run JSONL. The new policy must be selected on the new validation corpus and confirmed on unopened independent samples.

## Positive witness refinement from P1

Alternative native/beam candidates are generated without truth and only scored by the offline evaluator. The following counts refine SEARCH_LIMITED when an explicitly verified correct-class candidate is cheaper than the original failed incumbent. They are positive witnesses, not an assumption that every unresolved case is search-limited.

| Workload | Radius | Diagnosed failures | Cheaper correct witness after P1 |
|---|---:|---:|---:|
| surface_d3_p0.003_B4 | 1 | 16 | 6 |
| surface_d3_p0.003_B4 | 2 | 16 | 10 |
| surface_d5_p0.006_B4 | 1 | 16 | 2 |
| surface_d5_p0.006_B4 | 2 | 16 | 3 |
| bb144_p0.015_B4 | 1 | 12 | 0 |
| bb144_p0.015_B4 | 2 | 12 | 0 |

Growth exposure is corrected for the generated proposal affine base: a mismatch absent relative to the incumbent is not classified as unexposed if the proposal already reaches the correct class, or the growth-supported kernel can fix that proposal. The original raw structural-span flags remain auditable. Raw witnesses and all category intersections: `results/solver_comparison/20261110T091016Z/positive_failure_attribution_certificates.json` and `failure_category_intersections.json`. Growth-support certificates and independent row/column rank checks are in the P0 run. Unresolved optimization remains unresolved; no acceptance-blocking population claim is inferred from a rejected proposal alone.


Final classification and confidence intervals: [REFINED_ATTRIBUTION.md](REFINED_ATTRIBUTION.md). Its proposal-relative affine exposure test and P1 positive witnesses supersede the initial counts above.

## State and numerical-summary conventions

The raw P0 names `after_radius1` and `after_radius2` denote separate fixed-radius branches from the same cut initialization. They do not denote a sequential radius1→radius2 run. Original B4 policies have one seam; actual sequential adaptive radius1→radius2 events, with before/after frames, are recorded separately in `results/selected_validation_diagnostics.jsonl`. The P0 original-final-state comparisons condition both queried bands on the same original-policy incumbent.

Some original NumPy quantile summaries contain non-finite tokens when LLRs include infinities. A NaN produced by interpolation of infinities is not by itself evidence of a NaN BP message or an implementation mismatch. A post-measurement finite-LLR/reference audit and portable derived JSONL copies are provided in the P0 directory; original raw records remain unchanged. The finite audit records actual finite, NaN, positive/negative-infinite LLR counts separately and compares the unmodified audit module against official LDPC on identical local targets.


Actual production-path selection witnesses, including a correct cut incumbent harmed by a cheaper repair, are separately counted in [TRAJECTORY_SELECTION.md](TRAJECTORY_SELECTION.md). The final-state conditional proposal counts do not include every earlier trajectory event.


The later fixed selected-policy replay adds positive witnesses without changing any configuration. [FINAL_ATTRIBUTION.md](FINAL_ATTRIBUTION.md) gives the final union of certificates and intervals; initial P0/P1 counts above remain stage-specific.
