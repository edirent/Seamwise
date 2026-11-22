# Final diagnostic certificates, including the fixed-policy follow-up

Initial P0 and P1 records are unchanged. This final table adds the selected-policy replay after the entire benchmark, with no policy tuning. A decoder-generated correction is clamped to the old exterior and counted only when its full syndrome/frame and strictly lower cost are independently verified. Evidence scopes and actual-path selection failures remain separate.

| Workload | Radius | Sampled original failures | Unreachable | Cheaper correct witness, union | Missing original affine growth direction | Cost explanation unresolved |
|---|---:|---:|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | 1 | 16 | 2 | 7 | 14 | 7 |
| surface_d3_p0.003_B4 | 2 | 16 | 0 | 11 | 14 | 5 |
| surface_d5_p0.006_B4 | 1 | 16 | 0 | 4 | 13 | 12 |
| surface_d5_p0.006_B4 | 2 | 16 | 0 | 5 | 11 | 11 |
| bb144_p0.015_B4 | 1 | 12 | 0 | 2 | 9 | 10 |
| bb144_p0.015_B4 | 2 | 12 | 0 | 12 | 7 | 0 |

## Production-radius search witnesses

| Workload | Certified / sampled failures | Stratum-weighted witness fraction | Pointwise 95% finite-population bounds |
|---|---|---:|---|
| surface_d3_p0.003_B4 | 7/16 | 44.9% | 15.2%–81.7% |
| surface_d5_p0.006_B4 | 4/16 | 27.8% | 6.9%–68.1% |
| bb144_p0.015_B4 | 12/12 | 100.0% | 78.6%–100.0% |

The estimates weight seeded random historical failure strata and use exact hypergeometric inversion, Bonferroni across strata. They are exploratory pointwise intervals, not simultaneous across all categories. Positive witnesses certify existence; failure to find a witness does not certify absence, so an interval for the certificate rule must not be used as an upper bound on the actual prevalence of search limitation. Categories overlap and are not an exclusive causal partition.

The decisive BB follow-up finds cheaper correct-class full-band corrections for all 12 sampled old failures using the unchanged selected damped-BP configuration. Thus strict cost descent permits a correct update on all 12: none of these 12 is ACCEPTANCE_LIMITED in the formal no-cheaper-correct-solution sense. The old solver missed such candidates, despite exact implementation agreement with official BP arithmetic. This supports inference/candidate generation as a limitation on these cases; the effect cannot be assigned separately to damping, normalization and iteration allowance without the controlled BP diagnostics. It does not prove that posterior-class mismatch never matters, or that every unsampled failure has the same cause.

Actual-path selection conflicts still occurred in 7/12 BB cases (five correct initial corrections harmed; two correct proposals rejected). These can overlap SEARCH_LIMITED: an expensive correct proposal may be rejected even though another, cheaper correct correction exists. See `TRAJECTORY_SELECTION.md`. Raw selected corrections, clamped witnesses, floating allowances, original flags, new flags and exact label intersections remain in the accompanying JSON/JSONL.
