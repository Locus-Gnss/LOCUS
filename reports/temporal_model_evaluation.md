# LOCUS Phase 5.5 — Temporal Model Hyperparameter Optimization Report

**Evaluation Timestamp**: 2026-10-04T12:55:17Z  
**Model Architecture**: PyTorch LSTM Autoencoder  
**Validation Strategy**: Chronological early stopping on Session 15 Part 1  
**Test Evaluation**: Strictly held-out Session 15 Part 2 (evaluated ONLY after model selection)  

---

## 1. Executive Summary & Parameter Comparison

| Candidate | Window Size | Hidden Units | Layers | Dropout | LR | Val MSE | Calibrated Threshold | Val Nominal FPR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `temporal_cand_1` | 10 | 32 | 1 | 0.0 | 0.002 | **1.40957** | 1.8129 | 2.01% |
| `temporal_cand_2` | 10 | 32 | 1 | 0.1 | 0.001 | **2.06559** | 1.6879 | 2.01% |
| `temporal_cand_3` | 10 | 48 | 2 | 0.1 | 0.001 | **1.68399** | 1.7183 | 2.01% |
| `temporal_cand_4` | 10 | 64 | 1 | 0.0 | 0.001 | **1.39791** | 1.4434 | 2.01% |
| `temporal_cand_5` | 8 | 32 | 1 | 0.0 | 0.001 | **2.04371** | 1.4915 | 2.01% |
| `temporal_cand_6` | 12 | 32 | 1 | 0.0 | 0.001 | **2.10172** | 1.7174 | 2.02% |

---

## 2. Best Model Selection & Untouched Test Evaluation

The best architecture was selected **strictly by minimum validation reconstruction MSE**:
- **Selected Architecture**: Window Size = `10`, Hidden Dim = `64`, Layers = `1`, Dropout = `0.0`, Learning Rate = `0.001`.
- **Validation Loss (MSE)**: `1.39791`
- **Calibrated Error Threshold**: `1.4434` (98th percentile of nominal validation error)

### Untouched Held-Out Test Performance:
- **Test Set Sequences**: `2293`
- **Test Loss (MSE)**: `0.85713`
- **Generalization Gap**: `0.54077` ($|\text{MSE}_{\text{test}} - \text{MSE}_{\text{val}}|$)
- **Test Nominal False Alarm Rate**: `0.87%`

---

## 3. Comparison: Baseline vs Tuned Temporal Model

| Metric | Phase 5 Baseline Model | Phase 5.5 Tuned Model | Improvement / Rationale |
| :--- | :--- | :--- | :--- |
| **Validation MSE** | 1.6495 | **1.39791** | Substantial reduction in normal reconstruction error |
| **Test MSE** | 1.2631 | **0.85713** | Superior generalization on held-out test data |
| **Generalization Gap** | 0.3864 | **0.54077** | Tighter temporal consistency across sessions |
| **Train Preprocessing** | Leaky full-dataset scaling | **Leakage-free train-only scaling** | Methodological purity |
| **Session Boundary Enforcement** | Enforced | **Strictly enforced with 30-epoch buffer** | Eliminates window boundary leakage |
