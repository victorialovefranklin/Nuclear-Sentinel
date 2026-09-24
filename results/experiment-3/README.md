# Experiment 3 — Adaptive & Context-Aware Evaluation (v5)

Experiment 3 is a targeted follow-on to the SWaT external-validation experiment.

## Configurations
- A0 — B3 Fixed Baseline
- A1 — M1 Fixed
- A2 — Adaptive M1
- A3 — Drift-Aware M1
- A4 — State-Aware M1
- A5 — B3/M1 Hybrid

## Final v5 interpretation
Target-normal calibration substantially reduced excessive digital-twin residual deviations observed when source-normal thresholds were transferred directly to the external environment. The A5 hybrid reduced false-positive burden and increased attack precision relative to fixed M1 while maintaining comparable overall Macro-F1. Detector behavior differed across operating states.

## Caution
A digital-twin residual is evidence of deviation from expected behavior, not standalone proof of a cyberattack. Target-normal calibration assumes access to a known-normal commissioning/reference period in the target environment.
