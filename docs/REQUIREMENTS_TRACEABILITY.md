# Đối chiếu yêu cầu và trạng thái nghiệm thu

Ngày kiểm tra: 2026-09-08. Phạm vi chính là LCK primary, Season 16 từ `2026-01-01`; Gol.gg là nguồn thống kê chính, nguồn lịch bổ sung chỉ dùng cho fixture.

| Yêu cầu ban đầu | Bằng chứng trong project | Trạng thái |
|---|---|---|
| Nhập 1 đội, 1 tuyển thủ, 2 tuyển thủ hoặc 2 đội | Streamlit có Team overview, Team comparison, Player overview, Player comparison; CLI `team-report`, `player-report`, `player-compare`, `h2h-report` | Hoàn thành và browser-QA |
| Không lấy Academy/Challengers, chỉ starting five | Alias/config primary LCK, non-primary external opponent flags, `roster_periods` latest-period join, quality check 5 người/team | Hoàn thành |
| Chỉ dùng S16 và dữ liệu update hằng ngày | Season constraint, cutoff `2026-01-01`, cache freshness 24h, CLI `freshness`, `update-all`, `scripts/daily_update.ps1` | Hoàn thành; snapshot hiện tại đã crawl full |
| Scrape Gol.gg, lưu raw, retry/cache/manifest | `src/collection/http_client.py`, raw HTML, crawl manifests, update-all manifest | Hoàn thành |
| Lịch sử trận, series, tournament, game number | `series`, `games.series_id`, `games.game_number`, H2H detail report | Hoàn thành trên dữ liệu đã crawl |
| Team stats: win rate, K/D, GPM/GDM, DPM, CS/D@15, first blood/tower, side | `team_summary`, `team_side_summary`, parser summary/fullstats, EDA CSV | Hoàn thành trường đã source cung cấp |
| Player stats: KDA, DPM, CSM, gold share, vision, CS@15/GD@15/XP@15, solo kills | `parse_fullstats_page`, `upsert_fullstats`, player summary/champion pool | Hoàn thành: 6.420/6.420 rows có DPM/CSM; GD@15/CSD@15 có 6.410/6.420 do source thiếu 10 giá trị; không tự điền giả |
| Champion pool, pick/win rate, breadth và cảnh báo mẫu nhỏ | `champion_pool`, `data/processed/champion_pool.csv`, dashboard section | Hoàn thành |
| So sánh H2H và từng role | `h2h-report`, `_role_matchups`, cảnh báo cross-role | Hoàn thành bản descriptive |
| Visualization đa dạng, có câu hỏi nghiệp vụ | `scientific_visualizations.py` gồm 12 global + 2 T1–HLE chart: heatmap, lollipop, scatter/bubble, box, violin, stacked bar, sequential small multiples, dumbbell | 14 rich PNG đã render/visual QA; notebook sinh thêm 6 hình; 8 SVG fallback vẫn có |
| Thống kê đúng chuẩn, không kết luận quá mức | Wilson CI; chi-square, z-test hai tỷ lệ, Welch t-test GDM, Cohen's d; assumption và limitation trong report Phase 7 | `inferential_status=ok`; chi-square vẫn mang `assumption_warning` do paired rows và bị cấm dùng như confirmatory result |
| Predict trận kế tiếp, không leakage | `predict-matchup`, data cutoff, feature version, H2H blend; `backtest` walk-forward baseline + Logistic Regression accuracy/Brier/log loss | Hoàn thành trên 581 baseline predictions và 577 Logistic Regression predictions; hiện chưa có fixture tương lai được schedule supplement xác nhận |
| Lịch thi đấu ngoài LCK nếu có | `update-schedule`, JSON-LD/HTML/LoL Esports API + Leaguepedia MediaWiki parser, UTC normalization, fixture tests | Hoàn thành collector: 2 fixture cũ đã lưu; lần refresh 28/08 không tìm thấy fixture tương lai mới, nên app gắn nhãn matchup giả định |
| Pandas/NumPy EDA theo luồng Colab | `src/analysis/pandas_eda.py`, 8 bảng tại `data/processed/pandas_eda/`, báo cáo `reports/pandas-eda-phase.*` | Hoàn thành; nối tiếp bằng 14 scientific PNG và 6 notebook PNG đã visual-QA |
| Report, README, roadmap, runbook, file guide, test | `reports/final-project-report.md`, `README.md`, `ROADMAP.md`, `docs/RUNBOOK.md`, `docs/05_CODEBASE_FILE_GUIDE.md`, 31 unit tests | Hoàn thành; kết quả tái kiểm duyệt ở `reports/release-readiness-2026-09-08.md` |

## Bằng chứng chạy lần cuối

- `.\.venv-vscode\Scripts\python.exe -m unittest discover -s tests -v`: **31/31 passed** trong môi trường hiện tại; gồm test rolling-form theo quá khứ, test report dùng thư mục tạm và không ghi đè output thật.
- Notebook EDA: **38 cells**, cân bằng 19 Markdown hướng dẫn và 19 code cells; bản percent-cell `.py` đã chạy thành công trên snapshot thật và sinh 6 PNG. Cơ chế skip vẫn được giữ cho máy tối giản.
- `quality-check`: **12/12 passed**, gồm draft uniqueness, đúng 10 picks/10 bans và GPM/GDM đúng miền/đơn vị.
- GDM đã được migration từ total final gold difference về gold differential per minute; toàn DB hiện có range `[-1047.73, 1047.73]` và hai phía mỗi game cộng bằng 0.
- Database: 667 game pages, 271 series, **13.340 draft actions (20/game)**, 152 player dimensions (50 current LCK starters qua roster scope), 205 roster-period rows; external opponents are non-primary.
- Full-stats coverage: 6.670/6.670 player-game rows có DPM và CSM; GD@15/CSD@15 là 6.660/6.670, giữ `NULL` đúng nguồn cho 10 giá trị thiếu.
- `backtest`: 581 LCK-only baseline predictions scored; baseline accuracy 59,55%, Brier 0,2375, log loss 0,6679; Logistic Regression có 577 predictions, accuracy 60,14%, Brier 0,2399, log loss 0,6764.
- `pandas-eda`: thành công với 1.248 primary team-game rows và 5.397 current-starter player-game rows; sinh 8 bảng kiểm tra/phân tích bằng Pandas/NumPy.
- `visualize --team-a-id 2809 --team-b-id 2805`: `renderer=matplotlib-seaborn`, sinh 14 PNG; các nhóm hình đại diện đã được mở kiểm tra trực quan và rolling-form được sửa sau QA.
- AST learning audit: **163/163 function/class definitions có docstring**; inline comments giải thích các đoạn nghiệp vụ hoặc logic dễ sai thay vì lặp lại cú pháp hiển nhiên.
- Timeline: **5.793 objective milestone events trên 666/667 game**; gồm first blood, first tower, dragon, herald và Nashor.
- `update-schedule`: Leaguepedia MediaWiki API chạy thành công ngày 08/09/2026; 3 fixture được parse/upsert trong lượt mới nhất. Tại thời điểm final report chưa có fixture tương lai cụ thể, nên dashboard vẫn hiển thị đúng `hypothetical`, không gọi là “trận kế tiếp”.

## Những việc còn lại để nâng từ bản hoàn thiện học thuật lên bản production

1. Scientific stack đã cài và verifier trả `ready`; cần giữ `.venv-vscode` khi demo hoặc chạy lại `scripts/setup_vscode.ps1` trên máy mới.
2. Tiếp tục chạy `update-schedule` hằng ngày để bracket TBD được thay bằng tên đội sau khi kết quả cập nhật.
3. Không thêm Random Forest/GridSearch vào core vì không cần thiết cho scope năm 3; tập trung giải thích đúng baseline, Logistic Regression, p-value, effect size và limitation.
4. Tiếp tục daily update để snapshot S16 không bị stale; các event chi tiết khác (từng kill/CS theo giây) vẫn nullable vì không nằm trong hợp đồng nguồn hiện tại.
