# 14 — Logistic Regression và cách đọc model

## 🧠 Mental Model

Logistic Regression học log-odds tuyến tính rồi map về probability. Trong project đây là model minh hoạ có thể giải thích, không phải claim “AI thắng mọi trận”.

## 📱 Phone Mode

```text
z = intercept + w1*form_diff + w2*h2h_diff
p = 1 / (1 + exp(-z))
```

Nếu `z=0`, `p=0.5`; nếu z dương, team A có xác suất cao hơn. Đây là toy trace, không phải coefficient runtime hiện tại.

## 📥 Input

Rows theo trận với feature trước trận và target win. Cần chronological split.

## ⚙️ Step-by-Step Execution

1. Sort by match date.
2. Construct pre-game rolling feature.
3. Train on past, test on future.
4. Fit logistic (scikit-learn nếu available hoặc fallback rõ ràng).
5. Predict probabilities.
6. Report accuracy/log-loss/Brier/confusion + baseline.

## 📤 Output

`run_backtest` trả fold metrics và aggregate; report chỉ publish khi có đủ rows/fold.

## 🔍 Đọc output

Accuracy 0.60 không nói model calibrated; log-loss phạt dự đoán quá tự tin. So với majority baseline.

## 🧪 Simulated Lab

Ba trận đầu train, trận 4 test. Nếu feature trận 4 chứa kết quả trận 4, đó là leakage dù accuracy rất cao.

## ❌ What If?

- Few games: không overfit/không khoe coefficient.
- Class imbalance: xem baseline và confusion.
- Solver unavailable: report limitation, không gọi fallback là production ML.

## 💻 Try It Yourself

Chạy backtest command trong `docs/RUNBOOK.md`; mở report để xem fold chronology.

## 🧪 Automated Test

`tests/test_backtest.py` bảo vệ metrics/leakage assumptions; 31 tests pass.

## 🛠 Nếu kết quả sai thì debug ở đâu?

Cutoff/feature builder → split index → model fit → metric aggregation → report.

## 🎤 Bạn phải tự giải thích được

Odds/log-odds, sigmoid, coefficient sign, regularization, calibration, baseline và chronological validation.

## ✅ Checkpoint

Bạn tự giải thích được tại sao accuracy cao do leakage là kết quả xấu.

### 📍 Good stopping point

Chuyển sang walk-forward khi đã đọc được một coefficient nhưng không diễn giải causal.

