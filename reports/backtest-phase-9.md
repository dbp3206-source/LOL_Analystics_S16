# Phase 9 Walk-forward Model Evaluation

- Games available: `1`
- Baseline games scored: `1`
- Logistic games scored after warm-up: `0`

| Model | Accuracy | Brier score | Log loss |
|---|---:|---:|---:|
| Laplace baseline | 100.0% | 0.2500 | 0.6931 |
| Logistic regression | — | — | — |

- Leakage control: each prediction uses only rows dated before the current game; the current result is appended after scoring.
- Warning: results are descriptive until a materially larger S16 sample is collected.
