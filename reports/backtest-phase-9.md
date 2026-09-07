# Phase 9 Walk-forward Model Evaluation

- Games available: `581`
- Baseline games scored: `581`
- Logistic games scored after warm-up: `577`

| Model | Accuracy | Brier score | Log loss |
|---|---:|---:|---:|
| Laplace baseline | 59.6% | 0.2375 | 0.6679 |
| Logistic regression | 60.1% | 0.2399 | 0.6764 |

- Leakage control: each prediction uses only rows dated before the current game; the current result is appended after scoring.
- Warning: results are descriptive until a materially larger S16 sample is collected.
