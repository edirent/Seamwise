# Policy ablation: validation and frozen design

All rates here are exploratory validation results. The 128-ID prescreen is a prefix of the 512-ID validation set, not an additional independent corpus. The final test choices were locked before opening any new confirmatory outcomes.

## Implemented policies

The C++ path retains partitioned initialization, conditional repair with fixed exterior, exact syndrome checks and observable-frame construction. A model-only preparation computes at most 128 independently parity-checked kernel moves per band. Bounded beam search uses depth at most two and K in {1,2,4,8,16}. It preserves low-cost configurations and some distinct full logical signatures; this is a heuristic search with no completeness claim. At most two conditional solver calls are allowed per decode, in addition to initialization/fallback. Every primary workload has one B4 seam. Radius two is the whole non-invisible region; a third or independent combined region would duplicate it and was not fabricated.

Policy A (`cost`) includes the incumbent, deduplicates configurations, and accepts only a strictly lower configuration cost (tolerance 1e-10). Every kernel perturbation preserves D_J z=t_J; final full syndrome/frame gates are retained. Policy B (`class_mass`) sums exp(-C) over unique retained configurations within each logical signature and selects the cheapest representative in the winning class. It can increase configuration cost, is a separately named policy, and has no original monotone-cost theorem. Its biased, bounded candidate pool has no exact posterior/MAP interpretation, no exhaustive class coverage, and no claim of calibrated relative class mass.

Adaptive radius1→radius2 uses only BP nonconvergence, fewer than two retained logical signatures, a configuration gap below 0.5, or an empty first band. These are fixed decoder-visible triggers. The ensemble makes a second bounded BP proposal with an alternative scale only when nonconverged or logically redundant; true observables never generate candidates or trigger escalation. The serial BP schedule is the official variable-serial LDPC schedule, not check-layered BP. No graph, fault prior, shared physical fault, or observable mapping was changed.

## Fixed-budget prescreen (128 validation IDs)

| Workload | Variant | Failures | Mean ms | p99 ms |
|---|---|---:|---:|---:|
| surface_d3_p0.003_B4 | ensemble4_cost | 2/128 | 1.981 | 4.706 |
| surface_d3_p0.003_B4 | K4_class_mass | 3/128 | 1.814 | 3.695 |
| surface_d3_p0.003_B4 | ensemble4_class_mass | 2/128 | 2.02 | 4.573 |
| surface_d3_p0.003_B4 | K8_class_mass | 3/128 | 3.164 | 4.903 |
| surface_d3_p0.003_B4 | combined8_cost | 1/128 | 9.67 | 50.09 |
| surface_d3_p0.003_B4 | adaptive8_cost | 3/128 | 3.695 | 12.16 |
| surface_d3_p0.003_B4 | K2_class_mass | 3/128 | 1.328 | 3.311 |
| surface_d3_p0.003_B4 | K4_cost | 3/128 | 1.883 | 3.698 |
| surface_d3_p0.003_B4 | K16_cost | 3/128 | 5.587 | 7.601 |
| surface_d3_p0.003_B4 | K1_cost | 3/128 | 0.2621 | 1.926 |
| surface_d3_p0.003_B4 | combined8_class_mass | 1/128 | 9.644 | 50.14 |
| surface_d3_p0.003_B4 | K16_class_mass | 3/128 | 5.819 | 8.19 |
| surface_d3_p0.003_B4 | K8_cost | 3/128 | 3.158 | 4.888 |
| surface_d3_p0.003_B4 | P2_fast | 3/128 | 0.2583 | 1.924 |
| surface_d3_p0.003_B4 | K2_cost | 3/128 | 1.25 | 3.19 |
| surface_d3_p0.003_B4 | adaptive8_class_mass | 3/128 | 3.786 | 13.02 |
| surface_d3_p0.003_B4 | K1_class_mass | 3/128 | 0.2783 | 2.259 |
| surface_d3_p0.003_B4 | original | 4/128 | 0.2386 | 1.079 |
| surface_d5_p0.006_B4 | K4_class_mass | 18/128 | 19.91 | 28.4 |
| surface_d5_p0.006_B4 | K2_class_mass | 18/128 | 15.96 | 22.47 |
| surface_d5_p0.006_B4 | K16_cost | 18/128 | 39.35 | 49.63 |
| surface_d5_p0.006_B4 | adaptive8_class_mass | 14/128 | 62.52 | 88.45 |
| surface_d5_p0.006_B4 | K1_class_mass | 18/128 | 10.93 | 19.5 |
| surface_d5_p0.006_B4 | adaptive8_cost | 14/128 | 55.75 | 77.2 |
| surface_d5_p0.006_B4 | K4_cost | 18/128 | 19.25 | 27.24 |
| surface_d5_p0.006_B4 | combined8_cost | 14/128 | 419.2 | 576.9 |
| surface_d5_p0.006_B4 | K8_cost | 18/128 | 25.35 | 32.15 |
| surface_d5_p0.006_B4 | ensemble4_class_mass | 19/128 | 24.58 | 34.19 |
| surface_d5_p0.006_B4 | K2_cost | 18/128 | 15.65 | 21.96 |
| surface_d5_p0.006_B4 | K1_cost | 18/128 | 9.57 | 17.15 |
| surface_d5_p0.006_B4 | combined8_class_mass | 14/128 | 447.5 | 594.4 |
| surface_d5_p0.006_B4 | K16_class_mass | 18/128 | 41.63 | 50.44 |
| surface_d5_p0.006_B4 | ensemble4_cost | 19/128 | 25.41 | 36.22 |
| surface_d5_p0.006_B4 | P2_fast | 18/128 | 10.13 | 18.44 |
| surface_d5_p0.006_B4 | original | 21/128 | 7.624 | 16.27 |
| surface_d5_p0.006_B4 | K8_class_mass | 18/128 | 28.4 | 38.21 |
| bb144_p0.015_B4 | K8_cost | 0/128 | 46.35 | 57.4 |
| bb144_p0.015_B4 | adaptive8_cost | 0/128 | 25.38 | 35.98 |
| bb144_p0.015_B4 | K8_class_mass | 0/128 | 45.66 | 62.44 |
| bb144_p0.015_B4 | K1_cost | 0/128 | 3.704 | 14.42 |
| bb144_p0.015_B4 | K4_class_mass | 0/128 | 26.6 | 40.29 |
| bb144_p0.015_B4 | original | 0/128 | 15.41 | 34.76 |
| bb144_p0.015_B4 | ensemble4_class_mass | 0/128 | 49.31 | 65.5 |
| bb144_p0.015_B4 | P2_fast | 0/128 | 3.807 | 12.21 |
| bb144_p0.015_B4 | ensemble4_cost | 0/128 | 48.92 | 67.38 |
| bb144_p0.015_B4 | K2_class_mass | 0/128 | 18.93 | 36.09 |
| bb144_p0.015_B4 | K1_class_mass | 0/128 | 3.713 | 13.35 |
| bb144_p0.015_B4 | K16_cost | 0/128 | 78.68 | 100.1 |
| bb144_p0.015_B4 | K16_class_mass | 0/128 | 74.7 | 94.44 |
| bb144_p0.015_B4 | K2_cost | 0/128 | 19.24 | 37.01 |
| bb144_p0.015_B4 | adaptive8_class_mass | 0/128 | 24.96 | 36.08 |
| bb144_p0.015_B4 | K4_cost | 0/128 | 26.84 | 41.3 |
| surface_d3_p0.003_B4 | joint_search8 | 3/128 | 5.527 | 7.627 |
| surface_d3_p0.003_B4 | joint_fast | 3/128 | 0.2579 | 1.85 |
| surface_d3_p0.003_B4 | cut_fast | 5/128 | 0.1486 | 1.376 |
| surface_d3_p0.003_B4 | fixed_r2_K1 | 3/128 | 0.3851 | 2.61 |
| surface_d3_p0.003_B4 | fixed_r2_K8 | 3/128 | 5.808 | 9.255 |
| surface_d3_p0.003_B4 | fixed_r1_K8 | 3/128 | 3.248 | 5.558 |
| surface_d5_p0.006_B4 | fixed_r1_K8 | 18/128 | 26.24 | 35.72 |
| surface_d5_p0.006_B4 | joint_search8 | 17/128 | 35.56 | 42.47 |
| surface_d5_p0.006_B4 | joint_fast | 17/128 | 7.553 | 9.912 |
| surface_d5_p0.006_B4 | fixed_r2_K8 | 15/128 | 44.18 | 50.67 |
| surface_d5_p0.006_B4 | cut_fast | 20/128 | 6.277 | 9.634 |
| surface_d5_p0.006_B4 | fixed_r2_K1 | 15/128 | 13.75 | 19.44 |
| bb144_p0.015_B4 | joint_search8 | 0/128 | 41.05 | 49.6 |
| bb144_p0.015_B4 | cut_fast | 0/128 | 2.11 | 9.567 |
| bb144_p0.015_B4 | joint_fast | 0/128 | 1.628 | 5.006 |
| bb144_p0.015_B4 | fixed_r2_K1 | 0/128 | 3.61 | 12.01 |
| bb144_p0.015_B4 | fixed_r2_K8 | 0/128 | 43.42 | 62.64 |
| bb144_p0.015_B4 | fixed_r1_K8 | 0/128 | 24.1 | 36.34 |

Every fixed-radius K=1/2/4/8/16 policy, including truncated class-mass selection, had the same logical failures as the P2 fast BP baseline on the 128-ID prescreen: d3=3, d5=18, BB=0. This negative result is retained. K=1/cost corrections match the P2 fast native decoder exactly on all 128 IDs per workload. The native class-mass toy test does demonstrate an actual semantic difference when multiple unique higher-cost configurations outweigh one lower-cost class; a working implementation does not establish an empirical accuracy gain.

The d5 fixed radius2 K1 control had 15 failures versus 18 at radius1, while adaptive K8 had 14. More accessible variables and conditional-state changes are therefore plausible contributors; increased K alone did not explain the prescreen improvement. d3 serial BP and serial-plus-beam both had 1 failure, with large extra latency. BB had zero failures for all fast variants, so no prescreen accuracy ranking among them is justified.

## Full 512-ID validation finalists

Roles were chosen from the prescreen within each family by fewest failures, then mean latency. All retained roles were evaluated again on all 512 validation IDs. The final operating point is the fastest role within 10% of the minimum observed Seamwise validation failure count. This is an internal operating-point rule, not statistical proof of noninferiority. The external 10% relative accuracy constraint is assessed separately on the independent test.

| Workload | Role | Failures /512 | Mean ms | p99 ms |
|---|---|---:|---:|---:|
| surface_d3_p0.003_B4 | stronger_solver | 32 | 0.429 | 2.191 |
| surface_d3_p0.003_B4 | matched_joint | 15 | 8.386 | 37.65 |
| surface_d3_p0.003_B4 | baseline_lsd | 16 | 7.297 | 32.11 |
| surface_d3_p0.003_B4 | baseline_relay | 24 | 0.2667 | 2.175 |
| surface_d3_p0.003_B4 | baseline_osd | 11 | 1.862 | 6.846 |
| surface_d3_p0.003_B4 | original | 36 | 0.2484 | 1.141 |
| surface_d3_p0.003_B4 | adaptive_radius | 13 | 3.428 | 12.4 |
| surface_d3_p0.003_B4 | matched_cut | 15 | 5.346 | 30.9 |
| surface_d3_p0.003_B4 | multi_candidate | 13 | 1.259 | 3.297 |
| surface_d3_p0.003_B4 | baseline_tesseract | 10 | 1.951 | 11.05 |
| surface_d3_p0.003_B4 | best_bp | 15 | 8.103 | 50.91 |
| surface_d3_p0.003_B4 | best_combined | 15 | 7.769 | 47.57 |
| surface_d5_p0.006_B4 | stronger_solver | 60 | 16.42 | 38.97 |
| surface_d5_p0.006_B4 | multi_candidate | 60 | 15.69 | 23.71 |
| surface_d5_p0.006_B4 | original | 59 | 7.166 | 14.42 |
| surface_d5_p0.006_B4 | best_combined | 43 | 52.74 | 78.71 |
| surface_d5_p0.006_B4 | matched_cut | 79 | 5.994 | 10.13 |
| surface_d5_p0.006_B4 | baseline_osd | 28 | 384.4 | 480.6 |
| surface_d5_p0.006_B4 | baseline_lsd | 36 | 261.3 | 336.4 |
| surface_d5_p0.006_B4 | adaptive_radius | 43 | 53.85 | 79.17 |
| surface_d5_p0.006_B4 | baseline_tesseract | 15 | 779.2 | 1.492e+04 |
| surface_d5_p0.006_B4 | matched_joint | 56 | 35.48 | 43.89 |
| surface_d5_p0.006_B4 | best_bp | 42 | 405.3 | 615.8 |
| bb144_p0.015_B4 | best_combined | 0 | 3.757 | 11.2 |
| bb144_p0.015_B4 | matched_cut | 0 | 2.06 | 9.101 |
| bb144_p0.015_B4 | multi_candidate | 0 | 18.19 | 32.15 |
| bb144_p0.015_B4 | baseline_tesseract | 0 | 46.82 | 81.69 |
| bb144_p0.015_B4 | original | 2 | 15.61 | 30.52 |
| bb144_p0.015_B4 | baseline_lsd | 41 | 159.2 | 899.6 |
| bb144_p0.015_B4 | best_bp | 0 | 3.893 | 12.29 |
| bb144_p0.015_B4 | matched_joint | 0 | 1.646 | 4.453 |
| bb144_p0.015_B4 | adaptive_radius | 0 | 24.5 | 37.91 |
| bb144_p0.015_B4 | stronger_solver | 5 | 42.15 | 80.19 |
| bb144_p0.015_B4 | baseline_osd | 62 | 20.61 | 53.55 |

## Frozen choices and causal controls

The independent primary matrix fixes 8000 shots per workload/configuration, before outcomes, under a five-hour sequential one-core cap. Component/baseline controls fix 2000 shared prefix IDs. Dedicated timing uses 1024 independent IDs in 3 fresh processes. The policy/data/source/binary lock is `configs/confirmatory_lock.json`. Its internal 10% validation rule is distinct from the external noninferiority hypothesis.

- surface_d3_p0.003_B4: {"K": 2, "candidate": true, "damping": 0.25, "depth": 2, "iterations": 60, "kind": "new", "max_calls": 2, "name": "selected_combined", "policy": "repair1", "scale": 0.8, "schedule": "parallel", "selection": "cost"}; selected from multi_candidate.
- surface_d5_p0.006_B4: {"K": 8, "adaptive": true, "candidate": true, "depth": 2, "iterations": 30, "kind": "new", "max_calls": 2, "name": "selected_combined", "policy": "repair1", "radius": 1, "scale": 0.8, "selection": "cost"}; selected from best_combined.
- bb144_p0.015_B4: {"damping": 0.25, "iterations": 60, "kind": "new", "name": "selected_combined", "policy": "repair2", "scale": 0.8, "schedule": "parallel"}; selected from best_combined.

The confirmatory controls include unchanged original; stronger repair-only solver; best BP; multi-candidate; adaptive; matched cut and joint; the SAME selected BP at original radius, radius2 and joint; and uniform stronger-inner-family joint, cut, and repaired variants. These prevent attributing an improved BP or inner-family substitution to the outer repair idea. Joint controls reuse the original global solution as their initial proposal instead of performing a deliberately redundant second identical solve; their prepared memory still includes conditional storage and is reported as implemented.

Model-only pool construction and hashes are in `results/prepared_pools/manifest.json`. `results/selected_validation_diagnostics.jsonl` retains actual candidate classes, generated rank, cached-move logical rank, accessible faults, escalation and logical changes for 32 selected-policy validation IDs per workload. Matched-BP fixed-radius traces separately retain iterations, convergence/residuals and finite LLR quantiles; they are not misrepresented as the adaptive execution trace. Reverse-order redecoding matched exact corrections/frames on all 96 audited shots.

Correctness evidence: 2,768 ASan/UBSan/leak native cases, six Python contract tests, BP reference differentials, small oracle brute-force checks, model/hash equivalence and shuffle/reset checks. Diagnostic builds are separate from uninstrumented production timing. Full logs, failures, deferrals and all unsuccessful policies remain in the evidence/results tree.

The adaptive/fixed candidate comparisons share ceilings on solver calls, candidate width, move pool and depth; the fixed strategy may use fewer calls than its allowance. Actual work and latency are reported rather than assuming equal realized work. Zero-target bypass can also trigger the conservative escalation rule; no post-test trigger adjustment was made.
