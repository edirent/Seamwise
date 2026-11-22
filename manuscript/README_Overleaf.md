# Seamwise unified manuscript

Select main.tex and compile with pdfLaTeX twice in Overleaf. All figures, tables and bibliography entries are included. Python is not required to compile the paper.

The manuscript presents one Seamwise method: ownership-based initialization, fixed-exterior boundary repair, logical-reach certificates, a merge-persistent HUF backend, and exact composition rules. Complexity derivations remain in Appendix J; the main text states the key bounds.

The new study covers 24 circuit configurations, 168 requested backend/configuration jobs, 136 complete measurement jobs, 37 complete oracle pairs (2,560 paired shot executions), and 18 additional independent-process timing repetitions. Reused timing inputs do not add independent logical samples. The separate experiment archive contains all data, source, input hashes, raw outputs, cluster histories, non-completion logs, profiling and reproduction commands.

The two HUF modes are newly authored reference implementations, with a documented additional BP-assisted residual variant. They are not the original authors' binary. External Tesseract, BP+LSD2 and BP+OSD2 runs use native packages. Unavailable 2026-specific adapters remain explicitly unmeasured. Related work remains cited.

The paper reports deterministic output preservation and conditional work bounds, plus measured latency improvements at selected operating points. It does not claim universal superiority, a threshold, or completed 2026 baseline coverage. The finite logical-failure and process-memory measurements are reported with their scope and limitations.

The six original Seamwise figures are retained. The additional scaling and cluster figures come from the measured pilot. New source/data can be found in the companion experiments archive (an artifact bundle, not a separate research method).
