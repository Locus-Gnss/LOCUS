# LOCUS Phase 5.5 — XGBoost Supervised Classifier Evaluation Report

**Evaluation Timestamp**: 2026-10-04T12:53:12Z  
**Dataset Inspected**: `data/features/locus_security_features.csv` (9,382 total epochs across 6 sessions)  
**Status**: `UNFITTED_PENDING_LABELLED_SCENARIOS`  
**Security Governance Principle**: **Zero Label Fabrication Safeguard**  

---

## 1. Provenance Audit Finding

In strict accordance with the LOCUS cybersecurity principles and Phase 5.5 directives:
> *"Only perform supervised tuning if legitimate labels exist. Do NOT create fake spoofing/jamming labels. If verified labels do not exist, clearly report which supervised metrics cannot legitimately be calculated."*

The primary feature dataset (`data/features/locus_security_features.csv`) represents authentic, stationary empirical GNSS logs recorded by the hardware receiver in Ahmedabad, India. No intentional radio-frequency interference, meaconing, or kinematic trajectory manipulation was applied during these physical capture sessions.

Consequently, **no legitimate binary or multi-class attack ground truth exists in this dataset**.

---

## 2. Uncalculable Supervised Metrics

Because legitimate attack labels are absent, calculating supervised metrics on this dataset would require hallucinating fictitious labels. The following supervised metrics **cannot legitimately be computed** at this stage:
- **Accuracy**
- **Precision (Attack & Multi-class)**
- **Recall / Detection Rate (PoD)**
- **F1-Score / Macro F1 / Weighted F1**
- **Confusion Matrix**
- **Receiver Operating Characteristic (ROC-AUC)**
- **Precision-Recall Area Under Curve (PR-AUC)**

---

## 3. Tunable Hyperparameters & Search Infrastructure

The supervised XGBoost detector infrastructure has been fully engineered with controlled validation and Optuna search readiness:

```python
search_space = {
    "n_estimators": [100, 200, 300],
    "max_depth": [3, 4, 5, 6],
    "learning_rate": [0.01, 0.03, 0.05, 0.1],
    "subsample": [0.7, 0.8, 0.9],
    "colsample_bytree": [0.7, 0.8, 0.9],
    "min_child_weight": [1, 3, 5],
    "gamma": [0.0, 0.1, 0.2],
    "reg_alpha": [1e-3, 0.1, 1.0],
    "reg_lambda": [1e-3, 0.1, 1.0]
}
```

### Validation Strategy:
- Controlled, session-aware cross-validation across injected scenario episodes.
- Stratified sampling by attack taxonomy (Spoofing, Jamming, Replay, Multipath).
- Test set strictly held out until model acceptance.

---

## 4. Integration into Evidence Bundle

When the Evidence Fusion Engine evaluates an epoch:
```json
"xgboost": {
  "available": false,
  "status": "UNFITTED_PENDING_LABELLED_SCENARIOS",
  "attack_probability": null,
  "predicted_label": null,
  "model_version": "xgb-unfitted-v1.0",
  "note": "Supervised XGBoost requires verified labelled attack scenario data."
}
```
Downstream SOC agents in Phase 6 recognize this status and rely on the physical rule invariants and unsupervised/temporal anomaly detectors.
