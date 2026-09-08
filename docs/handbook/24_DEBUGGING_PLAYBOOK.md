# 24 — Debugging playbook

## 🧠 Mental Model

Debug theo data lineage, không đoán từ screenshot. Tìm điểm đầu tiên output lệch expected.

## 📱 Phone Mode

| Symptom | Trace first | Common cause |
|---|---|---|
| Chart trống | DataFrame shape → query | wrong season/team filter |
| Win rate sai | grain/denominator | duplicated join |
| Prediction quá cao | cutoff/features | leakage/few sample |
| Parser 0 rows | raw HTML/fixture | source schema drift |
| Dữ liệu stale | timestamp/cache | update failed |
| Test import fail | venv/PYTHONPATH | wrong interpreter |
| Streamlit crash | config/DB path | run from wrong cwd |

## ⚙️ Step-by-Step Execution

1. Reproduce with smallest fixture.
2. Print input shape/dtypes/keys.
3. Compare expected vs actual at first boundary.
4. Add regression test.
5. Fix root layer and rerun full suite.

## 🧪 Simulated Lab

Nếu T1 xuất hiện hai lần sau merge, kiểm tra uniqueness của right frame trước khi đổi chart aggregation.

## ❌ Anti-patterns

Không catch mọi exception rồi trả empty; không sửa DB bằng tay; không tắt warning/test để xanh.

## 💻 Try It Yourself

Chạy health, show-config, tests rồi trace một failed artifact theo bảng trên.

## ✅ Checkpoint

Bạn mô tả được bug bằng `input → first wrong output → root cause → regression test → fix`.

