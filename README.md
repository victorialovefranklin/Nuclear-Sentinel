# Nuclear Sentinel

## Digital-Twin Framework for Dynamic Cyber-Physical Risk Assessment and Resilience in Nuclear Operational Technology

This public research repository contains reproducible analysis code, derived result tables, publication figures, and the static Nuclear Sentinel Research Dashboard for three experimental stages.

### Experimental program
- **Experiment 1 — HAI/HAIEnd Primary Evaluation:** control/command evidence, physical-process evidence, multimodal B3, and digital-twin-enhanced M1.
- **Experiment 2 — SWaT External Validation:** external transfer, threshold sensitivity, distribution shift, residual behavior, and detection tradeoffs.
- **Experiment 3 — Adaptive & Context-Aware Evaluation (v5):** A0–A5 configurations, adaptive calibration, drift awareness, operating-state context, target-normal digital-twin residual calibration, and B3/M1 hybrid evidence fusion.

### Repository structure
- `scripts/` — Python experiment scripts
- `notebooks/` — available experiment notebooks
- `results/` — derived CSV result and audit tables
- `figures/` — research figures
- `data/README.md` — input manifest and data-access boundary
- `docs/index.html` — GitHub Pages dashboard

### Important research boundaries
HAI/HAIEnd and SWaT are industrial cyber-physical research environments used as proxy environments for methodological evaluation. They are not operational nuclear-facility datasets.

Digital-twin residuals indicate deviation from expected physical behavior. They do not independently prove that a cyberattack occurred.

Nuclear Sentinel is a research and human-supervised decision-support framework, not an autonomous nuclear control system.

### Experiment 3 final v5 result
The final v5 hybrid (A5) reduced false positives from 2,014 under fixed M1 (A1) to 1,483, while attack precision increased from about 32.75% to 37.82%. Recall decreased from about 14.45% to 13.28%, and Macro-F1 remained comparable. Target-normal calibration materially reduced excessive residual exceedance caused by direct source-to-target threshold transfer.

### GitHub Pages
Publish from the `main` branch and `/docs` folder. The dashboard entry point is `docs/index.html`.
