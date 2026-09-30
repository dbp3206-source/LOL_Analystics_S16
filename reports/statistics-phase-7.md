# Phase 7 — Statistical Evidence

- Thời điểm chạy: `2026-09-29T15:47:27.030011+00:00`
- Phạm vi: các trận chính thức S16 của 10 đội LCK primary; có thể gồm giải quốc tế.
- Wilson CI biểu diễn độ bất định của tỷ lệ thắng quan sát.
- Trạng thái suy luận: `partial`.

## 1. Tỷ lệ thắng và Wilson 95% CI

| Team | Wins | Games | Rate | 95% CI | Warning |
|---|---:|---:|---:|---|---|
| Hanwha Life Esports | 1 | 1 | 100.0% | 20.7%–100.0% | n < 30 |
| T1 | 0 | 1 | 0.0% | 0.0%–79.3% | n < 30 |

## 2. Kiểm định thăm dò

- Chi-square side × outcome: `assumption_warning`; p-value = `1.0`.
  - Không dùng p-value này làm kết luận xác nhận: blue/red là hai quan sát ghép cặp của cùng game.
- Cặp chọn: **T1** và **Hanwha Life Esports**.
- Two-proportion z-test: `skipped`; p-value = `N/A`.
- Welch t-test GDM + Cohen's d: `skipped`; p-value = `N/A`; d = `None`.

## 3. Giới hạn bắt buộc khi diễn giải

- Các kiểm định mang tính quan sát/thăm dò, không chứng minh quan hệ nhân quả.
- P-value không phải xác suất thắng và không thay thế mô hình dự đoán/backtest.
- So sánh thô chưa kiểm soát đầy đủ sức mạnh đối thủ, lịch thi đấu chồng lặp, thời gian và meta/patch.
- Bảng side × outcome chứa hai phía ghép cặp của cùng game, nên không thỏa hoàn toàn giả định quan sát độc lập của chi-square.

## 4. Cách đọc đúng

CI rộng nghĩa là ước lượng còn bất định. P-value < 0.05 chỉ là bằng chứng chống lại giả thuyết H0 trong mẫu và theo giả định của kiểm định. Muốn dự đoán trận kế tiếp phải dùng đặc trưng trước trận, temporal cutoff và backtest ở mô-đun modeling.
