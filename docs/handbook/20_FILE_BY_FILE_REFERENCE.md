# 20 — File-by-file reference

Đây là bản tra cứu nhanh; giải thích đầy đủ hơn ở `docs/05_CODEBASE_FILE_GUIDE.md`.

| Path | Vai trò | Đọc khi |
|---|---|---|
| `src/config.py` | config/policy/paths | đổi season, scope, TTL |
| `src/cli.py` | command router | chạy pipeline |
| `src/logging_config.py` | logging | debug runtime |
| `src/collection/http_client.py` | cache/HTTP | tải raw |
| `src/collection/parsers.py` | team/match HTML | directory/list |
| `src/collection/game_parsers.py` | game/fullstats HTML | game facts |
| `src/collection/schedule.py` | fixture parser/upsert | next match |
| `src/collection/updater.py` | orchestration | team/all update |
| `src/collection/source_audit.py` | source coverage | audit freshness |
| `src/storage/database.py` | schema/upsert/repair | DB integrity |
| `src/quality/cleaning.py` | canonical values | raw cleanup |
| `src/quality/checks.py` | data contract | gate publish |
| `src/analysis/metrics.py` | DA summaries | KPI/comparison |
| `src/analysis/pandas_eda.py` | DataFrame EDA | profiling |
| `src/analysis/statistics.py` | uncertainty/tests | inference |
| `src/analysis/visualizations.py` | core charts | artifact generation |
| `src/analysis/scientific_visualizations.py` | advanced charts | research figures |
| `src/analysis/reports.py` | team/H2H/player reports | narrative |
| `src/modeling/predictor.py` | matchup prediction | interactive estimate |
| `src/modeling/backtest.py` | walk-forward model | evaluation |
| `src/reporting/final_report.py` | final report | delivery |
| `src/app/streamlit_app.py` | UI | demo/dashboard |
| `scripts/verify_environment.py` | env smoke test | setup |
| `scripts/sync_percent_notebook.py` | notebook sync | reproducibility |
| `notebooks/01–04` | staged learning/demo | guided exploration |
| `tests/` | contracts/regression | before commit |
| `docs/01–05` | existing project docs | context/runbook/reference |
| `reports/` | generated evidence | inspect results |

## 📱 Phone Mode

Trace one request: `cli → config → updater → parser → DB → metrics → report/app`. Mỗi layer chỉ nên có một owner.

## ✅ Checkpoint

Chọn bất kỳ output nào và truy ngược được ít nhất 3 file upstream.

