# LoL Pro Analytics S16 — A-to-Z Handbook

> Giáo trình tự học + source-code handbook + runtime guide + testing/debugging/presentation handbook cho chính repository này.

## 🧭 Bạn đang đọc gì?

Handbook này được viết cho người biết Python cơ bản nhưng chưa chắc về DA, DS, SQL, web scraping, statistics hoặc ML. Nó có hai chế độ song song:

- **📱 Phone / read-only mode:** đọc mental model, toy data, execution trace, output mẫu và câu hỏi defense ngay trên GitHub mobile.
- **💻 Hands-on mode:** chạy lệnh trong VS Code khi có laptop để kiểm chứng, sửa parameter, tạo lỗi an toàn và chạy test.

Laptop là lớp xác minh, không phải điều kiện để hiểu chapter.

## 🚀 Chọn route học nhanh trên điện thoại

```text
START HERE
├─ Muốn hiểu project nhanh      → 01 → 04 → 22 → 30
├─ Muốn học Python project      → 02 → 04 → 05 → 20
├─ Muốn học Data Analyst        → 03 → 08 → 09 → 10 → 11 → 13
├─ Muốn học Statistics          → 12 → 13 → 14
├─ Muốn học Data Science        → 14 → 15 → 16
├─ Muốn hiểu Testing/Debug      → 18 → 23 → 24
└─ Sắp thuyết trình             → 25 → 26 → 30
```

## ⏱ Quick study routes

### 📱 15 phút

Đọc [01 mental model](01_PROJECT_MENTAL_MODEL.md), xem lineage một game ở [22 data lineage](22_DATA_LINEAGE_AND_TRACEABILITY.md), rồi trả lời ba câu: grain của `team_game_stats` là gì, vì sao chỉ S16, và prediction khi không có fixture tương lai được gọi là gì.

### 📱 30 phút

Đọc [04 kiến trúc](04_REPOSITORY_ARCHITECTURE.md), làm simulated lab `normalize_role`, `groupby` và Laplace smoothing trong các chapter 07/10/14.

### 📱 60 phút

Đọc trọn một chapter kỹ thuật theo block: Mental Model → Phone Mode → Input → Execution → Output → What If → Try It Yourself → Test → Checkpoint.

### 💻 Laptop session

Đọc chapter trước, chạy command tương ứng sau. Bắt đầu bằng `scripts/demo_offline.ps1` trước khi crawl web.

## 📚 Learning order đầy đủ

1. [01 — Project mental model](01_PROJECT_MENTAL_MODEL.md)
2. [02 — Python project foundations](02_PYTHON_PROJECT_FOUNDATIONS.md)
3. [03 — DA/DS foundations](03_DA_DS_FOUNDATIONS.md)
4. [04 — Repository architecture](04_REPOSITORY_ARCHITECTURE.md)
5. [05 — Config and CLI](05_CONFIG_AND_CLI.md)
6. [06 — Scraping and parsing](06_SCRAPING_AND_PARSING.md)
7. [07 — Database and schema](07_DATABASE_AND_SCHEMA.md)
8. [08 — Cleaning and quality](08_CLEANING_AND_QUALITY.md)
9. [09 — NumPy and Pandas](09_NUMPY_PANDAS_CORE.md)
10. [10 — EDA and metrics](10_EDA_AND_METRICS.md)
11. [11 — Statistics and uncertainty](11_STATISTICS_AND_UNCERTAINTY.md)
12. [12 — Visualization system](12_VISUALIZATION_SYSTEM.md)
13. [13 — Prediction and features](13_PREDICTION_AND_FEATURES.md)
14. [14 — Logistic Regression](14_LOGISTIC_REGRESSION.md)
15. [15 — Walk-forward backtest](15_WALK_FORWARD_BACKTEST.md)
16. [16 — Streamlit dashboard](16_STREAMLIT_DASHBOARD.md)
17. [17 — Testing and reproducibility](17_TESTING_AND_REPRODUCIBILITY.md)
18. [18 — Operations and freshness](18_OPERATIONS_AND_FRESHNESS.md)
19. [19 — Reporting and research story](19_REPORTING_AND_RESEARCH_STORY.md)
20. [20 — File-by-file reference](20_FILE_BY_FILE_REFERENCE.md)
21. [21 — Function-by-function reference](21_FUNCTION_BY_FUNCTION_REFERENCE.md)
22. [22 — Data lineage](22_DATA_LINEAGE_AND_TRACEABILITY.md)
23. [23 — Full capability test guide](23_FULL_CAPABILITY_TEST_GUIDE.md)
24. [24 — Debugging playbook](24_DEBUGGING_PLAYBOOK.md)
25. [25 — Demo and presentation](25_DEMO_AND_PRESENTATION_GUIDE.md)
26. [26 — Oral defense Q&A](26_ORAL_DEFENSE_QA.md)
27. [27 — Beginner exercises](27_BEGINNER_EXERCISES.md)
28. [28 — Glossary](28_GLOSSARY.md)
29. [29 — Limitations and tradeoffs](29_LIMITATIONS_AND_DESIGN_TRADEOFFS.md)
30. [30 — Master cheatsheet](30_MASTER_CHEATSHEET.md)

## 🏷 Evidence labels

| Label | Ý nghĩa |
|---|---|
| `SOURCE-BACKED` | Suy ra trực tiếp từ source/config/schema |
| `RUNTIME-VERIFIED` | Đã chạy trong workspace và có output thực |
| `TEST-VERIFIED` | Được bảo vệ bởi automated test |
| `SOURCE-DERIVED SIMULATION` | Toy example suy ra từ control flow, không giả mạo runtime |
| `LIMITATION` | Giới hạn đã biết, không được che giấu |
| `OPTIONAL EXTENSION` | Ý tưởng mở rộng, không thuộc core deliverable |

Snapshot audit gần nhất: Python `3.12.14`, 31/31 tests pass, `health=ok`, freshness `fresh`, dữ liệu local 667 games. Counts có thể thay đổi sau daily update; khi vậy README/report mới nhất là source of truth của snapshot.

## ✅ Checkpoint trước khi đi tiếp

- [ ] Tôi biết handbook có phone mode và hands-on mode.
- [ ] Tôi biết code/runtime hiện tại là source of truth.
- [ ] Tôi biết không được gọi hypothetical matchup là official prediction.
- [ ] Tôi biết có thể đọc tiếp mà không cần chạy Python.

### 📍 Good stopping point

Đến đây bạn đã biết cách dùng handbook. Khi quay lại, bắt đầu từ **01 — Project mental model**.
