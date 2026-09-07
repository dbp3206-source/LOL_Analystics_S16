# 01 — Tổng quan đồ án LoL Pro Analytics S16

## 1. Đồ án giải quyết bài toán gì?

Đồ án xây dựng một ứng dụng Python phục vụ phân tích các đội tuyển LCK cấp một và năm tuyển thủ chính của mỗi đội trong Season 16. Người dùng có thể xem một đối tượng riêng lẻ hoặc đối chiếu hai đối tượng:

- một đội tuyển;
- hai đội tuyển;
- một tuyển thủ;
- hai tuyển thủ cùng hoặc khác đội.

Hệ thống trả lời các câu hỏi như: đội nào đang có phong độ tốt hơn, đội nào kiểm soát mục tiêu sớm tốt hơn, tuyển thủ cùng vị trí khác nhau ở KDA/DPM/CSM ra sao, champion pool có rộng không, và một cặp đấu sắp tới có những kịch bản nào.

Đây là đồ án DA/DS bằng Python, không phải hệ thống cá cược. Dự đoán chỉ là một baseline giáo dục có giải thích, uncertainty và kiểm tra theo thứ tự thời gian.

## 2. Phạm vi dữ liệu

| Thành phần | Quy tắc |
|---|---|
| Mùa giải | Chỉ S16, từ `2026-01-01` |
| Đội chính | 10 đội LCK cấp một được cấu hình |
| Tuyển thủ | Starting five gần nhất; không lập hồ sơ chính cho dự bị |
| Giải đấu | LCK và giải quốc tế S16 mà các đội LCK tham dự |
| Thống kê chính | Gol.gg |
| Lịch tương lai | Leaguepedia hoặc LoL Esports, chỉ để bổ sung fixture |
| Academy/Challengers | Bị loại khỏi tập phân tích chính |

Đối thủ ngoài LCK có thể được lưu như dimension phụ nếu họ gặp đội LCK ở giải quốc tế. Họ không tự động trở thành đối tượng phân tích chính.

## 3. Luồng xử lý từ input đến output

```text
Yêu cầu người dùng
    ↓
Xác định mode và đối tượng cần phân tích
    ↓
Kiểm tra độ mới dữ liệu / lấy fixture phù hợp
    ↓
Scrape Gol.gg có cache, retry, rate limit và raw archive
    ↓
Parse HTML thành game, team, player, draft, timeline
    ↓
Upsert vào SQLite, không chèn trùng source ID
    ↓
Cleaning + 12 data-quality gates
    ↓
EDA và feature engineering bằng Python/Pandas/NumPy
    ↓
Thống kê mô tả + visualization theo câu hỏi nghiệp vụ
    ↓
So sánh / prediction baseline / kịch bản
    ↓
CLI, Streamlit, CSV, hình và report có data cutoff
```

Mỗi bước tạo một đầu ra có thể kiểm tra. Vì vậy nếu kết quả cuối sai, ta có thể quay lại xác định lỗi nằm ở HTML gốc, parser, database, cleaning hay analysis.

## 4. Kiến trúc thư mục

| Thư mục/file | Vai trò | Đầu vào | Đầu ra |
|---|---|---|---|
| `configs/project.json` | Khóa phạm vi S16, nguồn, đội và freshness | Quy tắc project | Cấu hình đã validate |
| `src/collection/` | Tải trang và parse dữ liệu | URL/HTML | Python dataclass/dictionary |
| `data/raw/` | Lưu bằng chứng nguồn theo ngày | HTML tải về | Raw archive + manifest |
| `src/storage/` | Schema và upsert SQLite | Parsed objects | `data/lol_analytics.db` |
| `src/quality/` | Chuẩn hóa và quality gates | SQLite chưa kiểm định | Dataset đạt/không đạt gate |
| `src/analysis/` | Metrics, EDA, statistics, figures | SQLite sạch | CSV, JSON, Markdown, hình |
| `src/modeling/` | Prediction và walk-forward backtest | Feature trước cutoff | Probability + evaluation |
| `app/streamlit_app.py` | Giao diện demo bằng Python | SQLite/reports | Dashboard tương tác |
| `tests/` | Fixture HTML và regression tests | Code + dữ liệu giả lập | Bằng chứng pass/fail |
| `reports/` | Kết quả có thể nộp/đối chiếu | Các phase đã chạy | Báo cáo và figure manifest |

## 5. Nghiệp vụ Data Analyst được thể hiện

### 5.1 Xác định câu hỏi trước khi vẽ

Biểu đồ không được chọn chỉ vì đẹp. Ví dụ:

- Muốn so sánh quy mô giữa nhiều đội → bar/lollipop chart.
- Muốn xem phong độ thay đổi theo thời gian → line chart/rolling window.
- Muốn xem phân phối DPM giữa hai tuyển thủ → box/violin plot.
- Muốn xem mối quan hệ GPM và win rate → scatter plot với annotation.
- Muốn xem nhiều metric của đúng hai đối tượng → heatmap hoặc dumbbell chart.
- Muốn xem tương quan giữa các feature → correlation heatmap, kèm cảnh báo “correlation không đồng nghĩa causation”.

### 5.2 Kiểm tra dữ liệu trước phân tích

Workflow Pandas tại `src/analysis/pandas_eda.py` thực hiện:

1. đọc các bảng từ SQLite bằng `pandas.read_sql_query`;
2. xem `shape`, kiểu dữ liệu và khoảng thời gian;
3. đổi cột thời gian về `datetime`;
4. đếm missing và duplicate;
5. thống kê count/mean/std/min/quartile/max;
6. xem skewness và kurtosis;
7. dùng IQR để gắn cờ điểm cần xem xét, không tự động xóa;
8. dùng `groupby`, `crosstab` và correlation để tìm pattern.

Outlier trong esports có thể là một trận thật sự đặc biệt. Vì vậy project không xóa outlier chỉ vì nó nằm ngoài công thức IQR.

### 5.3 So sánh đúng ngữ cảnh

- Tỷ lệ thắng phải đi cùng số trận và khoảng tin cậy.
- Player comparison ưu tiên cùng role; nếu khác role phải cảnh báo.
- Chỉ số raw CSM/DPM giữa Support và Bot không thể kết luận trực tiếp ai “giỏi hơn”.
- Champion có 100% win rate sau một game không được xem là pick đáng tin cậy.
- H2H là bằng chứng bổ sung, không thay thế phong độ hiện tại và sample size.

## 6. Nghiệp vụ Data Scientist được thể hiện

Project dùng phần DS vừa sức sinh viên năm 3:

- feature engineering từ recent form, economy, combat và H2H;
- Bayesian/Laplace smoothing để giảm cực đoan khi sample nhỏ;
- Logistic Regression giáo dục, có regularization cơ bản;
- walk-forward backtest theo thời gian;
- accuracy, Brier score và log loss;
- cutoff để không dùng dữ liệu tương lai;
- uncertainty và trạng thái `insufficient_data`.

Không đưa deep learning, ensemble phức tạp hay tuning quy mô lớn vào phần bắt buộc. Những kỹ thuật đó làm tăng độ khó nhưng không tự động tăng chất lượng nghiệp vụ.

## 7. Các sản phẩm đầu ra

1. Source code Python có module rõ trách nhiệm.
2. SQLite database cho dữ liệu có cấu trúc.
3. Raw archive để tái kiểm tra nguồn.
4. CSV trung gian và bảng EDA bằng Pandas/NumPy.
5. Báo cáo quality, EDA, statistics, prediction và backtest.
6. Bộ visualization theo câu hỏi nghiệp vụ.
7. Dashboard Streamlit để demo nhiều mode.
8. Notebook/VS Code cell flow để học và trình bày.
9. Ba tài liệu học tập: tổng quan, hướng dẫn chạy, playbook kiến thức.
10. Unit tests để chứng minh parser, database, analysis và predictor không hồi quy.

## 8. Tiêu chí hoàn thành học thuật

Đồ án chỉ được xem là hoàn thiện khi:

- dữ liệu S16 qua toàn bộ quality gates;
- test chạy pass trong môi trường VS Code chuẩn;
- các notebook chạy từ đầu đến cuối;
- Matplotlib/Seaborn/Statsmodels được sử dụng thật, không chỉ ghi trong requirements;
- visualization có nhiều dạng phù hợp từng câu hỏi;
- prediction có fixture/cutoff/freshness rõ ràng;
- báo cáo chỉ dùng số liệu có thể truy ngược về dữ liệu;
- người mới có thể làm theo `02_VSCODE_HANDS_ON_GUIDE.md` mà không phải đoán lệnh.
