# Actual production-path selection witnesses

This scope differs from the final-incumbent conditional queries in REFINED_ATTRIBUTION.md. Here a correct incumbent produced by partitioned initialization is itself an available correction; accepting a wrong-class repair instead is a production selection failure. Rejecting a generated correct proposal while retaining a wrong incumbent is also a selection failure. Their union is counted per failed shot, never as disjoint population causes. These events do not certify that every correct-class solution is more expensive, and are not ACCEPTANCE_LIMITED optimum certificates.

All B4 primaries have one actual production seam, so an accepted wrong-class update directly changes a correct cut initial correction into the recorded final failure. Original radius1/radius2 branches remain separate, and only the production radius is used in this table.

| Workload | Production radius | Diagnosed failed shots | Correct proposal rejected | Correct incumbent harmed | Union | Weighted population estimate | Pointwise 95% bounds |
|---|---:|---:|---:|---:|---:|---:|---|
| surface_d3_p0.003_B4 | 1 | 16 | 0 | 0 | 0 | 0.0% | 0.0%–37.1% |
| surface_d5_p0.006_B4 | 1 | 16 | 3 | 0 | 3 | 20.9% | 3.6%–61.7% |
| bb144_p0.015_B4 | 2 | 12 | 2 | 5 | 7 | 58.3% | 33.3%–81.0% |

Finite-population bounds invert the hypergeometric distribution within the seeded uniform historical failure strata, with Bonferroni across strata. They are exploratory pointwise intervals, not simultaneous across all diagnostic properties. The enriched control corpus is not used as an unweighted population denominator. Exact IDs and before/after event witnesses are in `trajectory_selection_certificates.json`. The conditional query count and this actual-path count answer different questions; neither should silently replace the other.
