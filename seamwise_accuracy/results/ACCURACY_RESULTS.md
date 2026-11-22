# Independent accuracy results

Policy/source/data lock: `configs/confirmatory_lock.json`, SHA256 `85f1b80ee05f1667763ffbbb2d84991233af58b6afb429b563c4d2de35043e28`. Choices and fixed counts precede each job’s `truth_access.json`. The new circuit-generated confirmatory stream has 8000 fixed primary IDs and 2000 fixed shared component IDs per workload. Previous 10,000-shot tests and all 512 new validation shots are exploratory. Sampled errors/true observables are absent from the decoder API; labels are read only for external scoring after the lock.

No policy was selected using these outcomes. The internal validation rule chooses the fastest finalist within 10% of the minimum Seamwise validation failure count; it is not an external noninferiority test. Tesseract was the strongest eligible full-validation reference on all three workloads. Official native LSD/OSD and available eligible Relay are separate component comparisons. GARI’s invalid validation outcome and other uncompleted/ineligible prior operating points are preserved, not called defeated. Their new inferential comparisons are NOT_EVALUABLE. See the execution ledger and P2 evidence.

## Fixed primary matrix

Wilson intervals below are marginal 95%, not multiplicity-adjusted. “Invalid” counts an explicitly available correction failing D x=s. Tesseract supplies a logical frame only, so its correction validity is UNAVAILABLE; zero reported invalid frames is not a certificate for an unreturned correction. Native/official adapter correction-frame consistency is checked outside timing, and new production decoders also enforce full syndrome consistency internally.

| Workload | Configuration | Failures / N | Wilson 95% (%) | Invalid / corrections checked |
|---|---|---:|---|---:|
| surface_d3_p0.003_B4 | original | 403/8000 | 4.579–5.539 | 0 / 8000 |
| surface_d3_p0.003_B4 | baseline_tesseract | 125/8000 | 1.313–1.858 | UNAVAILABLE (frame only) |
| surface_d3_p0.003_B4 | selected_combined | 178/8000 | 1.924–2.572 | 0 / 8000 |
| surface_d5_p0.006_B4 | original | 1011/8000 | 11.93–13.38 | 0 / 8000 |
| surface_d5_p0.006_B4 | baseline_tesseract | 231/8000 | 2.543–3.278 | UNAVAILABLE (frame only) |
| surface_d5_p0.006_B4 | selected_combined | 868/8000 | 10.19–11.55 | 0 / 8000 |
| bb144_p0.015_B4 | baseline_tesseract | 0/8000 | 0–0.048 | UNAVAILABLE (frame only) |
| bb144_p0.015_B4 | selected_combined | 1/8000 | 0.002207–0.07078 | 0 / 8000 |
| bb144_p0.015_B4 | original | 29/8000 | 0.2525–0.5201 | 0 / 8000 |

## Paired primary conclusions

A is the selected improved Seamwise and B is the named comparator. Cell order: both correct / only A wrong / only B wrong / both wrong. The paired risk difference is p_A−p_B. Confidence bounds use simultaneous exact binomial bounds on multinomial cells and a union bound, without treating the cells as independent. Multiplicity is fixed at 425 planned pairwise comparisons across the complete primary+component matrix, including missing jobs. A further factor of two covers risk-difference and noninferiority endpoints jointly; each NI bound uses half its endpoint alpha (six exact cell tails). Per-endpoint alpha=5.8823529e-05. It is never reduced after outcomes.

Noninferiority uses p_A−1.10 p_B≤0 with the previously declared 10% relative margin. PASS requires its adjusted one-sided upper bound≤0. A positive adjusted lower bound demonstrates violation; otherwise it is NOT_ESTABLISHED. Zero/zero observed failures has no finite risk-ratio estimate and cannot establish this relative criterion under these bounds. Marginal Wilson overlap is not used to infer superiority.

| Workload | B | Paired cells | Risk difference (%) | Adjusted CI (%) | NI contrast upper (%) | 10% NI decision |
|---|---|---|---:|---|---:|---|
| surface_d3_p0.003_B4 | original | 7568/29/254/149 | -2.813 | -3.926–-1.689 | -2.033 | PASS |
| surface_d3_p0.003_B4 | baseline_tesseract | 7788/87/34/91 | 0.6625 | -0.1471–1.469 | 1.398 | NOT_ESTABLISHED |
| surface_d5_p0.006_B4 | original | 6678/311/454/557 | -1.787 | -3.782–0.2127 | -0.7879 | PASS |
| surface_d5_p0.006_B4 | baseline_tesseract | 7065/704/67/164 | 7.963 | 6.185–9.714 | 9.561 | VIOLATION_DEMONSTRATED |
| bb144_p0.015_B4 | original | 7970/1/29/0 | -0.35 | -0.7306–0.0261 | 0.02045 | NOT_ESTABLISHED |
| bb144_p0.015_B4 | baseline_tesseract | 7999/1/0/0 | 0.0125 | -0.139–0.1727 | 0.1781 | NOT_ESTABLISHED |

## Fixed 2000-ID component and external comparisons

These roles were selected before new test labels opened. Their N differs from the primary matrix. Pairwise comparisons to a primary configuration use the predeclared shared 0..1999 prefix, never a favorable intersection or a latency-selected subset. Full paired cells and adjusted intervals for every available planned pair are in `accuracy_analysis.json`.

| Workload | Component | Failures / N | Wilson 95% (%) | Invalid | Auxiliary single-pass mean ms |
|---|---|---:|---|---:|---:|
| surface_d3_p0.003_B4 | strong_joint | 103/2000 | 4.264–6.207 | 0 | 1.003 |
| surface_d3_p0.003_B4 | same_BP_radius2 | 40/2000 | 1.472–2.712 | 0 | 0.5433 |
| surface_d3_p0.003_B4 | strong_cut | 99/2000 | 4.083–5.99 | 0 | 0.5985 |
| surface_d3_p0.003_B4 | baseline_relay | 77/2000 | 3.091–4.786 | 0 | 0.3703 |
| surface_d3_p0.003_B4 | same_BP_fixed_radius | 43/2000 | 1.6–2.883 | 0 | 0.3152 |
| surface_d3_p0.003_B4 | multi_candidate | 43/2000 | 1.6–2.883 | 0 | 1.577 |
| surface_d3_p0.003_B4 | baseline_osd | 46/2000 | 1.729–3.054 | 0 | 2.411 |
| surface_d3_p0.003_B4 | strong_all_repair | 86/2000 | 3.495–5.28 | 0 | 0.9126 |
| surface_d3_p0.003_B4 | baseline_lsd | 40/2000 | 1.472–2.712 | 0 | 9.352 |
| surface_d3_p0.003_B4 | best_bp | 46/2000 | 1.729–3.054 | 0 | 9.961 |
| surface_d3_p0.003_B4 | matched_joint | 43/2000 | 1.6–2.883 | 0 | 2.578 |
| surface_d3_p0.003_B4 | adaptive_radius | 41/2000 | 1.515–2.769 | 0 | 4.664 |
| surface_d3_p0.003_B4 | same_BP_joint | 43/2000 | 1.6–2.883 | 0 | 0.3254 |
| surface_d3_p0.003_B4 | stronger_solver | 96/2000 | 3.947–5.827 | 0 | 0.5512 |
| surface_d3_p0.003_B4 | matched_cut | 55/2000 | 2.119–3.562 | 0 | 0.1955 |
| surface_d5_p0.006_B4 | matched_cut | 353/2000 | 16.04–19.38 | 0 | 8.144 |
| surface_d5_p0.006_B4 | adaptive_radius | 206/2000 | 9.043–11.71 | 0 | 74.03 |
| surface_d5_p0.006_B4 | same_BP_joint | 226/2000 | 9.986–12.76 | 0 | 9.979 |
| surface_d5_p0.006_B4 | strong_all_repair | 328/2000 | 14.84–18.09 | 0 | 37.55 |
| surface_d5_p0.006_B4 | same_BP_radius2 | 218/2000 | 9.608–12.34 | 0 | 18.05 |
| surface_d5_p0.006_B4 | strong_cut | 438/2000 | 20.14–23.77 | 0 | 23.8 |
| surface_d5_p0.006_B4 | baseline_osd | 116/2000 | 4.858–6.912 | 0 | 418.8 |
| surface_d5_p0.006_B4 | matched_joint | 226/2000 | 9.986–12.76 | 0 | 39.16 |
| surface_d5_p0.006_B4 | multi_candidate | 259/2000 | 11.55–14.49 | 0 | 16.82 |
| surface_d5_p0.006_B4 | best_bp | 202/2000 | 8.855–11.5 | 0 | 444 |
| surface_d5_p0.006_B4 | stronger_solver | 252/2000 | 11.22–14.13 | 0 | 17.79 |
| surface_d5_p0.006_B4 | strong_joint | 345/2000 | 15.66–18.97 | 0 | 27.31 |
| surface_d5_p0.006_B4 | same_BP_fixed_radius | 262/2000 | 11.69–14.65 | 0 | 10.08 |
| surface_d5_p0.006_B4 | baseline_lsd | 167/2000 | 7.216–9.644 | 0 | 261.2 |
| bb144_p0.015_B4 | baseline_osd | 176/2000 | 7.636–10.12 | 0 | 19.25 |
| bb144_p0.015_B4 | strong_cut | 184/2000 | 8.01–10.55 | 0 | 21.49 |
| bb144_p0.015_B4 | stronger_solver | 11/2000 | 0.3074–0.9822 | 0 | 40.16 |
| bb144_p0.015_B4 | matched_cut | 0/2000 | 0–0.1917 | 0 | 2.058 |
| bb144_p0.015_B4 | multi_candidate | 0/2000 | 0–0.1917 | 0 | 17.89 |
| bb144_p0.015_B4 | strong_all_repair | 100/2000 | 4.128–6.044 | 0 | 51.59 |
| bb144_p0.015_B4 | matched_joint | 0/2000 | 0–0.1917 | 0 | 1.495 |
| bb144_p0.015_B4 | same_BP_joint | 0/2000 | 0–0.1917 | 0 | 1.54 |
| bb144_p0.015_B4 | baseline_lsd | 131/2000 | 5.547–7.72 | 0 | 155.2 |
| bb144_p0.015_B4 | same_BP_radius2 | 0/2000 | 0–0.1917 | 0 | 3.622 |
| bb144_p0.015_B4 | best_bp | 0/2000 | 0–0.1917 | 0 | 3.543 |
| bb144_p0.015_B4 | adaptive_radius | 0/2000 | 0–0.1917 | 0 | 23.53 |
| bb144_p0.015_B4 | same_BP_fixed_radius | 0/2000 | 0–0.1917 | 0 | 3.568 |
| bb144_p0.015_B4 | strong_joint | 168/2000 | 7.263–9.697 | 0 | 27.86 |

## Precision, missing outcomes and limits

The maximum 10,000 new samples were generated before tuning. The validation-only five-hour throughput rule fixed N=8000 before any confirmatory label access. Rare-event comparisons, especially BB144, can remain inconclusive at this N. For every zero-failure cell the one-sided marginal 95% upper bound is 1−0.05^(1/N); zero failures does not establish zero risk. No timeout/unsupported/service failure is counted as a correct shot or a defeated baseline. Incomplete prefixes are retained but excluded from completed failure rates; missing counts are explicit in raw ledgers. Correction validity unavailable from a frame-only baseline remains unavailable. No additional confirmatory claim is made from timing or memory repetitions.
- bb144_p0.015_B4 / baseline_tesseract: 0/8000, marginal one-sided 95% risk upper 0.03744%.

Incomplete accuracy jobs: 0. Complete primary jobs: 9. Complete secondary jobs: 43. Raw files and failures are retained under the phase paths in `P4_run_index.json`.

The bounded oracle and candidate search establish positive witnesses, not exhaustive causal classification. Model equivalence gates exclude no untested defect. Native HUF is the reference-compatible reimplementation from the original framework; it is not falsely labeled the original author executable. Tesseract/Relay/LDPC/GARI source and binary provenance remain in the sealed original framework and every new job summary.


Execution recovery: three complete primary jobs were retained from the initial execution. The interrupted 3188-ID Tesseract prefix remains unchanged and is excluded as an independent estimate; the exact same configuration was retried on all fixed 8000 IDs. If a later stage watchdog left another incomplete Tesseract attempt, the budget-only completion rule can continue its remaining fixed IDs in a fresh process after exact checkpoint replay checks; this retains one unique result per ID and is excluded from dedicated timing. Duplicate predictions were crosschecked and never increase N. An estimated 46.6 minutes of prior active execution are charged to the five-hour planning cap; the offline interruption is excluded. The old worker termination time and uncommitted in-flight work were not recorded, so this is accounted active time with a 30-second allowance, not a certified upper bound on all historical CPU work. The resumed supervisor itself enforces its remaining wall cap. Configuration/source/binary/data locks did not change. Accuracy-run timings across execution dates are auxiliary; dedicated timing is measured entirely in fresh paired workers after recovery. See evidence/P4_recovery_plan.json and recovery_prediction_crosscheck.json.


Mechanistic follow-up (exploratory, no policy changes): failure_attribution/FINAL_ATTRIBUTION.md combines positive cost witnesses from P0/P1 and the fixed selected-policy replay. BP_QUALITY.md compares all eight predeclared BP presets on identical validation syndromes. These diagnostics do not add confirmatory samples.
