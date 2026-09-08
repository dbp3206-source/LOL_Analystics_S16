# 17 — Testing, reproducibility và regression safety

## 🧠 Mental Model

Test bảo vệ contract; reproducibility bảo vệ khả năng giải thích. Một số tốt nhưng không biết nó sinh ra từ version/config nào thì chưa đủ.

## 📱 Phone Mode

**RUNTIME-VERIFIED**:

```text
Ran 31 tests in about 42.137s
OK
```

Có `PendingDeprecationWarning` từ Seaborn boxplot; warning không làm suite fail.

## 📥 Input

Fixtures nhỏ, deterministic config, temporary SQLite, parser HTML, metric frames.

## ⚙️ Step-by-Step Execution

1. Unit test pure cleaning/metrics.
2. Parser fixture test.
3. DB integration/upsert test.
4. Prediction/backtest regression.
5. Visualization artifact test.
6. Full suite trước commit.
7. Lưu command/version/commit cùng report.

## 📤 Output

Pass/fail, traceback, artifact existence, QA reports. Test không thay thế manual visual review.

## 🔍 Đọc output

Failure đầu tiên thường là root; đọc fixture/input và traceback trước khi sửa downstream.

## 🧪 Simulated Lab

Đổi normalization `TOP` thành `Top` rồi chạy tests: nếu role comparison fail, regression đã bắt đúng.

## ❌ What If?

- Flaky test: tìm clock/network/randomness.
- Test pass nhưng wrong chart: cần assertion semantic/visual inspection.
- Fixture stale: pin expected output và source note.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m unittest discover -s tests -v
```

## 🧪 Automated Test

Full suite 31/31 pass trong current snapshot (**TEST-VERIFIED**).

## 🛠 Nếu kết quả sai thì debug ở đâu?

Test name → fixture → function → upstream contract. Tránh sửa assertion chỉ để xanh.

## 🎤 Bạn phải tự giải thích được

Unit/integration/regression khác nhau; fixture deterministic; vì sao test output không chứng minh dữ liệu internet mới nhất.

## ✅ Checkpoint

Bạn biết test nào bảo vệ parser, DB, metrics, model, visual và biết test chưa bao phủ UI browser.

### 📍 Good stopping point

Chỉ commit khi full suite xanh và limitation được ghi.

