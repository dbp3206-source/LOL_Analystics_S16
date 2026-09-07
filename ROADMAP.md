# Final Implementation Roadmap

## Phase 1 — Project foundation

### Kiến thức dùng

- Python module, function, exception, typing, datetime và logging.
- Git cơ bản và môi trường ảo.

### Công việc

- Tạo cấu trúc `src`, `data`, `notebooks`, `app`, `tests`, `reports`.
- Tạo virtual environment và dependency manifest.
- Tạo file cấu hình season, timezone, rate limit và danh sách đội LCK.
- Thiết lập logging và đường dẫn độc lập với máy.

### Definition of done

- Chạy được `python -m src.cli --help`.
- Test smoke và import toàn project thành công.

## Phase 2 — Source audit và scraper prototype

**Trạng thái: hoàn thành prototype (2026-08-26).** Đã audit Gol.gg, crawl thử T1/HLE, lưu raw HTML có cache/manifest, lọc Kespa Cup 2025 và tạo báo cáo tại `reports/source-audit-phase-2.md`.

### Kiến thức dùng

- HTTP, HTML, status code, timeout, retry và DOM parsing.
- User requirement về web scraping; đây là phần bổ sung cần thiết ngoài các roadmap học.

### Công việc

- Kiểm tra robots.txt, điều khoản và cấu trúc URL Gol.gg.
- Cố định selector cho tournament, team, player, series và game.
- Lưu raw HTML kèm URL, collected_at, status và content hash.
- Rate limit, cache, retry có backoff và crawl manifest.
- Viết parser test bằng HTML fixture, không gọi web trong unit test.

### Definition of done

- Scrape thử T1 và HLE S16 thành công.
- Parser không nhầm HLE với HLE Challengers.
- Có log lỗi và không tải trùng trang chưa thay đổi.

## Phase 3 — Database và incremental update

**Trạng thái: hoàn thành full snapshot, incremental refresh gần nhất 2026-09-08.** SQLite schema version 1, lệnh `db-init`, parser game-level, `update-game --game-id ...`, `update-team --team-id ...` và `update-all` có dry-run/max-games đã hoàn thành. Snapshot hiện có 667 game pages và fullstats; external tournament opponents được giữ non-primary.

Phase 4 đã có `quality-check`: chuẩn hóa dimension text/role, đánh cờ Academy/Challengers và ghi quality report 12/12 vào `reports/data-quality-phase-4.*`; draft parser đã được sửa và toàn bộ 667 game có đúng 13.340 actions. GDM dùng đúng đơn vị gold differential per minute thay vì total final gold difference.

Phase 5 đã có metric layer dependency-light: team summary, player summary, rolling 5/10-game form và CSV/EDA report.

Phase 6 đã có `app/streamlit_app.py` với các chế độ team/player comparison và recent form; dashboard hiển thị sample size và cảnh báo dữ liệu null.

Phase 7 đã có baseline `predict-matchup`: posterior win rate, H2H blend, uncertainty và prediction log có model/feature version.

Phase 8 đã có full `update-all`, `final-report` và `docs/RUNBOOK.md`; current workspace có 667 game pages, 5.793 timeline milestones, 14 rich PNG cùng 8 SVG fallback figures.

### Kiến thức dùng

- Pandas đọc/ghi dữ liệu.
- SQL căn bản: table, key, join, filter, aggregation.

### Công việc

- Tạo SQLite schema và migration script bằng Python.
- Lưu dimension/fact tables theo `docs/DATA_SCHEMA.md`.
- Upsert idempotent theo source ID.
- Tạo lệnh `python -m src.cli update --season S16`.
- Nếu dữ liệu trong ngày đã đủ mới thì không crawl lại.
- Nguồn lịch phụ chỉ ghi vào bảng schedule.

### Definition of done

- Chạy update hai lần không tạo duplicate.
- Có data cutoff và trạng thái update theo từng nguồn.

## Phase 4 — Data quality và cleaning

**Trạng thái: hoàn thành (cập nhật 2026-09-08).** Có 12 quality checks, chuẩn hóa role/text, tách external opponents khỏi primary LCK, loại trừ Academy/Challengers khỏi dataset chính, kiểm tra starting five và current roster.

### Kiến thức dùng

- Pandas cleaning, missing values, dtype, outlier và feature engineering.
- Quy trình inspect/clean trong notebook Colab tham khảo.

### Công việc

- Chuẩn hóa team/player/champion aliases và role.
- Tách đội chính khỏi Academy/Challengers.
- Xác định starting five từ lineup chính thức gần nhất.
- Chuyển phần trăm, signed number, duration và date về dtype chuẩn.
- Kiểm tra missing, duplicate, cardinality, range và foreign key.
- Gắn domestic/international, tournament, split và patch.
- Xuất data-quality report trước/sau cleaning.

### Definition of done

- Dataset chính không có season ngoài S16.
- Game hoàn tất có đúng hai đội và một winner.
- Player comparison chỉ gồm starting five hiện tại.
- Mọi trường bị loại hoặc sửa đều có lý do trong cleaning log.

## Phase 5 — EDA và nghiệp vụ đội tuyển

**Trạng thái: hoàn thành và chạy lại trên snapshot 2026-09-08.** Có team/player summary, rolling form, champion pool, blue/red side, objective timing, Pandas/NumPy intermediate tables và CSV exports; rich plots/notebook visuals đã render.

### Kiến thức dùng

- NumPy/Pandas aggregation.
- Univariate, bivariate, multivariate analysis từ Colab.
- Matplotlib/Seaborn từ các roadmap.

### Công việc

- Tổng quan số giải, series, game, patch và độ phủ dữ liệu.
- Team profile: win rate, K:D, GPM/GDM, GD/CS/TD/DRA@15, DPM.
- Objective: dragon, Voidgrub, Herald, Nashor và tower.
- Vision và blue/red side.
- Rolling form 5/10 game và 3/5 series.
- Exponentially weighted form.
- Tách domestic-only, international-only và all-S16.
- Hiển thị cỡ mẫu cho mọi tỷ lệ.

### Definition of done

- Mỗi biểu đồ trả lời một câu hỏi nghiệp vụ.
- Có notebook EDA tái lập được từ SQLite/processed CSV.

## Phase 6 — Head-to-head và role matchup

**Trạng thái: bản truy vấn/report hoàn thành (2026-08-26).** Có single-team, H2H game detail, same-role lane matchup, champion pool và cảnh báo khác role/sample nhỏ; dữ liệu quốc tế sẽ tự xuất hiện khi Gol.gg crawl được tournament S16 tương ứng.

### Kiến thức dùng

- GroupBy, pivot, merge, crosstab và comparison visualization.

### Công việc

- Series record, game record, score, side, patch và tournament.
- Giữ các đối đầu quốc tế S16 giữa hai đội LCK.
- Cảnh báo roster mismatch và sample size nhỏ.
- Xây single-team profile và single-player profile.
- Xây player-vs-player comparison cho tuyển thủ cùng hoặc khác đội.
- So sánh TOP, JUNGLE, MID, BOT, SUPPORT theo nhóm metric phù hợp.
- Nếu hai tuyển thủ khác role, so sánh role-adjusted percentile; không kết luận từ raw KDA/DPM khác ngữ cảnh.
- Champion pool: số game, win rate, KDA, recent usage và breadth.
- Không xếp hạng champion bằng win rate đơn lẻ khi cỡ mẫu nhỏ.

### Definition of done

- Truy vấn T1–HLE tạo được đủ năm lane comparisons.
- Truy vấn một đội, một tuyển thủ và hai tuyển thủ tạo được báo cáo độc lập.
- Không trộn substitute vào profile đội hình chính.

## Phase 7 — Thống kê suy luận

**Trạng thái: hoàn thành ở mức nhập môn, scientific runtime đã verified (2026-09-08).** Wilson interval chạy bằng standard library. SciPy/Statsmodels đã chạy chi-square side × outcome, two-proportion z-test, Welch t-test GDM và Cohen's d cho T1–HLE. Chi-square được đánh dấu `assumption_warning` vì blue/red là cặp phụ thuộc của cùng game; report không dùng p-value đó làm kết luận xác nhận.

### Kiến thức dùng

- Standard library + Statsmodels/SciPy: confidence interval, chi-square, z-test hai tỷ lệ, Welch t-test và effect size.

### Công việc

- Confidence interval cho win rate.
- So sánh phân phối metric giữa hai đội.
- Kiểm tra giả định trước phép kiểm định.
- Báo p-value cùng effect size và ý nghĩa nghiệp vụ.
- Không kết luận mạnh từ head-to-head ít trận.

### Definition of done

- Mỗi kết luận thống kê có giả thuyết, phép kiểm định, cỡ mẫu và diễn giải.

## Phase 8 — Visualization package

**Trạng thái: rich renderer đã render lại (2026-09-08).** Có 12 global chart và 2 matchup chart bằng Matplotlib/Seaborn, bám luồng univariate–bivariate–multivariate của Colab. Fallback 8 SVG vẫn giữ cho môi trường tối giản; notebook còn sinh 6 hình học theo cell. QA trước đó đã sửa rolling form sang trục thứ tự game để không nối giả xu hướng qua khoảng thời gian không thi đấu.

### Kiến thức dùng

- Matplotlib, Seaborn, subplot và annotation.

### Công việc

- KPI comparison table.
- Dumbbell chart.
- Rolling form chart.
- Head-to-head/objective timeline (facts đã lưu; chart timeline phong phú hơn để mở rộng).
- Side-performance chart.
- Objective heatmap.
- Early-game comparison.
- Năm role matchup panels.
- Champion-pool heatmap.
- Pick/ban chart nếu parser đủ ổn định.
- Confusion matrix và prediction probability.

### Definition of done

- 10–12 visualizations có title, subtitle, unit, sample size, source và data cutoff.
- Không dùng 3D hoặc radar với dữ liệu thô khác đơn vị.

## Phase 9 — Prediction

**Trạng thái: baseline + walk-forward model comparison chạy lại 2026-09-08.** `predict-matchup` dùng economy/combat/H2H baseline; `backtest` so sánh baseline trên 581 game và Logistic Regression trên 577 game bằng accuracy/Brier/log loss theo thời gian không leakage. Đây là mức modeling chính được chốt cho sinh viên năm 3; Random Forest/GridSearch không phải deliverable bắt buộc.

### Kiến thức dùng

- Logistic Regression, temporal split/walk-forward và model metrics từ các roadmap; implementation hiện tại dependency-light để dễ đọc cú pháp.
- Log Loss/Brier Score là bổ sung nhỏ để đánh giá xác suất.

### Công việc

- Target chính: game winner; series probability được suy ra cho BO3/BO5.
- Baseline bằng rolling win rate hoặc rating đơn giản.
- 12–18 prematch differential features.
- Time-based split và walk-forward evaluation đơn giản.
- So sánh baseline và Logistic Regression.
- Accuracy, Log Loss và Brier Score; confusion matrix/precision/recall chỉ bổ sung nếu thật sự giúp câu hỏi phân loại.
- Lưu model, feature list, training cutoff và metrics.

### Data policy

- Training chính dùng các trận S16 có hai phía đủ feature, ưu tiên LCK-vs-LCK.
- Trận quốc tế được dùng cho form/head-to-head; chỉ vào training khi cả hai phía có feature đầy đủ.
- Tuyệt đối không dùng dữ liệu xảy ra sau prediction timestamp.
- Draft tương lai không phải model input; chỉ dùng làm scenario có điều kiện.

### Definition of done

- Model thắng baseline trên ít nhất một probability metric mà không giảm mạnh độ ổn định.
- Nếu không thắng baseline, sản phẩm dùng baseline và báo trung thực.

## Phase 10 — Python application và report

**Trạng thái: deliverable học thuật hoàn thành và tái kiểm duyệt (2026-09-08).** Có 6 mode, gồm Recent form độc lập; freshness, manual supplemental schedule refresh, team/player/H2H/champion sections, standalone CLI entity reports và final handoff report. Leaguepedia MediaWiki API là schedule supplement hoạt động; LoL Esports shell/403 chỉ còn là fallback.

### Kiến thức dùng

- Streamlit là một extension Python nhỏ, thay cho Dash/Flask được nhắc trong roadmap nâng cao.
- Jupyter report và documentation từ các roadmap.

### Công việc

- Form chọn analysis mode: one team, two teams, one player hoặc two players.
- Entity selectors thay đổi theo analysis mode; scope, recent-N và BO format chỉ hiện khi phù hợp.
- Freshness check và nút cập nhật dữ liệu.
- Team/player overview, recent form, H2H, lane/peer matchups, champion pool và prediction khi đủ điều kiện.
- Lịch trận tiếp theo từ nguồn phụ, chuẩn hóa theo Asia/Bangkok.
- Hiển thị source, collected_at, data cutoff, model version và limitations.
- Hoàn thiện notebooks, report, slide, README, tests và demo script.

### Definition of done

- Query chuẩn T1–HLE chạy end-to-end.
- Bốn analysis modes đều chạy end-to-end trên ít nhất một fixture kiểm thử.
- Ứng dụng vẫn phân tích được khi không có trận tương lai; chỉ bỏ phần next-fixture prediction.
- Chạy được trên VS Code bằng các lệnh được ghi trong README.

## Lịch 9 tuần đề xuất

| Tuần | Trọng tâm | Đầu ra |
|---|---|---|
| 1 | Python project, source audit | Skeleton, source notes |
| 2 | Scraper prototype | Raw T1/HLE data |
| 3 | SQLite, incremental update | Database S16 |
| 4 | Cleaning, data quality | Processed tables, QA report |
| 5 | Team EDA, form, H2H | EDA notebook |
| 6 | Player/role/champion analysis | Matchup notebook |
| 7 | Statistics, visualization | Analysis figures |
| 8 | Prediction và backtest | Model report |
| 9 | Streamlit, report, tests, rehearsal | Final submission |

## Out of scope

- LCK Challengers/Academy.
- Substitute profile comparison.
- Dữ liệu S15 trở về trước.
- Theo dõi toàn bộ đội chuyên nghiệp toàn cầu.
- NLP chatbot tổng quát.
- Deep learning, XGBoost, SHAP, PCA/DBSCAN.
- DVC, Docker, Airflow/Prefect và Flask API riêng.
- Cá cược hoặc cam kết kết quả chắc chắn.
