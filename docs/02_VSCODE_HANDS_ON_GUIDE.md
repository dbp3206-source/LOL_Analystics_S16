# 02 — Hướng dẫn học và chạy project trên VS Code

Tài liệu này tổ chức project theo tư duy giải quyết vấn đề. Không nên bắt đầu bằng dashboard vì như vậy chỉ thấy kết quả mà không hiểu dữ liệu đi qua những bước nào.

## 1. Chuẩn bị một lần

### Bước 1 — Mở đúng workspace

Trong VS Code chọn **File → Open Folder** và mở thư mục `lol-pro-analytics-s16`. Khi mở đúng, Explorer phải thấy `src`, `data`, `reports`, `tests` và `.vscode`.

### Bước 2 — Chuẩn bị Python

Project dùng Windows CPython 3.12 x64. Trong PowerShell terminal:

```powershell
.\scripts\setup_vscode.ps1
```

Script thực hiện ba việc: tạo `.venv-vscode`, cài `requirements.txt`, sau đó chạy `scripts/verify_environment.py`.

Nếu VS Code chưa tự nhận interpreter, nhấn `Ctrl+Shift+P` → **Python: Select Interpreter** → chọn:

```text
.venv-vscode\Scripts\python.exe
```

### Bước 3 — Xác nhận môi trường

Nhấn `Ctrl+Shift+P` → **Tasks: Run Task** → **Python: Verify DA/DS environment**.

Kết quả hợp lệ phải có `"status": "ready"` và danh sách `missing` rỗng. Nếu còn missing, không nên demo notebook, visualization hoặc Streamlit.

## 2. Thứ tự đọc code khuyến nghị

| Thứ tự | File | Câu hỏi cần trả lời sau khi đọc |
|---:|---|---|
| 1 | `README.md` | Project làm gì và có lệnh nào? |
| 2 | `docs/01_PROJECT_OVERVIEW.md` | Luồng DA/DS tổng thể là gì? |
| 3 | `configs/project.json` | Phạm vi S16, 10 đội và nguồn được khóa thế nào? |
| 4 | `src/config.py` | JSON trở thành Python object và được validate ra sao? |
| 5 | `src/collection/http_client.py` | Cache, retry, rate limit, raw archive hoạt động thế nào? |
| 6 | `src/collection/parsers.py` | Từ HTML danh sách đội/trận lấy được dữ liệu gì? |
| 7 | `src/collection/game_parsers.py` | Một game được tách thành team/player/draft/timeline thế nào? |
| 8 | `src/storage/schema.sql` | Vì sao cần các bảng dimension/fact và khóa ngoại? |
| 9 | `src/storage/database.py` | Upsert chống trùng và refresh starting five ra sao? |
| 10 | `src/quality/cleaning.py` | Text và role được chuẩn hóa thế nào? |
| 11 | `src/quality/checks.py` | 12 điều kiện nào quyết định data analysis-ready? |
| 12 | `src/analysis/pandas_eda.py` | Pandas/NumPy biến dữ liệu sạch thành insight ban đầu ra sao? |
| 13 | `src/analysis/metrics.py` | Feature nghiệp vụ được tính như thế nào? |
| 14 | `src/analysis/statistics.py` | Sample size và khoảng tin cậy được xử lý ra sao? |
| 15 | `src/analysis/visualizations.py` | Mỗi hình trả lời câu hỏi gì? |
| 16 | `src/modeling/predictor.py` | Probability được tạo từ evidence nào? |
| 17 | `src/modeling/backtest.py` | Vì sao phải train trên quá khứ rồi test ở tương lai? |
| 18 | `app/streamlit_app.py` | Các kết quả được ghép thành giao diện thế nào? |
| 19 | `tests/test_foundation.py` | Những giả định quan trọng nào đã được tự động kiểm tra? |

Sau bảng đọc nhanh này, dùng `docs/05_CODEBASE_FILE_GUIDE.md` để tra trách nhiệm, input, output và logic cốt lõi của toàn bộ file thực thi, script, notebook, fixture và artifact.

## 3. Luồng chạy tối thiểu không truy cập web

Luồng này dùng database hiện có, phù hợp để học và demo offline.

### 3.1 Health check

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli health
```

- Input: `configs/project.json`.
- Xử lý: đọc cấu hình, validate season/source/team count và tạo đường dẫn runtime nếu cần.
- Output: JSON trạng thái cơ bản.

### 3.2 Quality gate

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli quality-check
```

- Input: `data/lol_analytics.db`.
- Xử lý: cleaning rồi chạy 12 SQL checks.
- Output: `reports/data-quality-phase-4.md` và `.json`.
- Quyết định: nếu status không phải `passed`, dừng trước EDA/prediction và đọc affected rows.

### 3.3 EDA nền và EDA Pandas

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli eda
.\.venv-vscode\Scripts\python.exe -m src.cli pandas-eda
```

`eda` tạo bảng nghiệp vụ tái sử dụng. `pandas-eda` trình bày thao tác học thuật tương tự Colab. Hãy mở từng CSV trong `data/processed/pandas_eda/` bằng VS Code Data Viewer:

1. `missingness.csv` — cột nào thiếu và thiếu bao nhiêu phần trăm;
2. `team_numeric_summary.csv` — thống kê mô tả chỉ số đội;
3. `player_numeric_summary.csv` — thống kê mô tả chỉ số tuyển thủ;
4. `iqr_outlier_candidates.csv` — điểm nào cần rà soát;
5. `side_outcome_crosstab.csv` — side và kết quả;
6. `role_summary.csv` — baseline theo role;
7. `tournament_summary.csv` — khác biệt theo giải;
8. `team_metric_correlation.csv` — ma trận tương quan.

### 3.4 Statistics, visualization và backtest

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli statistics-report --team-a-id 2809 --team-b-id 2805
.\.venv-vscode\Scripts\python.exe -m src.cli visualize --team-a-id 2809 --team-b-id 2805
.\.venv-vscode\Scripts\python.exe -m src.cli backtest
```

Đọc output theo thứ tự: statistics trước để biết uncertainty, visualization để hiểu pattern, backtest cuối để đánh giá dự đoán trên dữ liệu chưa được mô hình nhìn thấy ở thời điểm dự đoán.

Nếu `statistics-report` ghi `inferential_status=skipped`, mở trường `missing_optional_packages`: đó là trạng thái hợp lệ khi máy chưa có SciPy/Statsmodels. Wilson CI vẫn chạy. Không được trình bày rằng chi-square/z-test/t-test đã cho kết quả trước khi trạng thái là `ok` hoặc `partial` và report thực sự có p-value.

Notebook `notebooks/01_eda_s16.ipynb` nên chạy đủ 19 code cells từ trên xuống. Cell 1–12 dạy load/inspect/EDA bảng; Cell 13 kiểm tra môi trường; Cell 14–19 lần lượt minh họa histogram+KDE/boxplot, violin, 100% stacked bar, bubble scatter, correlation heatmap và rolling line. Các cell hình tự bỏ qua, không làm hỏng luồng Pandas, nếu package chưa cài.

### 3.5 Chạy toàn bộ test

```powershell
.\.venv-vscode\Scripts\python.exe -m unittest discover -s tests -v
```

Mỗi dòng `ok` là một hành vi đã được kiểm tra. Test không chứng minh mọi kết quả đều đúng tuyệt đối, nhưng ngăn các lỗi đã biết quay trở lại.

## 4. Luồng cập nhật dữ liệu web

Chỉ chạy khi có mạng và cần lấy dữ liệu mới.

### Bước 1 — Dry run

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli update-all --dry-run --max-games-per-team 1
```

Dry run cho biết hệ thống sẽ lấy gì mà chưa crawl toàn bộ. Đây là bước kiểm soát phạm vi và tránh tạo tải không cần thiết cho nguồn.

### Bước 2 — Incremental update nhỏ

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli update-all --max-games-per-team 3 --include-fullstats
```

HTTP client ưu tiên cache còn mới. Trang thay đổi được lưu raw, parser chuyển HTML thành object, database upsert theo source ID.

### Bước 3 — Kiểm tra lại toàn pipeline

```powershell
.\scripts\daily_update.ps1 -MaxGamesPerTeam 3
```

Script chạy tuần tự crawl → quality → EDA → statistics → visualization → backtest → schedule → freshness và dừng ngay nếu một lệnh quan trọng lỗi.

## 5. Chạy từng dòng/đoạn như Google Colab trong VS Code

Notebook `notebooks/01_eda_s16.ipynb` có 38 cell (19 cặp giải thích/code) và dùng nút **Run Cell**. Bản nguồn `01_eda_s16.py` chia cell bằng marker:

```python
# %%
import pandas as pd

# %%
frame = pd.read_csv("data/processed/team_summary.csv")
frame.head()
```

Đặt con trỏ trong cell rồi chọn **Run Cell**. Luôn chạy từ trên xuống vì biến ở cell sau có thể phụ thuộc cell trước. Nếu chạy cell giữa trước và gặp `NameError`, hãy chọn **Restart Kernel and Run All**.

Quy tắc học mỗi cell:

1. đọc comment “mục tiêu”;
2. đoán shape/kiểu output;
3. chạy cell;
4. đối chiếu kết quả với dự đoán;
5. sửa một tham số nhỏ và quan sát thay đổi;
6. trả dữ liệu về trạng thái gốc trước khi demo.

## 6. Demo sáu mode

### 6.1 Demo offline một nút trước khi mở dashboard

Trong VS Code, nhấn `Ctrl+Shift+P` → **Tasks: Run Task** → chọn **Demo: Run offline T1 vs HLE**. Task chạy test → quality → Pandas EDA → statistics → visualization → backtest → final report, hoàn toàn từ SQLite hiện có nên không phụ thuộc mạng.

Lệnh tương đương:

```powershell
.\scripts\demo_offline.ps1 -TeamAId 2809 -TeamBId 2805
```

Muốn đổi cặp đội, thay hai ID. Script không ép query một đội/một player thành hai entity; các mode đó vẫn dùng CLI/dashboard riêng.

### 6.2 Mở dashboard

Khởi động ứng dụng:

```powershell
.\.venv-vscode\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

Kịch bản demo nên đi theo thứ tự:

1. đọc freshness banner và data cutoff;
2. chọn **Team overview** để xem một đội;
3. chọn **Player overview** để giải thích metric cá nhân/champion pool;
4. chọn **Team comparison** cho T1 và HLE;
5. giải thích role matchup cùng vị trí;
6. mở prediction, nói rõ official fixture hay hypothetical;
7. mở **Player comparison** để giải thích cảnh báo khi khác role;
8. mở **Recent form** để đọc rolling win rate và kills/deaths theo thứ tự trận;
9. kết thúc bằng uncertainty, sample warning và limitation.

## 7. Cách đọc một hàm Python trong project

Ví dụ khi gặp `run_pandas_eda(config, output_root=None)`:

- tên hàm: hành động chính là “chạy EDA”;
- tham số `config`: nguồn đường dẫn và quy tắc S16;
- tham số optional: cho phép test ghi vào thư mục tạm;
- docstring: hợp đồng input/output;
- phần đầu hàm: load và validate;
- phần giữa: transform/aggregate;
- phần cuối: ghi artifact và return manifest.

Hãy phân biệt:

- `return`: trả object cho code gọi hàm;
- `write_text`/`to_csv`: tạo file bền vững;
- `print`: chỉ hiển thị terminal;
- `raise`: dừng luồng khi giả định quan trọng bị vi phạm.

## 8. Checklist trước khi thuyết trình

- Task verify environment trả `ready`.
- 31 test hiện có đều pass hoặc số test mới cao hơn và đều pass.
- Quality report là 12/12 passed.
- Data cutoff là ngày cập nhật gần nhất.
- Notebook đã Restart Kernel and Run All.
- Figure không bị cắt chữ, legend hoặc đơn vị.
- Prediction dùng đúng fixture nếu gọi là “trận tiếp theo”.
- Có thể giải thích ít nhất một dòng dữ liệu từ raw → SQLite → CSV → chart.
- Không nói correlation là nguyên nhân.
- Không kết luận mạnh từ champion/sample chỉ có 1–4 game.
