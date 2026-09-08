# 15 — Walk-forward, leakage và model evaluation

## 🧠 Mental Model

Mỗi trận trong quá khứ phải được dự đoán bằng những gì đã biết ngay trước trận. Walk-forward mô phỏng đúng operational reality: train mở rộng → predict trận kế → cập nhật.

## 📱 Phone Mode

```text
Games: G1 G2 G3 G4 G5
Train: G1-G2 → predict G3
Train: G1-G3 → predict G4
Train: G1-G4 → predict G5
```

## 📥 Input

Chronological game rows, team features, target win, minimum training window.

## ⚙️ Step-by-Step Execution

1. Sort by timestamp.
2. Create features using rows `< current_game`.
3. Define folds.
4. Fit only train slice.
5. Score next slice.
6. Aggregate and compare baseline.
7. Audit leakage checklist.

## 📤 Output

Fold table: train end, test game/date, prediction, actual, log-loss/Brier/accuracy; plus aggregate confidence.

## 🔍 Đọc output

Nếu fold đầu skipped vì insufficient history, đó là expected. Một aggregate không thay thế fold-level diagnostics.

## 🧪 Simulated Lab

Feature `recent_win_rate` của G4 dùng G1–G3; nếu dùng G4, bug. Hãy tự đánh dấu từng row trước khi xem đáp án.

## ❌ What If?

- Random split: optimistic bias.
- H2H includes future meeting: leakage.
- Same series game split across train/test: dependence; cân nhắc series-level split.

## 💻 Try It Yourself

Đọc `src/modeling/backtest.py` và report backtest; dùng tests trước khi thay model.

## 🧪 Automated Test

`tests/test_backtest.py` cùng suite 31/31 pass; metrics logistic/backtest đã được kiểm tra.

## 🛠 Nếu kết quả sai thì debug ở đâu?

In feature date range alongside target date; kiểm tra fold boundaries và source query WHERE clause.

## 🎤 Bạn phải tự giải thích được

Leakage là gì, vì sao time series khác i.i.d., và tại sao prediction accuracy cần baseline.

## ✅ Checkpoint

Bạn vẽ được timeline train/test và chỉ ra dữ liệu nào bị cấm dùng tại prediction time.

### 📍 Good stopping point

Chỉ mở rộng model khi backtest protocol ổn định và có test regression.

