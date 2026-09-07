# Quality Gate — Target 95/100

Đây là tiêu chuẩn nghiệm thu nội bộ, không phải bảo đảm điểm số từ giảng viên.

| Hạng mục | Điểm |
|---|---:|
| Đúng phạm vi S16, đội chính và starting five | 10 |
| Scraper ổn định, incremental, cache và log | 10 |
| Database/schema, idempotency và data provenance | 10 |
| Cleaning, validation và data-quality evidence | 15 |
| DA workflow và insight nghiệp vụ | 15 |
| Statistical validity | 10 |
| Visualization rõ ràng và đúng ngữ cảnh | 10 |
| Prediction, chống leakage và backtest | 15 |
| Demo, report, code comment, test và reproducibility | 5 |
| **Tổng** | **100** |

## Automatic rejection conditions

- Có dữ liệu S15 trở về trước trong feature chính.
- Nhầm đội primary với Challengers/Academy.
- So sánh substitute như starting five mà không cảnh báo.
- Prediction feature chứa dữ liệu từ target hoặc tương lai.
- Win rate champion không có số game.
- Gọi trận đã kết thúc là trận tiếp theo.
- Scraper chạy lại tạo duplicate.
- Báo cáo không ghi data cutoff/source.
- Model không được so sánh với baseline.
- Có biểu đồ nhưng không có câu hỏi hoặc diễn giải.
- So sánh trực tiếp raw metrics của hai role khác nhau mà không chuẩn hóa theo role.
- Ép single-team/single-player query phải có Entity B.
- Draft có action trùng hoặc không đủ đúng 10 picks và 10 bans cho game đã parse.
- Gọi kết quả hypothetical là “trận tiếp theo”, hoặc dự đoán official fixture khi dữ liệu đã stale.

## Required evidence

- Unit test parser/cleaner.
- Data-quality report.
- Crawl/update manifest.
- Notebook hoặc script report chạy lại được từ SQLite/CSV.
- Model evaluation và temporal split evidence.
- Walk-forward baseline report (`reports/backtest-phase-9.*`) và cảnh báo sample nhỏ.
- Full-stats parser fixture và schedule JSON-LD parser fixture.
- Screenshot/demo query T1–HLE.
- README hướng dẫn từ môi trường sạch.
