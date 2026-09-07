# 05 — Bản đồ source code: đọc file nào, logic gì, input/output ra sao

Tài liệu này là “mục lục có giải thích” cho toàn bộ code thực thi của project. Mục tiêu không phải học thuộc từng dòng, mà hiểu hợp đồng của từng file: dữ liệu đi vào từ đâu, được biến đổi vì sao, và đầu ra được kiểm chứng ở đâu.

## 1. Cách đọc code mà không bị ngợp

Với mỗi file, đọc theo bốn câu hỏi:

1. **Input là gì?** URL, HTML, JSON cấu hình, SQLite hay DataFrame?
2. **Invariant là gì?** Điều kiện nào luôn phải đúng, ví dụ `season = S16` hoặc một game chỉ có hai team rows?
3. **Transform là gì?** Parse, normalize, aggregate, feature engineering hay inference?
4. **Output là gì?** Object Python, row SQLite, CSV, figure, JSON report hay giao diện?

Trong source code, docstring giải thích hợp đồng của hàm/lớp; inline comment được dùng ở các đoạn nghiệp vụ dễ hiểu sai. Không comment lại các phép gán hiển nhiên vì điều đó làm code dài mà không giúp hiểu bản chất.

## 2. Điểm vào và cấu hình

| File | Trách nhiệm | Input → Output | Điểm nên đọc |
|---|---|---|---|
| `configs/project.json` | Khóa season, mốc ngày, 10 đội LCK, nguồn, cache và đường dẫn | JSON → `ProjectConfig` | Vì sao scope không trôi sang S15/Academy |
| `src/config.py` | Load JSON, resolve path và validate cấu hình | Path → dataclass cấu hình | `load_config`, validation team/source |
| `src/cli.py` | Khai báo lệnh và điều phối module | CLI args → JSON terminal/file artifact | `build_parser`, `main`; CLI không chứa nghiệp vụ phân tích |
| `src/logging_config.py` | Cấu hình log thống nhất | Tên logger → console/file log | Phân biệt log vận hành với kết quả phân tích |
| `src/__init__.py` và các `*/__init__.py` | Đánh dấu Python package | Import path → package | Các file này cố ý rất ngắn |

## 3. Thu thập dữ liệu web

| File | Trách nhiệm | Input → Output | Logic cốt lõi |
|---|---|---|---|
| `src/collection/http_client.py` | HTTP có timeout, retry, rate limit, cache và raw archive | URL → HTML/JSON bytes + manifest | Không scrape dồn dập; giữ bằng chứng nguồn để audit parser |
| `src/collection/parsers.py` | Parse directory, team summary và match list | HTML → team/game candidate objects | Chuẩn hóa text, lọc ngày từ 2026, quarantine năm không rõ |
| `src/collection/game_parsers.py` | Parse một game và trang fullstats | HTML → game/team/player/draft/timeline records | Mapping đúng blue/red, winner, role, 10 pick/10 ban và chỉ số advanced |
| `src/collection/updater.py` | Điều phối incremental update theo game/team/toàn bộ LCK | Candidate URL → upsert result + update manifest | Deduplicate source ID, cache hit và lỗi từng trang không làm mất trace |
| `src/collection/schedule.py` | Lấy lịch bổ sung và chuẩn hóa UTC | Leaguepedia/LoL Esports payload → fixture rows | Nguồn lịch không được thay thế Gol.gg cho thống kê |
| `src/collection/source_audit.py` | Kiểm tra cấu trúc nguồn trước khi tin parser | Trang mẫu → audit Markdown/JSON | Chứng minh selector/field tồn tại thay vì đoán schema web |

Luồng gọi chính: `src.cli` → `updater` → `http_client` → `parsers/game_parsers` → `storage.database`.

## 4. Lưu trữ và chất lượng

| File | Trách nhiệm | Input → Output | Logic cốt lõi |
|---|---|---|---|
| `src/storage/schema.sql` | Định nghĩa 19 bảng dimension/fact/operational/derived | SQL → SQLite schema version 1 | Primary/foreign key, season check, grain của từng bảng |
| `src/storage/database.py` | Mở DB, migrate idempotent, upsert records và query helper | Parsed objects → normalized rows | `ON CONFLICT` chống trùng; refresh roster period không xóa lịch sử |
| `src/quality/cleaning.py` | Chuẩn hóa whitespace, tên và role | Dirty dimension values → canonical values | Missing giữ là `NULL`; không biến thiếu dữ liệu thành 0 |
| `src/quality/checks.py` | Chạy 12 SQL quality gates | SQLite → pass/fail + affected rows | Dừng analysis khi season, winner, lineup, range, draft hoặc scope sai |

`schema.sql` trả lời “dữ liệu được tổ chức thế nào”; `database.py` trả lời “code ghi/đọc thế nào”; `checks.py` trả lời “khi nào dữ liệu đủ tin cậy để phân tích”.

## 5. Data Analysis

| File | Trách nhiệm | Input → Output | Logic cốt lõi |
|---|---|---|---|
| `src/analysis/metrics.py` | Tạo team/player summary, rolling form, side, champion pool, H2H và role matchup | SQLite rows → dictionaries/tables | Luôn giữ sample size; so sánh player theo role; rolling chỉ nhìn quá khứ |
| `src/analysis/reports.py` | EDA nền không phụ thuộc scientific stack | SQLite → CSV + Markdown/JSON | Tạo artifact kiểm tra được trước khi vẽ |
| `src/analysis/pandas_eda.py` | Luồng EDA kiểu Colab bằng Pandas/NumPy | SQLite → 8 CSV + report | Shape/dtype, missing, duplicate, describe, IQR, groupby, crosstab, correlation |
| `src/analysis/statistics.py` | Thống kê mô tả và suy luận nhập môn | Clean samples → CI/test/effect size | Wilson CI, z-test, Welch t-test, Cohen's d; assumptions ghi cùng kết quả |
| `src/analysis/scientific_visualizations.py` | Chuẩn bị bảng và render 12–14 rich figures | DataFrames → PNG + manifest | Mỗi chart gắn với một câu hỏi; clipping chỉ để hiển thị |
| `src/analysis/visualizations.py` | SVG fallback khi thiếu Matplotlib/Seaborn | Summary rows → 8 SVG | Giữ demo khả dụng trên môi trường tối giản, không giả vờ là rich renderer |

## 6. Data Science và dự đoán

| File | Trách nhiệm | Input → Output | Logic cốt lõi |
|---|---|---|---|
| `src/modeling/predictor.py` | Baseline có giải thích cho một matchup | Team history trước cutoff + optional fixture → probability/evidence | Bayesian smoothing, recent/economy/combat/H2H; sample nhỏ và hypothetical được gắn nhãn |
| `src/modeling/backtest.py` | Đánh giá baseline và Logistic Regression theo thời gian | Chronological games → accuracy/Brier/log loss | Walk-forward: mỗi game chỉ dùng thông tin đã tồn tại trước game đó |

Không đọc `predictor.py` trước `metrics.py`: model chỉ có ý nghĩa khi hiểu feature và grain đã tạo ra nó.

## 7. Sản phẩm trình bày và báo cáo

| File | Trách nhiệm | Input → Output | Logic cốt lõi |
|---|---|---|---|
| `app/streamlit_app.py` | Dashboard Python 6 mode | SQLite/reports + lựa chọn người dùng → tables/charts/prediction | Freshness banner, official/hypothetical contract, cùng-role warning |
| `src/reporting/final_report.py` | Tổng hợp trạng thái bàn giao | SQLite + phase reports → `reports/final-project-report.md` | Chỉ ghi số liệu đọc được từ workspace hiện tại |
| `notebooks/01_eda_s16.py` | Notebook dạng percent-cell dễ review Git | SQLite → bảng + 6 hình | Mỗi `# %%` code có cell Markdown giải thích liền trước |
| `notebooks/01_eda_s16.ipynb` | Bản chạy tương tác trong VS Code Jupyter | Cùng logic file percent-cell → cell outputs | Dùng để demo từng bước giống Colab |
| `scripts/sync_percent_notebook.py` | Đồng bộ `.py` percent-cell sang `.ipynb` | Python cell source → notebook JSON | Tránh sửa hai bản bằng tay rồi lệch nhau |
| `scripts/verify_environment.py` | Kiểm tra Python/package khoa học | Runtime → JSON `ready`/`missing` | Không bắt đầu demo khi scientific stack chưa đủ |
| `scripts/setup_vscode.ps1` | Tạo venv và cài dependency | Máy Windows + Python → `.venv-vscode` | Bootstrap một lần trên VS Code |
| `scripts/daily_update.ps1` | Chạy pipeline online hằng ngày | Web sources → refreshed DB/reports/figures | Fail-fast theo chuỗi collect → QA → DA → DS → report |
| `scripts/demo_offline.ps1` | Chạy nghiệm thu không crawl mạng | Local DB → test/reports/figures | Kịch bản an toàn trước buổi thuyết trình |

## 8. Test và fixture

| File/nhóm | Vai trò |
|---|---|
| `tests/test_foundation.py` | 31 regression tests cho config, parser, schema, upsert, EDA, schedule, visualization, prediction và leakage |
| `tests/fixtures/team_*.html` | HTML cố định để test directory/match list/team stats |
| `tests/fixtures/game_page.html`, `fullstats.html`, `draft_section.html`, `timeline.html` | Mẫu game-level cho parser, draft và objective timeline |
| `tests/fixtures/schedule*.{html,json}`, `leaguepedia_api.json` | Mẫu nhiều định dạng lịch đấu |

Fixture giúp test không phụ thuộc website đang online và bảo vệ parser trước regression. Nó không thay thế source audit định kỳ vì HTML thật có thể thay đổi.

## 9. File đầu ra và cách truy nguồn

| Output | Sinh bởi | Dùng để làm gì |
|---|---|---|
| `data/raw/YYYY-MM-DD/` + `crawl_manifest.jsonl` | `http_client.py` | Bằng chứng web và debug parser |
| `data/lol_analytics.db` | `database.py` | Single source of truth cục bộ |
| `data/processed/pandas_eda/*.csv` | `pandas_eda.py` | Xem bảng trung gian bằng VS Code Data Viewer |
| `reports/data-quality-phase-4.*` | `checks.py` | Quyết định có được phân tích tiếp không |
| `reports/statistics-phase-7.*` | `statistics.py` | CI, test, effect size và assumption |
| `reports/figures/*` | visualization modules/notebook | Bộ hình nộp và demo |
| `reports/backtest-phase-9.*` | `backtest.py` | Bằng chứng dự đoán không chỉ được đánh giá trên training data |
| `reports/final-project-report.md` | `final_report.py` | Snapshot bàn giao có số liệu thực tế |

## 10. Đường đọc nhanh theo mục tiêu

- Muốn hiểu scraping: `config.py` → `http_client.py` → `parsers.py` → `game_parsers.py` → `updater.py`.
- Muốn hiểu DA: `schema.sql` → `checks.py` → `pandas_eda.py` → `metrics.py` → `statistics.py` → `scientific_visualizations.py`.
- Muốn hiểu DS: `metrics.py` → `predictor.py` → `backtest.py`.
- Muốn demo: `scripts/demo_offline.ps1` → `app/streamlit_app.py` → `reports/final-project-report.md`.
- Muốn kiểm tra một kết quả: chart/report → CSV/query → SQLite row → raw HTML + manifest.
