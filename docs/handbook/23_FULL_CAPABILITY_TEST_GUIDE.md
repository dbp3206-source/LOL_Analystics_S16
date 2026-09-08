# 23 — Full capability test guide

Mỗi lab có **precondition → command → expected output → file → debug path**. Chạy theo thứ tự để tránh test downstream trên DB rỗng.

| Capability | Command/route | Expected evidence |
|---|---|---|
| Environment | `python scripts/verify_environment.py` | dependency/version report |
| Health | `python -m src.cli health` | JSON status ok, S16, 10 teams |
| Config | `python -m src.cli show-config` | project/season/source |
| DB schema | documented init/runbook command | table counts/schema |
| Collection | update command in `docs/RUNBOOK.md` | raw/cache + update log |
| Dry run | updater dry-run option if configured | URLs/counts, no mutation |
| Source audit | run source-audit command | coverage/freshness report |
| Quality | quality command | PASS/warnings |
| EDA | EDA command/notebook 01 | profile/summary |
| Pandas | notebook 02 | DataFrames/plots |
| Team report | CLI/report route | team markdown/CSV |
| Player report | CLI/report route | player stats/champions |
| Compare | compare route | side-by-side table |
| H2H | matchup route | historical rows |
| Statistics | statistics route | intervals/tests |
| Visuals | visualization route | PNG/SVG files |
| Prediction | predict route | probability + cutoff |
| Backtest | backtest route | chronological folds |
| Notebook sync | `scripts/sync_percent_notebook.py` | deterministic notebook text |
| Streamlit | `streamlit run src/app/streamlit_app.py` | UI tabs/empty states |
| Final report | report command | `reports/final_report.md` |
| Tests | `python -m unittest discover -s tests -v` | 31/31 OK |

## 📱 Phone Mode

Nếu không thể chạy terminal, dùng mỗi row như a read-only walkthrough: input → function → output → artifact → what can fail. Không gọi capability “verified” chỉ từ đọc code.

## 🧪 Automated Test

Đã chạy full suite **RUNTIME-VERIFIED**: `Ran 31 tests ... OK`; dashboard/browser và internet refresh chưa được claim verified (**LIMITATION**).

## 🛠 Debug order

Environment → config → DB counts → quality → analysis → visual → model → UI.

## ✅ Checkpoint

Bạn có checklist demo end-to-end và biết evidence nào cần chụp/đính kèm.

