# Phase 7 — Statistical Evidence

- Thời điểm chạy: `2026-09-07T17:04:44.265664+00:00`
- Phạm vi: các trận chính thức S16 của 10 đội LCK primary; có thể gồm giải quốc tế.
- Wilson CI biểu diễn độ bất định của tỷ lệ thắng quan sát.
- Trạng thái suy luận: `ok`.

## 1. Tỷ lệ thắng và Wilson 95% CI

| Team | Wins | Games | Rate | 95% CI | Warning |
|---|---:|---:|---:|---|---|
| BNK FearX | 60 | 129 | 46.5% | 38.1%–55.1% |  |
| DN SOOPers | 47 | 120 | 39.2% | 30.9%–48.1% |  |
| Dplus KIA | 81 | 149 | 54.4% | 46.4%–62.2% |  |
| Gen.G | 89 | 128 | 69.5% | 61.1%–76.8% |  |
| HANJIN BRION | 43 | 108 | 39.8% | 31.1%–49.2% |  |
| Hanwha Life Esports | 87 | 139 | 62.6% | 54.3%–70.2% |  |
| KT Rolster | 48 | 106 | 45.3% | 36.1%–54.8% |  |
| Kiwoom DRX | 45 | 112 | 40.2% | 31.6%–49.4% |  |
| Nongshim RedForce | 43 | 105 | 41.0% | 32.0%–50.5% |  |
| T1 | 96 | 152 | 63.2% | 55.3%–70.4% |  |

## 2. Kiểm định thăm dò

- Chi-square side × outcome: `assumption_warning`; p-value = `3.5123942134008174e-06`.
  - Không dùng p-value này làm kết luận xác nhận: blue/red là hai quan sát ghép cặp của cùng game.
- Chưa chọn cặp đội; dùng `--team-a-id` và `--team-b-id` để chạy so sánh.

## 3. Giới hạn bắt buộc khi diễn giải

- Các kiểm định mang tính quan sát/thăm dò, không chứng minh quan hệ nhân quả.
- P-value không phải xác suất thắng và không thay thế mô hình dự đoán/backtest.
- So sánh thô chưa kiểm soát đầy đủ sức mạnh đối thủ, lịch thi đấu chồng lặp, thời gian và meta/patch.
- Bảng side × outcome chứa hai phía ghép cặp của cùng game, nên không thỏa hoàn toàn giả định quan sát độc lập của chi-square.

## 4. Cách đọc đúng

CI rộng nghĩa là ước lượng còn bất định. P-value < 0.05 chỉ là bằng chứng chống lại giả thuyết H0 trong mẫu và theo giả định của kiểm định. Muốn dự đoán trận kế tiếp phải dùng đặc trưng trước trận, temporal cutoff và backtest ở mô-đun modeling.
