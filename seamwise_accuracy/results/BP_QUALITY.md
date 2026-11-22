# Controlled BP quality diagnostics

All eight previously declared P2 presets use the same full detector graph, priors and first 32 validation syndromes per workload. Profiles were not selected or changed using this follow-up. Iterations, hard-decision residuals and convergence precede HUF; logical failures follow the joint BP+HUF solve. These small exploratory global-graph diagnostics are not measurements of the complete partition/repair policy, not additional independent test shots, and not publication latency. No correlated fault or logical mapping changes.

| Workload | Profile | Converged /32 | Mean iterations | Mean hard residual | Joint after-HUF failures /32 | NaN LLRs |
|---|---|---:|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | bp_reference | 23 | 10 | 1.5 | 3 | 0 |
| surface_d3_p0.003_B4 | bp_norm08 | 23 | 18.03 | 1.5 | 3 | 0 |
| surface_d3_p0.003_B4 | bp_norm10 | 24 | 17.03 | 1.188 | 2 | 0 |
| surface_d3_p0.003_B4 | bp_damp08 | 29 | 9.25 | 0.4062 | 1 | 0 |
| surface_d3_p0.003_B4 | bp_serial | 27 | 10.84 | 0.3125 | 1 | 0 |
| surface_d3_p0.003_B4 | bp_norm05 | 19 | 24.75 | 1.594 | 2 | 0 |
| surface_d3_p0.003_B4 | bp_iter60 | 23 | 18.44 | 1.5 | 4 | 0 |
| surface_d3_p0.003_B4 | bp_norm08_30 | 23 | 9.594 | 1.438 | 5 | 0 |
| surface_d5_p0.006_B4 | bp_reference | 0 | 30 | 16.56 | 6 | 0 |
| surface_d5_p0.006_B4 | bp_norm08 | 1 | 58.28 | 15.88 | 5 | 0 |
| surface_d5_p0.006_B4 | bp_norm10 | 3 | 57.16 | 13.97 | 2 | 0 |
| surface_d5_p0.006_B4 | bp_damp08 | 8 | 48.84 | 5.219 | 7 | 0 |
| surface_d5_p0.006_B4 | bp_serial | 5 | 51.16 | 6 | 6 | 0 |
| surface_d5_p0.006_B4 | bp_norm05 | 0 | 60 | 19.03 | 6 | 0 |
| surface_d5_p0.006_B4 | bp_iter60 | 0 | 60 | 16.09 | 6 | 0 |
| surface_d5_p0.006_B4 | bp_norm08_30 | 1 | 29.22 | 17 | 5 | 0 |
| bb144_p0.015_B4 | bp_reference | 0 | 30 | 69.78 | 1 | 0 |
| bb144_p0.015_B4 | bp_norm08 | 7 | 57.41 | 17.28 | 0 | 0 |
| bb144_p0.015_B4 | bp_norm10 | 17 | 51.28 | 5.562 | 0 | 0 |
| bb144_p0.015_B4 | bp_damp08 | 32 | 5.094 | 0 | 0 | 0 |
| bb144_p0.015_B4 | bp_serial | 31 | 5.312 | 0.125 | 0 | 0 |
| bb144_p0.015_B4 | bp_norm05 | 20 | 28.91 | 2.031 | 0 | 0 |
| bb144_p0.015_B4 | bp_iter60 | 0 | 60 | 66.78 | 1 | 0 |
| bb144_p0.015_B4 | bp_norm08_30 | 0 | 30 | 30.06 | 0 | 0 |

The fixed parallel .625/60 control isolates iteration from serial scheduling; .8/30 isolates normalization from iteration; .8/60 versus damped .8/60 isolates damping. A lower hard residual or faster convergence is not proof of a better logical class; the paired independent outcomes remain authoritative. The original 504 diagnostic conditioned-system LLR audit matches official LDPC exactly, including signed infinities, with no actual NaN messages; non-finite NumPy interpolation summaries are separately preserved and corrected.
