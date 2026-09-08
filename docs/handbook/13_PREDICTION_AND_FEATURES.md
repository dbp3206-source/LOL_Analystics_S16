# 13 — Prediction: từ phân tích sang xác suất có điều kiện

## 🧠 Mental Model

Predictor không nói đội “chắc thắng”; nó ước lượng xác suất dựa trên feature đã biết trước trận. Feature contract quan trọng hơn model fancy.

## 📱 Phone Mode

Input mô phỏng:

```json
{"team_a":"T1","team_b":"HLE","a_recent_win_rate":0.60,"b_recent_win_rate":0.55,"a_h2h":0.50}
```

Output mô phỏng: `p_team_a=0.57`, `p_team_b=0.43`, `confidence=LOW/MEDIUM` tùy sample. Đây là **SOURCE-DERIVED SIMULATION**, không phải prediction live.

## 📥 Input

Team form, head-to-head, side/context features, fixture teams; no post-match values.

## ⚙️ Step-by-Step Execution

1. Chốt prediction time.
2. Build rolling aggregates up to cutoff.
3. Align A/B feature names and missing policy.
4. Fit/score model or heuristic baseline.
5. Calibrate/interpret probability.
6. Return reason codes, sample size và caveat.

`src/modeling/predictor.py` là heuristic matchup predictor; `src/modeling/backtest.py` dùng Logistic Regression walk-forward.

## 📤 Output

Prediction gồm probability, predicted side, feature snapshot, data cutoff, model/baseline, limitation.

## 🔍 Đọc output

Probability 0.57 nghĩa 57/100 kỳ vọng dưới assumptions, không phải “độ tự tin cảm tính” hay guarantee.

## 🧪 Simulated Lab

Nếu form gần nhau và H2H yếu, output phải gần 0.5; một metric vượt trội không tự biến thành 0.9.

## ❌ What If?

- Missing next fixture: trả “no fixture found”, không đoán đối thủ.
- Feature NaN: dùng policy rõ ràng hoặc không score.
- Model score tốt trên random split nhưng tệ time split: nghi leakage.

## 💻 Try It Yourself

Dùng predict commands trong `docs/RUNBOOK.md`; đọc JSON/Markdown output và truy ngược feature.

## 🧪 Automated Test

`tests/test_prediction.py`, `tests/test_backtest.py` thuộc suite 31/31 pass (**TEST-VERIFIED**).

## 🛠 Nếu kết quả sai thì debug ở đâu?

Fixture cutoff → feature values → model coefficients → probability transform → report wording.

## 🎤 Bạn phải tự giải thích được

Prediction khác causal explanation; baseline khác ML; calibration khác accuracy; và vì sao up-to-date chưa đồng nghĩa predictive.

## ✅ Checkpoint

Bạn có thể in prediction kèm “as-of date, feature source, sample size, limitation”.

### 📍 Good stopping point

Trước khi backtest, bạn đã chứng minh không dùng dữ liệu tương lai.

