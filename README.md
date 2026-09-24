# Nuclear Sentinel

## Digital-Twin Framework for Dynamic Cyber-Physical Risk Assessment and Resilience in Nuclear Operational Technology

**Victoria Love Franklin**  
Ph.D. Data Science Research Scholar  
School of Applied Computational Sciences  
Meharry Medical College

---

## 🌐 Nuclear Sentinel Research Website

### [Launch the Nuclear Sentinel Research Website](https://victorialovefranklin.github.io/Nuclear-Sentinel/)

The **Nuclear Sentinel Research Website** is the interactive companion to this repository. It presents the research framework, research questions, experimental methodology, results, figures, digital-twin analysis, cross-experiment findings, and supporting technical documentation.

**Website:**  
https://victorialovefranklin.github.io/Nuclear-Sentinel/

**GitHub Repository:**  
https://github.com/victorialovefranklin/Nuclear-Sentinel

---

## About Nuclear Sentinel

**Nuclear Sentinel** is a doctoral research framework investigating how control-system information, physical-process measurements, digital-twin context, and data-driven detection methods can be integrated to support dynamic cyber-physical risk assessment and resilience in nuclear operational technology (OT).

The research examines whether combining multiple forms of cyber-physical evidence can improve the recognition and interpretation of abnormal system behavior while providing information that can support human-supervised cybersecurity and resilience decisions.

The experimental program progresses from primary industrial control-system evaluation to external validation and then to adaptive, context-aware detection.

Nuclear Sentinel is designed as a **research and decision-support framework**. It is not an autonomous nuclear control system.

---

## Research Objective

The primary objective of Nuclear Sentinel is to investigate whether control-system, equipment, sensor, and physical-process information can be combined with digital-twin context to improve the recognition and interpretation of abnormal cyber-physical behavior.

The broader framework connects:

**Control & Command Evidence**  
↓  
**Physical-Process Evidence**  
↓  
**Digital-Twin Context**  
↓  
**Abnormal-State Detection**  
↓  
**Cyber-Physical Risk Assessment**  
↓  
**Human-Supervised Decision Support**  
↓  
**Response & Resilience**

---

## Primary Research Question

> **Can control-system, equipment, sensor, and physical-process information be combined with a digital twin to better recognize abnormal system behavior, understand what may be affected, determine how serious an event may be, and support decisions about response and recovery in nuclear operational technology systems?**

The current experimental work directly evaluates abnormal-state detection and the contribution of digital-twin context.

Cyber-physical risk assessment, response, and recovery represent broader components of the Nuclear Sentinel framework and require additional evaluation beyond the current detection experiments.

---

# Experimental Evaluation

The Nuclear Sentinel experimental program contains three connected experiments.

## Experiment 1 — HAI/HAIEnd Primary Evaluation

Experiment 1 establishes the primary evaluation of the Nuclear Sentinel detection architecture using the HAI and HAIEnd industrial control-system datasets.

The experiment compares four evidence configurations:

- **B1 — Control/Command Evidence**
- **B2 — Physical-Process Evidence**
- **B3 — Combined Control + Physical Evidence**
- **M1 — Combined Evidence + Digital-Twin Context**

Digital-twin residuals represent differences between expected and observed physical-process behavior.

Three detection approaches are evaluated:

- Isolation Forest
- Random Forest
- Histogram Gradient Boosting

Performance measures include:

- Macro-F1
- Attack precision
- Attack recall
- False-positive rate
- Average precision
- Confusion matrices
- Detection latency
- Bootstrap confidence intervals
- Feature-importance analysis

### Experiment 1 Finding

The experiment demonstrates that digital-twin context can provide useful additional information for recognizing abnormal cyber-physical behavior, but the magnitude of the benefit depends on the detection algorithm.

The strongest improvement was observed for the Isolation Forest configuration, while supervised models produced smaller or mixed changes.

Therefore, the Experiment 1 results do **not** support a claim that digital-twin context universally improves every detector.

---

## Experiment 2 — SWaT External Validation

Experiment 2 evaluates whether the Nuclear Sentinel architecture transfers to a different industrial cyber-physical environment using the **Secure Water Treatment (SWaT)** testbed.

The same general evidence structure is retained:

- **B1 — Actuator/Control-State Evidence**
- **B2 — Physical Sensor Evidence**
- **B3 — Combined Control + Physical Evidence**
- **M1 — Combined Evidence + Digital-Twin Residuals**

The experiment evaluates:

- External validity
- Digital-twin transfer
- Detection tradeoffs
- Threshold sensitivity
- Distribution shift
- Scenario-dependent behavior

### Experiment 2 Finding

The architecture transferred technically to SWaT, but its behavior differed substantially from the primary HAI/HAIEnd experiment.

At the primary threshold, adding digital-twin residuals increased attack recall and reduced detection latency but also produced substantially more false positives.

Threshold-sensitivity analysis showed that performance depended strongly on calibration.

The external validation therefore demonstrates that digital-twin evidence cannot be assumed to transfer uniformly between operating environments.

---

## Experiment 3 — Adaptive & Context-Aware Evaluation

Experiment 3 investigates the calibration and transfer problems identified during external validation.

The experiment evaluates fixed, adaptive, drift-aware, state-aware, and hybrid detection strategies.

The primary configurations are:

- **A0 — B3 Fixed**
- **A1 — M1 Fixed**
- **A2 — Adaptive M1**
- **A3 — Drift-Aware M1**
- **A4 — State-Aware M1**
- **A5 — B3/M1 Hybrid**

Experiment 3 examines:

- Adaptive calibration
- Distribution shift
- Operating context
- Digital-twin residual transfer
- Target-normal calibration
- Hybrid detection
- Evidence fusion

### Experiment 3 v5 Results

The final v5 evaluation showed that target-normal calibration substantially reduced the excessive digital-twin residual deviations observed when source-normal thresholds were transferred directly to the external environment.

For the **A5 B3/M1 Hybrid** configuration:

| Metric | Result |
|---|---:|
| Macro-F1 | 0.5830 |
| Attack Precision | 37.82% |
| Attack Recall | 13.28% |
| False-Positive Rate | 1.26% |
| False Positives | 1,483 |

Compared with fixed M1 (**A1**), the hybrid configuration reduced false positives from **2,014 to 1,483**, a reduction of **531 false positives**, or approximately **26%**.

Attack precision increased from approximately **32.75% to 37.82%**, while attack recall decreased from approximately **14.45% to 13.28%**.

The A5 and A1 configurations produced comparable overall Macro-F1 performance.

Bootstrap analysis found:

- **A5 − A0 Macro-F1:** approximately **+0.0597**
- **95% CI:** approximately **+0.0067 to +0.1251**

For A5 compared with A1:

- **A5 − A1 Macro-F1:** approximately **−0.0011**
- **95% CI:** approximately **−0.0126 to +0.0096**

These findings do not establish that A5 is universally superior to fixed M1. Instead, they demonstrate an improved false-alarm and precision tradeoff under the tested configuration while maintaining comparable overall Macro-F1.

---

# Cross-Experiment Finding

Across the three experiments, the evidence supports the following conclusion:

> **Digital-twin context provides additional information for recognizing abnormal cyber-physical behavior, but its contribution depends on detector calibration, operating conditions, and distribution stability. Fixed residual and anomaly thresholds do not transfer uniformly across operating environments, supporting the need for context-aware calibration and human-supervised interpretation of digital-twin evidence within Nuclear Sentinel.**

The results also demonstrate why abnormal digital-twin residuals should be treated as **evidence requiring interpretation**, rather than automatic proof of a cyberattack.

---

# Repository Structure

```text
Nuclear-Sentinel/
│
├── data/
│   └── README.md
│
├── docs/
│   └── index.html
│
├── figures/
│   ├── experiment-1/
│   ├── experiment-2/
│   └── experiment-3/
│
├── notebooks/
│   └── experiment_3_adaptive_context_v5.ipynb
│
├── results/
│   ├── experiment-1/
│   ├── experiment-2/
│   └── experiment-3/
│
├── scripts/
│   ├── experiment_1_hai_haiend.py
│   ├── experiment_2_swat_external_validation.py
│   └── experiment_3_adaptive_context_v5.py
│
├── .gitignore
├── README.md
└── requirements.txt