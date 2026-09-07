# Runbook — LoL Pro Analytics S16

## 1. Environment

Môi trường demo chuẩn của project là `.venv-vscode/Scripts/python.exe`, được VS Code workspace chọn sẵn. Không dùng `.venv/bin/python.exe` của MSYS cho notebook, biểu đồ hoặc Streamlit.

The complete scientific stack is declared in `requirements.txt`. The scraper-only fallback is in `requirements-phase2.txt`.

## 2. Daily update sequence

Hoặc chạy gọn bằng `./scripts/daily_update.ps1 -MaxGamesPerTeam 3`. Script giữ thứ tự crawl → quality → EDA → statistics → visualization → backtest → schedule → freshness.

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli update-all --dry-run --max-games-per-team 1
.\.venv-vscode\Scripts\python.exe -m src.cli update-all --max-games-per-team 3 --include-fullstats
.\.venv-vscode\Scripts\python.exe -m src.cli quality-check
.\.venv-vscode\Scripts\python.exe -m src.cli eda
.\.venv-vscode\Scripts\python.exe -m src.cli pandas-eda
.\.venv-vscode\Scripts\python.exe -m src.cli statistics-report
.\.venv-vscode\Scripts\python.exe -m src.cli visualize
.\.venv-vscode\Scripts\python.exe -m src.cli backtest
.\.venv-vscode\Scripts\python.exe -m src.cli update-schedule
```

Repeat `update-team` for each of the 10 configured primary LCK teams. Use `--max-games 0` only after checking rate limits and source load.

For a controlled all-team seed/update, use `update-all --dry-run --max-games-per-team 1` first, then remove `--dry-run`. Keep `--max-games-per-team` small during development; use `0` only for a deliberate full refresh. If an uncached page fails, the updater records a `partial` run and preserves the cached/previously validated facts; do not fill missing advanced fields manually.

## 3. Query/demo sequence

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli predict-matchup --team-a-id 2805 --team-b-id 2809
.\.venv-vscode\Scripts\python.exe -m src.cli h2h-report --team-a-id 2805 --team-b-id 2809
.\.venv-vscode\Scripts\python.exe -m src.cli player-report --player-id 1328
.\.venv-vscode\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

The UI supports team overview, team comparison, player overview, player comparison, matchup prediction and recent form.

## 4. Quality gate

Run `quality-check` before EDA or prediction. A failed status means the dataset must not be presented as analysis-ready. Inspect `reports/data-quality-phase-4.md` and `data_quality_results` for affected rows.

## 5. Reproducibility

Every raw page is archived under `data/raw/YYYY-MM-DD/` with a content hash in `data/raw/crawl_manifest.jsonl`. SQLite facts are upserted by source IDs. Reports include data cutoff, status and sample size.

Each `update-all` run also writes `reports/update-all-latest.json`, including per-team resolution, selected game pages, upsert counts and fetch errors. This manifest is the handoff evidence for a daily refresh.

`update-schedule` is intentionally separate from Gol.gg statistics: it uses the configured supplemental source, normalizes timestamps to UTC, ignores unknown/non-primary teams and writes `reports/schedule-latest.json`.
