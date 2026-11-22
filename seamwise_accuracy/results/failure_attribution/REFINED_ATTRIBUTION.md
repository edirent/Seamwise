# Refined attribution after independent certificates

This table supersedes the initial structural-span counts and initial SEARCH_LIMITED counts in FAILURE_DIAGNOSIS.md. The raw P0 file remains unchanged. Counts overlap; exposure absence is a structural search limitation, not proof that a cheap correct candidate exists or that it is the unique cause. Unresolved refers to absence of a certified cost explanation, not absence of every other label.

| Workload | Radius | n failures sampled | Unreachable | Search witness | Cost blocking certified | Affine growth exposure missing | Proposal selection | Cost unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | 1 | 16 | 2 | 6 | 0 | 14 | 0 | 8 |
| surface_d3_p0.003_B4 | 2 | 16 | 0 | 10 | 0 | 14 | 1 | 6 |
| surface_d5_p0.006_B4 | 1 | 16 | 0 | 2 | 0 | 13 | 3 | 14 |
| surface_d5_p0.006_B4 | 2 | 16 | 0 | 3 | 0 | 11 | 1 | 13 |
| bb144_p0.015_B4 | 1 | 12 | 0 | 0 | 0 | 9 | 0 | 12 |
| bb144_p0.015_B4 | 2 | 12 | 0 | 0 | 0 | 7 | 2 | 12 |

## Fractions among all historical Seamwise failures

The diagnostic corpus intentionally oversamples rare paired outcomes. Estimates below weight each random failure stratum by its known historical population size. Intervals are pointwise 95% finite-population bounds, simultaneous across the two failure strata but not across all categories/radii. These are exploratory bounds for the ability of this audit to certify a property, with n=12 or 16 diagnostic failures; they are not precise estimates of a unique population cause.

| Workload | Production radius | Property | Weighted estimate | 95% finite-population bounds |
|---|---:|---|---:|---|
| surface_d3_p0.003_B4 | 1 | BAND_UNREACHABLE | 11.7% | 0.4%–50.4% |
| surface_d3_p0.003_B4 | 1 | SEARCH_LIMITED | 39.9% | 15.0%–77.9% |
| surface_d3_p0.003_B4 | 1 | ACCEPTANCE_LIMITED | 0.0% | 0.0%–37.1% |
| surface_d3_p0.003_B4 | 1 | REACH_EXPOSURE_LIMITED | 88.3% | 49.6%–99.6% |
| surface_d3_p0.003_B4 | 1 | PROPOSAL_SELECTION_FAILURE | 0.0% | 0.0%–37.1% |
| surface_d3_p0.003_B4 | 1 | UNRESOLVED | 48.4% | 14.0%–79.8% |
| surface_d5_p0.006_B4 | 1 | BAND_UNREACHABLE | 0.0% | 0.0%–36.3% |
| surface_d5_p0.006_B4 | 1 | SEARCH_LIMITED | 13.9% | 1.3%–54.5% |
| surface_d5_p0.006_B4 | 1 | ACCEPTANCE_LIMITED | 0.0% | 0.0%–36.3% |
| surface_d5_p0.006_B4 | 1 | REACH_EXPOSURE_LIMITED | 79.1% | 38.3%–96.4% |
| surface_d5_p0.006_B4 | 1 | PROPOSAL_SELECTION_FAILURE | 20.9% | 3.6%–61.7% |
| surface_d5_p0.006_B4 | 1 | UNRESOLVED | 86.1% | 45.5%–98.7% |
| bb144_p0.015_B4 | 2 | BAND_UNREACHABLE | 0.0% | 0.0%–21.4% |
| bb144_p0.015_B4 | 2 | SEARCH_LIMITED | 0.0% | 0.0%–21.4% |
| bb144_p0.015_B4 | 2 | ACCEPTANCE_LIMITED | 0.0% | 0.0%–21.4% |
| bb144_p0.015_B4 | 2 | REACH_EXPOSURE_LIMITED | 58.3% | 33.3%–81.0% |
| bb144_p0.015_B4 | 2 | PROPOSAL_SELECTION_FAILURE | 16.7% | 4.8%–42.9% |
| bb144_p0.015_B4 | 2 | UNRESOLVED | 100.0% | 78.6%–100.0% |

No ACCEPTANCE_LIMITED optimum certificate was obtained in this sample; its estimated certificate frequency of zero does not establish the absence of cost blocking. Rejected correct proposals (P0 actual events) prove selection disagreement on those shots but do not exclude an even cheaper correct proposal. No MODEL_OR_NUMERICAL_MISMATCH was observed in the recorded model/hash, BP reference, syndrome/frame and trace regression gates.

Exact intersections are in `results/solver_comparison/20261110T091016Z/failure_category_intersections.json`; no unsupported exclusive causal partition is imposed. Representative shot IDs, witnesses, native costs, and original oracle intervals are preserved in the raw P0/P1 evidence.


Actual production-path selection witnesses, including a correct cut incumbent harmed by a cheaper repair, are separately counted in [TRAJECTORY_SELECTION.md](TRAJECTORY_SELECTION.md). The final-state conditional proposal counts do not include every earlier trajectory event.


The later fixed selected-policy replay adds positive witnesses without changing any configuration. [FINAL_ATTRIBUTION.md](FINAL_ATTRIBUTION.md) gives the final union of certificates and intervals; initial P0/P1 counts above remain stage-specific.
