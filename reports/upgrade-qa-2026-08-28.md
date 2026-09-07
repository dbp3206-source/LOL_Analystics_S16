# Báo cáo nghiệm thu nâng cấp — 28/08/2026

## 1. Kết luận

Project đã đạt quy mô phù hợp một bài tập lớn Python năm 3 theo hướng DA/DS: có pipeline thu thập dữ liệu thật, raw archive, SQLite, làm sạch/quality gate, EDA, thống kê nhập môn, trực quan hóa đa dạng, so sánh đội/tuyển thủ, mô hình dự báo cơ bản và giao diện demo viết bằng Python.

Điểm benchmark nội bộ: **96/100 (9,6/10)**. Đây là điểm theo bằng chứng chạy trong workspace, không phải điểm môn học được bảo đảm trước.

| Nhóm tiêu chí | Điểm | Bằng chứng chính |
|---|---:|---|
| Bám phạm vi S16/LCK/Gol.gg và đúng bài toán | 20/20 | 10 LCK primary, external opponents chỉ làm dữ liệu phụ, không đưa S15 vào core |
| Python + nghiệp vụ DA/DS | 19/20 | Requests/BS4 → SQLite → Pandas/NumPy → statistics → visualization → modeling |
| Chất lượng dữ liệu và tái lập | 19/20 | cache/retry/hash manifest, incremental upsert, freshness 24h, 12/12 data gates |
| Visualization và problem solving | 19/20 | 14 scientific PNG + 6 notebook PNG, mỗi hình gắn câu hỏi/mẫu/giới hạn |
| Khả năng học, chạy và demo trên VS Code | 19/20 | notebook 38 cell, 3 tài liệu học tập, task/demo offline, Streamlit browser QA 6 mode |

Trừ 4 điểm vì website nguồn có thể đổi HTML; nguồn lịch hiện chưa cung cấp fixture tương lai; mô hình mới là baseline giáo dục chưa calibration/production-grade; có một cảnh báo deprecation từ nội bộ Seaborn khi chạy test.

## 2. Snapshot dữ liệu đã kiểm chứng

- Freshness: `fresh`; update thành công gần nhất `2026-08-28T02:52:28.194197+00:00`, giới hạn 24 giờ.
- 642 games, ngày thi đấu mới nhất `2026-08-27`, 264 series.
- 12.840 draft actions, đúng 20 hành động/game theo quality gate.
- 5.572 timeline objective events trên 641/642 games.
- 6.420 player-game rows; DPM/CSM đủ 6.420, GD@15/CSD@15 có 6.410. Mười giá trị thiếu được giữ `NULL`, không impute tùy tiện.
- Dataset phân tích: 1.198 primary team-game rows và 5.147 current-starter player-game rows.
- 152 player dimensions, 160 roster-period rows; truy vấn roster scope xác định 50 starter hiện tại của 10 đội.
- Quality report: 12/12 checks passed, không có affected row.

## 3. Review source code và mức độ dễ học

### Luồng code

1. `src/collection`: request có rate limit/cache/retry, lưu raw HTML, checksum và manifest; parser chuyển HTML sang dataclass có grain rõ ràng.
2. `src/storage`: schema quan hệ và idempotent upsert vào SQLite.
3. `src/quality`: chuẩn hóa dimension/role, kiểm tra season, lineup, numeric domain, draft và timeline.
4. `src/analysis`: Pandas EDA, metrics, thống kê, comparison và scientific visualization.
5. `src/modeling`: feature chỉ dùng lịch sử trước trận, baseline và Logistic Regression walk-forward.
6. `app`: Streamlit ghép các module thành sản phẩm demo.

Các module trọng yếu đã có docstring/comment giải thích **ý nghĩa nghiệp vụ, grain, input/output và quyết định dễ sai**. Không comment lại từng cú pháp hiển nhiên, vì kiểu “mỗi dòng một comment” làm code khó đọc và không phản ánh clean code. Phần cầm tay chỉ việc theo từng lệnh/cell nằm trong `docs/02_VSCODE_HANDS_ON_GUIDE.md`; lý thuyết và template tái sử dụng nằm trong `docs/03_DA_DS_PLAYBOOK.md`.

AST audit cuối: **163/163 function/class definitions có docstring**. Inline comments tiếp tục tập trung vào các đoạn dễ sai như season quarantine, cache/retry, paired-test assumption, temporal cutoff, role scope và leakage; các phép gán/cú pháp hiển nhiên không bị comment lặp lại.

### Mức độ năm 3

- Phần bắt buộc chỉ dùng EDA, groupby/crosstab/correlation, Wilson CI, z-test, Welch t-test, Cohen's d, baseline và Logistic Regression.
- Không đưa Deep Learning, Bayesian modeling nâng cao, causal inference, distributed processing, Random Forest/GridSearch vào core.
- Chi-square side × outcome được giữ như ví dụ kiểm tra assumption và mang `assumption_warning`, vì blue/red là hai quan sát ghép cặp của cùng game.

## 4. Review phân tích và visualization

Scientific renderer đã sinh 14 PNG:

1. missingness heatmap;
2. win-rate lollipop;
3. economy-win bubble scatter;
4. standardized team profile heatmap;
5. DPM boxplot theo role;
6. KDA violin theo role;
7. side-outcome 100% stacked bar;
8. lower-triangle correlation heatmap;
9. rolling-form sequential small multiples;
10. champion-pool bubble;
11. tournament-context heatmap;
12. role-baseline heatmap;
13. T1–HLE standardized dumbbell;
14. same-role starter matchup heatmap.

Notebook sinh thêm 6 hình để người học chạy từng cell. Các hình có title, câu hỏi nghiệp vụ, sample size/denominator, chú thích nguồn hoặc giới hạn. Rolling form đã được sửa từ trục ngày nối qua khoảng nghỉ sang **game order + step line**, tránh ngụ ý có dữ liệu ở những ngày không thi đấu. Violin chỉ clip p99 khi hiển thị, không làm thay đổi dữ liệu gốc. Champion win rate dùng ngưỡng mẫu tối thiểu.

## 5. Thống kê và dự báo

- T1: 93/147 wins, 63,3%, Wilson 95% CI 55,2%–70,6%.
- HLE: 85/134 wins, 63,4%, Wilson 95% CI 55,0%–71,1%.
- Two-proportion z-test: p = 0,9768; chưa đủ bằng chứng nói tỷ lệ thắng tổng thể khác nhau.
- Welch t-test GDM: p = 0,8716; Cohen's d = -0,0194, hiệu ứng quan sát rất nhỏ.
- Chi-square side × outcome: p-value chỉ để minh họa quy trình; **không dùng kết luận xác nhận** vì vi phạm giả định độc lập.
- Backtest walk-forward: baseline 556 dự đoán, accuracy 59,4%, Brier 0,2373, log loss 0,6676. Logistic Regression 552 dự đoán, accuracy 60,0%, Brier 0,2400, log loss 0,6768. Logistic tốt hơn nhẹ về accuracy nhưng baseline tốt hơn ở hai probability metrics; không cherry-pick một metric để tuyên bố mô hình phức tạp hơn luôn tốt hơn.
- Sample T1–HLE hiện là `hypothetical`: T1 50,17%, HLE 49,83%. Chênh lệch rất nhỏ và không được gọi là dự đoán “trận tiếp theo” khi chưa có fixture tương lai hợp lệ.

## 6. Bằng chứng chạy/QA

- Python 3.12.13; NumPy 2.3.5; Pandas 2.3.3; Matplotlib 3.10.9; Seaborn 0.13.2; SciPy 1.18.1; Statsmodels 0.15.0; scikit-learn 1.9.0; Streamlit 1.62.0.
- `scripts/verify_environment.py`: `status=ready`, không thiếu package.
- Source audit đã chạy lại trực tiếp với Gol.gg; robots.txt không cấm các path `/teams/` và `/game/stats/` đang dùng, raw response/checksum manifest được lưu lại.
- Compile source + parse `.vscode/tasks.json` và notebook JSON: passed.
- Unit tests: **31/31 passed**, gồm test rolling feature chỉ dùng trận hiện tại/quá khứ.
- Streamlit được chạy trong browser thật ở desktop viewport; đã kiểm tra đủ 6 mode, gồm bảng và hai biểu đồ Matplotlib của Recent form, cùng trạng thái prediction không fixture. Không có JavaScript error; phiên Recent form sạch không có console warning. Server log sạch sau khi tắt telemetry và thay API width đã deprecated.
- Visual QA: mở kiểm tra trực tiếp các nhóm heatmap, scatter, box/violin, stacked, rolling form, bubble, dumbbell và matchup.

## 7. Giới hạn còn lại và cách xử lý đúng

1. Gol.gg có thể thay cấu trúc HTML: chạy test/parser + quality-check sau mỗi refresh lớn; raw archive cho phép parse lại mà không crawl lại.
2. Leaguepedia refresh mới nhất không trả fixture tương lai; tiếp tục chạy `update-schedule` hằng ngày. Không tự đoán ngày/đối thủ.
3. Unittest có `PendingDeprecationWarning` từ nội bộ Seaborn; đây không phải runtime failure. Cảnh báo Vega ở Recent form đã được loại bỏ bằng renderer Matplotlib có kiểu dữ liệu và trục rõ ràng.
4. Dự báo là mô hình giáo dục và chưa calibration theo production; luôn trình bày cutoff, sample, Brier/log loss và uncertainty.
5. Project chưa có deployment/CI cloud vì không nằm trong phạm vi bài tập lớn Python đã chốt.

## 8. Lệnh nghiệm thu nhanh trên VS Code

```powershell
.\scripts\demo_offline.ps1 -TeamAId 2809 -TeamBId 2805
```

Lệnh này không crawl mạng; nó chạy test, quality, Pandas EDA, statistics, visualization, backtest và final report từ SQLite hiện có. Muốn cập nhật dữ liệu trước demo, chạy riêng `scripts/daily_update.ps1` khi có mạng.
