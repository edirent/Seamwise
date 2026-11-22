# Conditioned inner-solver comparison

Run `results/solver_comparison/20261110T091016Z`; 168 identical conditioned systems from the P0 exploratory diagnostic corpus. Each problem freezes the same exterior correction, D_J z = D_J x_J and original prior weights. No generator/solver receives truth. True logical-class membership is evaluated offline after candidate generation.

| Workload | Radius | Solver | Systems | Correct class in set | Lowest-cost choice correct | Cheaper correct witness | Mean classes | Mean solve ms |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| surface_d3_p0.003_B4 | 1 | HUF | 32 | 15 | 15 | 0 | 1 | 0.2918 |
| surface_d3_p0.003_B4 | 1 | LSD0 | 32 | 16 | 16 | 2 | 1 | 0.5061 |
| surface_d3_p0.003_B4 | 1 | LSD2 | 32 | 16 | 16 | 3 | 1 | 0.4939 |
| surface_d3_p0.003_B4 | 1 | OSD0 | 32 | 16 | 16 | 2 | 1 | 0.4523 |
| surface_d3_p0.003_B4 | 1 | OSD2 | 32 | 19 | 19 | 7 | 1 | 1.295 |
| surface_d3_p0.003_B4 | 1 | BEAM16 | 32 | 22 | 16 | 0 | 8 | 8.871 |
| surface_d3_p0.003_B4 | 2 | HUF | 32 | 17 | 17 | 1 | 1 | 0.6582 |
| surface_d3_p0.003_B4 | 2 | LSD0 | 32 | 16 | 16 | 3 | 1 | 1.232 |
| surface_d3_p0.003_B4 | 2 | LSD2 | 32 | 14 | 14 | 3 | 1 | 1.303 |
| surface_d3_p0.003_B4 | 2 | OSD0 | 32 | 16 | 16 | 3 | 1 | 1.253 |
| surface_d3_p0.003_B4 | 2 | OSD2 | 32 | 20 | 20 | 12 | 1 | 5.246 |
| surface_d3_p0.003_B4 | 2 | BEAM16 | 32 | 22 | 16 | 0 | 8 | 10.93 |
| surface_d5_p0.006_B4 | 1 | HUF | 32 | 18 | 18 | 0 | 1 | 3.218 |
| surface_d5_p0.006_B4 | 1 | LSD0 | 32 | 20 | 20 | 2 | 1 | 9.042 |
| surface_d5_p0.006_B4 | 1 | LSD2 | 32 | 20 | 20 | 3 | 1 | 9.799 |
| surface_d5_p0.006_B4 | 1 | OSD0 | 32 | 20 | 20 | 2 | 1 | 5.926 |
| surface_d5_p0.006_B4 | 1 | BEAM16 | 32 | 20 | 16 | 1 | 8 | 25.19 |
| surface_d5_p0.006_B4 | 2 | HUF | 32 | 20 | 20 | 7 | 1 | 7.733 |
| surface_d5_p0.006_B4 | 2 | LSD0 | 32 | 22 | 22 | 6 | 1 | 25.28 |
| surface_d5_p0.006_B4 | 2 | LSD2 | 32 | 22 | 22 | 8 | 1 | 24.35 |
| surface_d5_p0.006_B4 | 2 | OSD0 | 32 | 22 | 22 | 6 | 1 | 13.22 |
| surface_d5_p0.006_B4 | 2 | BEAM16 | 32 | 24 | 16 | 1 | 8 | 34.63 |
| bb144_p0.015_B4 | 1 | HUF | 20 | 10 | 10 | 5 | 1 | 4.869 |
| bb144_p0.015_B4 | 1 | LSD0 | 20 | 8 | 8 | 2 | 1 | 55.04 |
| bb144_p0.015_B4 | 1 | LSD2 | 20 | 8 | 8 | 2 | 1 | 55.4 |
| bb144_p0.015_B4 | 1 | OSD0 | 20 | 8 | 8 | 2 | 1 | 8.085 |
| bb144_p0.015_B4 | 1 | BEAM16 | 20 | 8 | 8 | 0 | 8 | 25.86 |
| bb144_p0.015_B4 | 2 | HUF | 20 | 10 | 10 | 0 | 1 | 10.3 |
| bb144_p0.015_B4 | 2 | LSD0 | 20 | 12 | 12 | 0 | 1 | 273.7 |
| bb144_p0.015_B4 | 2 | LSD2 | 20 | 13 | 13 | 0 | 1 | 274.1 |
| bb144_p0.015_B4 | 2 | OSD0 | 20 | 12 | 12 | 0 | 1 | 24.36 |
| bb144_p0.015_B4 | 2 | BEAM16 | 20 | 8 | 8 | 0 | 8 | 56.11 |

HUF/LSD/OSD times are native local solve only, excluding model preparation, bindings, audit extraction and logical scoring. BEAM16 is a bounded **offline Python research prototype**, with its full reference search time; these scopes are not an end-to-end speed comparison. OSD2 is predeclared deferred above 2,500 conditioned fault variables, not marked defeated. Exact configuration-cost CP-SAT results and real-cost bounds are stored per problem; no unknown optimum is replaced by the best observed cost.

The beam examines a model-only pool of at most 128 exact detector-kernel moves, preserving independent logical directions where the limit permits. Width K=16 and depth2 bound generated attempts by 1+128*(1+16). It reserves half the retained slots for distinct logical signatures and fills the rest by configuration cost. This deliberately biased candidate-set coverage is not posterior sampling or exact MAP.

Candidate-set recovery and lowest-cost selection differ materially on surface problems: the beam can contain the correct logical class without the cheapest configuration being in that class. BB144 stronger-solver proposals can be correct yet fail strict descent. Thus a cost-only larger search cannot be assumed to improve logical accuracy. These enriched diagnostic outcomes do not select the deployed policy; fresh independent validation will compare native BP/solver changes and only then bounded candidate/selection variants.

All returned candidates passed D_J z=t_J. The unchanged original native decoder remains the regression baseline. Native multi-candidate code must reproduce the reference beam on tractable fixtures and pass sanitizers/reset/order checks before timing.
