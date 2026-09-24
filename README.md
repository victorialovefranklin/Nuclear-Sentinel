# Nuclear Sentinel

## A Digital-Twin Framework for Dynamic Cyber-Physical Risk Assessment and Resilience in Nuclear Operational Technology

**Nuclear Sentinel** is a doctoral research framework investigating how control-system evidence, physical-process measurements, digital-twin context, calibration, and operating conditions can support cyber-physical monitoring, risk assessment, and resilience decision support.

## Research Objectives

1. Establish a reproducible cyber-physical evidence architecture.
2. Evaluate abnormal-state detection, digital-twin context, cross-environment transfer, and calibration.
3. Extend validated evidence toward consequence-aware risk and human-supervised resilience decision support.

## Experimental Program

### Experiment 1 - HAI/HAIEnd Primary Evaluation
Evaluates control and command evidence, physical-process evidence, combined multimodal evidence, and digital-twin residual context.

### Experiment 2 - SWaT External Validation
Evaluates how the framework behaves in a different industrial cyber-physical environment and examines transfer, threshold sensitivity, and distribution shift.

### Experiment 3 - Adaptive and Context-Aware Evaluation
Evaluates calibration, operating-state context, digital-twin residual transfer, target-normal calibration, and hybrid evidence fusion.

## Research Architecture

Control & Command Evidence + Physical-Process Evidence  
? Digital-Twin Context  
? Abnormal-State Detection  
? System-State Interpretation  
? Cyber-Physical Risk Context  
? Human-Supervised Response and Resilience

## Repository Structure

- `docs/` - research documentation, methods, literature, and proposal materials
- `experiments/` - experiment-specific materials
- `notebooks/` - Jupyter notebooks
- `scripts/` - reproducible analysis scripts
- `figures/` - research figures
- `results/` - experimental outputs
- `dashboard/` - Nuclear Sentinel Research Dashboard
- `references/` - reference-management materials
- `data/` - local research datasets excluded from Git

## Research Boundaries

HAI/HAIEnd and SWaT are industrial cyber-physical research environments used as proxy environments for methodological evaluation. They are not operational nuclear-facility datasets.

Digital-twin residuals represent differences between observed and expected physical behavior. A large residual provides evidence of abnormal behavior but does not independently establish that a cyberattack occurred.

Nuclear Sentinel is designed as a research and human-supervised decision-support framework. It is not an autonomous nuclear control system.

## Research Status

Doctoral research in progress.
