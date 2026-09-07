# LoL Pro Analytics S16 — Final Project Handoff

Generated: `2026-09-07T17:30:03.929395+00:00`

## Product scope

Ứng dụng Python phân tích đội tuyển LCK cấp một và tuyển thủ trong Season 16, dùng Gol.gg làm nguồn thống kê chính. Dữ liệu trước 01/01/2026 và Academy/Challengers không đi vào phân tích chính.

## Completed pipeline

1. Source audit + robots check + rate-limited raw archive.
2. Team match-list parser và game-level parser.
3. SQLite schema version 1 với idempotent upsert.
4. Cleaning và 12 data-quality checks.
5. Team/player EDA, Pandas/NumPy inspection, rolling 5/10-game form và CSV exports.
6. Streamlit dashboard với 6 mode: one/two team, one/two player, matchup prediction và recent form.
7. Series/draft/current-roster và objective timeline milestone derivation từ game summary khi source cung cấp.
8. Wilson confidence intervals; introductory chi-square/z-test/Welch t-test khi dependency sẵn sàng; leakage-safe walk-forward baseline evaluation và explainable prediction.

## Evidence from current workspace

- SQLite tables: `19`; games: `667`; series: `271`; drafts: `13340`; timeline events: `5793`; teams: `23`; players: `152`; roster rows: `205`.
- Source audit report: `available`.
- Quality report: `available`; status `passed`.
- EDA report: `available`; team rows `10`, player rows `50`.
- Latest update run: `{'run_id': 'update-20260907T170423-dd255c9e', 'started_at': '2026-09-07T17:04:23.694347+00:00', 'finished_at': '2026-09-07T17:04:38.506657+00:00', 'status': 'success', 'pages_requested': 6, 'pages_changed': 5, 'rows_upserted': 125, 'error_count': 0}`.
- Latest all-team manifest: status `ok`, dry_run `False`, teams resolved `10/10`.
- Latest quality run: `{'run_at': '2026-09-07T17:29:36.917266+00:00', 'passed': 12, 'checks': 12}`.
- Sample prediction: `baseline_ready`; context `hypothetical`; fixture timestamp `None`.
- Statistical report: `available`; inferential status: `ok`; visualization status: `ok`.
- Walk-forward evaluation: `available`; games scored `581`; logistic warm-up predictions `577`; small-sample warning `False`.
- Schedule report: `available`; stored rows `5`; future rows at generation time `0`.

## Reproducible commands

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli health
.\.venv-vscode\Scripts\python.exe -m src.cli source-audit
.\.venv-vscode\Scripts\python.exe -m src.cli db-init
.\.venv-vscode\Scripts\python.exe -m src.cli update-all --dry-run --max-games-per-team 1
.\.venv-vscode\Scripts\python.exe -m src.cli update-all --max-games-per-team 3
.\.venv-vscode\Scripts\python.exe -m src.cli quality-check
.\.venv-vscode\Scripts\python.exe -m src.cli eda
.\.venv-vscode\Scripts\python.exe -m src.cli pandas-eda
.\.venv-vscode\Scripts\python.exe -m src.cli statistics-report --team-a-id 2809 --team-b-id 2805
.\.venv-vscode\Scripts\python.exe -m src.cli visualize --team-a-id 2809 --team-b-id 2805
.\.venv-vscode\Scripts\python.exe -m src.cli backtest
.\.venv-vscode\Scripts\python.exe -m src.cli update-schedule
.\scripts\daily_update.ps1 -MaxGamesPerTeam 5
.\.venv-vscode\Scripts\python.exe -m src.cli predict-matchup --team-a-id 2805 --team-b-id 2809
.\.venv-vscode\Scripts\python.exe -m src.cli player-report --player-id 1328
.\.venv-vscode\Scripts\python.exe -m src.cli player-compare --player-a-id 1328 --player-b-id 5204
.\.venv-vscode\Scripts\python.exe -m unittest discover -s tests -v
.\.venv-vscode\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

## Known limitations before final academic demo

- The local database contains the refreshed S16 Gol.gg snapshot (latest incremental update recorded in SQLite): `667` game pages across all 10 configured LCK primary teams, plus external tournament opponents retained as non-primary dimensions.
- Team gold/GPM/GDM, first blood/first tower, draft actions, objective milestone timestamps (`5793` events) and Gol.gg full-stats player fields are populated for the current S16 snapshot; unsupported event streams remain nullable by source contract.
- Prediction includes an explainable baseline and educational logistic walk-forward comparison over the current LCK-only pair sample; it is evidence-backed but still requires calibration monitoring before production decisions.
- `.venv-vscode` scientific stack đã verified; notebook 19 code cells sinh 6 hình và Matplotlib/Seaborn renderer sinh 14 rich PNG. SciPy/Statsmodels tests đã chạy; assumption warning vẫn phải được trình bày.
- Schedule fixtures are sourced from Leaguepedia MediaWiki API stage pages. `5` normalized historical/current rows are stored and `0` remain in the future at report time; without a valid future fixture, matchup output must stay labelled hypothetical.

## Deliverables

- Source code: `src/collection`, `src/storage`, `src/quality`, `src/analysis`, `src/modeling`.
- App: `app/streamlit_app.py`.
- Reproducible notebook: `notebooks/01_eda_s16.ipynb`.
- Reports: `reports/source-audit-phase-2.*`, `data-quality-phase-4.*`, `eda-phase-5.*`, `prediction-*.json`.
- Update manifest: `reports/update-all-latest.json`.
- Statistical evidence: `reports/statistics-phase-7.*`.
- Prediction evaluation: `reports/backtest-phase-9.*`.
- Visualization manifest: `reports/visualization-phase-8.json` and `reports/figures/`.
- Data contract: `docs/DATA_SCHEMA.md`.
- Requirements traceability: `docs/REQUIREMENTS_TRACEABILITY.md`.
- Historical upgrade audit: `reports/upgrade-qa-2026-08-28.md`; latest release audit: `reports/release-readiness-2026-09-08.md`.
- Learning documents: `docs/01_PROJECT_OVERVIEW.md`, `docs/02_VSCODE_HANDS_ON_GUIDE.md`, `docs/03_DA_DS_PLAYBOOK.md`, `docs/04_REFERENCE_ALIGNMENT.md`, `docs/05_CODEBASE_FILE_GUIDE.md`.
- VS Code cell-by-cell EDA: `notebooks/01_eda_s16.py`.
- Roadmap: `ROADMAP.md`.
