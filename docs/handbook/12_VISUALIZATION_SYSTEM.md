# 12 — Visualization: biểu đồ để trả lời câu hỏi

## 🧠 Mental Model

Chart là một câu lập luận trực quan: chọn mark/scale/color theo question, không phải sưu tập loại biểu đồ. Project dùng Matplotlib/Seaborn và SVG fallback.

## 📱 Phone Mode

Đọc gallery trong `reports/figures/` và `README.md`: team comparison, player comparison, champion pool, rolling form, objective timing, matchup radar/heatmap khi dữ liệu đủ. Đây là các artifact đã tạo; không khẳng định phone đã render ảnh nếu chưa có screenshot (**LIMITATION**).

## 📥 Input

Summary DataFrame, metric definition, audience, desired comparison.

## ⚙️ Step-by-Step Execution

1. Chọn question và chart type.
2. Sort có chủ đích, giữ baseline.
3. Dùng palette semantic; tránh rainbow.
4. Annotate unit, sample, period, source.
5. Add uncertainty/baseline nếu phù hợp.
6. Save PNG/SVG và kiểm tra kích thước/label.

`generate_visualizations` và `generate_scientific_visualizations` là entry points; `_generate_svg_fallback` giúp môi trường thiếu plotting dependency.

## 📤 Output

| Question | Visual |
|---|---|
| Ai thắng nhiều hơn? | sorted bar + CI/denominator |
| Form thay đổi? | time line/rolling |
| Nhiều tướng? | lollipop/heatmap |
| Role profile? | radar chỉ khi scales chuẩn hoá |
| Objective theo phút? | distribution/box/strip |

## 🔍 Đọc output

Tên trục phải nói metric/unit; legend không được che data; màu team không được hiểu là causal.

## 🧪 Simulated Lab

Với hai đội, bar chart cho win rate; line chart cho last-5 rolling; heatmap cho role metrics. Một chart = một thông điệp chính.

## ❌ What If?

- Đơn vị khác scale: chuẩn hoá hoặc tách panel, không chồng mù.
- Label dài: wrap/rotate, không cắt tên.
- Một màu: có thể vẫn đúng nhưng mất encoding; dùng palette có ý nghĩa.

## 💻 Try It Yourself

Chạy visualization command trong `docs/RUNBOOK.md`; mở các file trong `reports/figures/` bằng VS Code Explorer.

## 🧪 Automated Test

`tests/test_visualizations.py` kiểm tra file/structure; 31/31 tests pass (**TEST-VERIFIED**). Seaborn có `PendingDeprecationWarning` ở boxplot, chưa phải failure.

## 🛠 Nếu kết quả sai thì debug ở đâu?

DataFrame trước chart → sort/filter → function kwargs → saved file → visual label. Không sửa màu để che metric bug.

## 🎤 Bạn phải tự giải thích được

Vì sao bar, line, heatmap, radar có trade-off; vì sao 3D/dual-axis thường gây hiểu nhầm; vì sao chart cần denominator.

## ✅ Checkpoint

Bạn chọn được ít nhất 5 visual khác nhau và giải thích câu hỏi mà mỗi visual trả lời.

### 📍 Good stopping point

Khi bạn có thể xoá một chart “đẹp nhưng vô ích” mà không mất insight.

