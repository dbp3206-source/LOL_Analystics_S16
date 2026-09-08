# 08 — Cleaning, quality gate và data contract

## 🧠 Mental Model

Cleaning làm dữ liệu nhất quán; quality gate quyết định dữ liệu đủ đáng tin để phân tích. Không “xoá outlier” chỉ vì nó khó nhìn.

## 📱 Phone Mode

Ví dụ input/output:

```text
raw role: " TOP " → normalized: "TOP"
raw player: "  Faker  " → "Faker"
raw DPM: "—" → NaN + missing flag
```

Đây là **SOURCE-DERIVED SIMULATION** của `normalize_role`, `normalize_text`, không phải một dòng raw mới tải.

## 📥 Input

Raw parser records, nulls, duplicate keys, academy labels, malformed numeric strings.

## ⚙️ Step-by-Step Execution

1. Chuẩn hoá text/role.
2. Ép kiểu numeric/date.
3. Giữ missing (không điền 0 mù quáng).
4. Loại/đánh dấu duplicate theo key.
5. Lọc S16 và primary LCK theo config.
6. Chạy checks: required, range, uniqueness, freshness, coverage.
7. Ghi quality report trước khi publish chart.

## 📤 Output

`src/quality/cleaning.py` trả giá trị đã canonical; `src/quality/checks.py` trả status/check details; `reports/quality/quality_report.md` là bản đọc được.

## 🔍 Đọc output

`PASS` không có nghĩa source đúng tuyệt đối; nó nghĩa contract nội bộ đạt. Hãy đọc warning (ví dụ missing timeline) và coverage.

## 🧪 Simulated Lab

| raw | rule | clean |
|---|---|---|
| `"Win"` | lower/canonical | `1` |
| `"Loss"` | canonical | `0` |
| `"N/A"` | missing | `NaN` |

Kỳ vọng: report nói rõ số missing, không biến `N/A` thành loss.

## ❌ What If?

- DPM âm: kiểm tra unit/parse, không clip ngay.
- CSD@15 missing: loại khỏi model feature nhưng giữ game cho win-rate.
- Freshness fail: app phải cảnh báo, không báo “live”.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m unittest tests.test_cleaning tests.test_quality -v
```

## 🧪 Automated Test

`tests/test_cleaning.py`, `tests/test_quality.py` được **TEST-VERIFIED** trong 31 tests.

## 🛠 Nếu kết quả sai thì debug ở đâu?

Raw value → cleaning function → quality rule → SQL filter → metric. Ghi một failing fixture nhỏ trước khi sửa.

## 🎤 Bạn phải tự giải thích được

Missing, zero và not-applicable khác nhau thế nào; vì sao quality report phải xuất hiện trước prediction; và tại sao scope S16 là một business rule.

## ✅ Checkpoint

Bạn có thể tạo data contract cho một cột: kiểu, domain, missing policy, source, downstream consumer.

### 📍 Good stopping point

Không bắt đầu EDA nếu chưa biết mỗi cột được clean và validate thế nào.

