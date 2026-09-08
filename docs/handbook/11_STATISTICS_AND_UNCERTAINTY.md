# 11 — Statistics: biến mô tả thành bằng chứng

## 🧠 Mental Model

Statistics không làm pattern “đúng” tự động. Nó lượng hoá uncertainty, sample size và effect size để tránh kết luận quá tay.

## 📱 Phone Mode

Production có `wilson_interval`, `binomial_summary`, `compare_rates`, `cohens_d`. Wilson phù hợp hơn tỷ lệ nhỏ/biên; Cohen’s d mô tả độ lớn chênh lệch trung bình.

## 📥 Input

Binary outcomes (win/loss), metric vectors (DPM/KDA), grouping (team/player/side), alpha và hypothesis.

## ⚙️ Step-by-Step Execution

1. Viết H0/H1 trước khi xem p-value.
2. Chọn unit độc lập hợp lý.
3. Tính point estimate + interval.
4. Tính effect size.
5. Kiểm tra assumptions và multiple comparisons.
6. Kết luận theo ngữ cảnh, không chỉ `p < .05`.

## 📤 Output

Report `reports/statistics/statistics_report.md` chứa interval, tests, dependency status và caveat. Nếu SciPy unavailable, report nói rõ thay vì giả lập p-value.

## 🔍 Đọc output

CI rộng thường nghĩa sample nhỏ/biến động cao. “Không có bằng chứng khác biệt” không phải “hai đội giống hệt”.

## 🧪 Simulated Lab

T1 8/12 và HLE 7/12: chênh lệch nhỏ, sample nhỏ; hãy báo interval và thực dụng nghiệp vụ (“cần xem matchup/context”), không claim certainty.

## ❌ What If?

- P-value nhỏ nhưng effect tiny: nêu cả hai.
- Nhiều champion tests: ghi multiple testing limitation.
- Player rows phụ thuộc cùng game: không giả định hoàn toàn độc lập.

## 💻 Try It Yourself

Đọc `src/analysis/statistics.py`, chạy test statistics trong `tests/test_statistics.py` nếu có; nếu test group chưa tách, chạy full suite.

## 🧪 Automated Test

Các test statistics thuộc suite 31 tests (**TEST-VERIFIED**); scipy dependency status được report runtime kiểm tra.

## 🛠 Nếu kết quả sai thì debug ở đâu?

Hypothesis → denominator → dependency status → test implementation → interpretation text.

## 🎤 Bạn phải tự giải thích được

CI, p-value, effect size, power, independence và selection bias bằng ví dụ T1/HLE.

## ✅ Checkpoint

Bạn không dùng câu “T1 chắc chắn mạnh hơn” nếu interval overlap/sample/context chưa ủng hộ.

### 📍 Good stopping point

Sau khi phân biệt mô tả (EDA) và suy luận (statistics), sang visualization.

