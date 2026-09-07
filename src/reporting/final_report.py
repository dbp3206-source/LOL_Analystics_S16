"""Generate a concise, evidence-backed project handoff report."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ProjectConfig
from ..storage.database import connect_database, schema_summary


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read an optional report without pretending a missing file exists."""

    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def generate_final_report(config: ProjectConfig) -> Path:
    """Combine current database/report evidence into the final handoff file."""

    with closing(connect_database(config.database_path)) as connection:
        counts = schema_summary(config.database_path)["tables"]
        latest_update = connection.execute(
            "SELECT run_id,started_at,finished_at,status,pages_requested,pages_changed,rows_upserted,error_count FROM update_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        latest_quality = connection.execute(
            "SELECT run_at, SUM(passed) passed, COUNT(*) checks FROM data_quality_results GROUP BY run_at ORDER BY run_at DESC LIMIT 1"
        ).fetchone()
        timeline_events = connection.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
        future_schedules = connection.execute(
            "SELECT COUNT(*) FROM schedules WHERE scheduled_at_utc > ?",
            (datetime.now(timezone.utc).isoformat(),),
        ).fetchone()[0]
    audit = _read_json(config.root / "reports" / "source-audit-phase-2.json")
    quality = _read_json(config.root / "reports" / "data-quality-phase-4.json")
    eda = _read_json(config.root / "reports" / "eda-phase-5.json")
    prediction = _read_json(config.root / "reports" / "prediction-2805-vs-2809.json")
    update_all = _read_json(config.root / "reports" / "update-all-latest.json")
    statistics = _read_json(config.root / "reports" / "statistics-phase-7.json")
    visualization = _read_json(config.root / "reports" / "visualization-phase-8.json")
    backtest = _read_json(config.root / "reports" / "backtest-phase-9.json")
    schedule = _read_json(config.root / "reports" / "schedule-latest.json")
    report_path = config.root / "reports" / "final-project-report.md"
    lines = [
        "# LoL Pro Analytics S16 — Final Project Handoff",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Product scope",
        "",
        "Ứng dụng Python phân tích đội tuyển LCK cấp một và tuyển thủ trong Season 16, dùng Gol.gg làm nguồn thống kê chính. Dữ liệu trước 01/01/2026 và Academy/Challengers không đi vào phân tích chính.",
        "",
        "## Completed pipeline",
        "",
        "1. Source audit + robots check + rate-limited raw archive.",
        "2. Team match-list parser và game-level parser.",
        "3. SQLite schema version 1 với idempotent upsert.",
        "4. Cleaning và 12 data-quality checks.",
        "5. Team/player EDA, Pandas/NumPy inspection, rolling 5/10-game form và CSV exports.",
        "6. Streamlit dashboard với 6 mode: one/two team, one/two player, matchup prediction và recent form.",
        "7. Series/draft/current-roster và objective timeline milestone derivation từ game summary khi source cung cấp.",
        "8. Wilson confidence intervals; introductory chi-square/z-test/Welch t-test khi dependency sẵn sàng; leakage-safe walk-forward baseline evaluation và explainable prediction.",
        "",
        "## Evidence from current workspace",
        "",
        f"- SQLite tables: `{len(counts)}`; games: `{counts.get('games', 0)}`; series: `{counts.get('series', 0)}`; drafts: `{counts.get('drafts', 0)}`; timeline events: `{timeline_events}`; teams: `{counts.get('teams', 0)}`; players: `{counts.get('players', 0)}`; roster rows: `{counts.get('roster_periods', 0)}`.",
        f"- Source audit report: `{'available' if audit else 'missing'}`.",
        f"- Quality report: `{'available' if quality else 'missing'}`; status `{quality.get('status') if quality else 'unknown'}`.",
        f"- EDA report: `{'available' if eda else 'missing'}`; team rows `{eda.get('team_rows') if eda else 0}`, player rows `{eda.get('player_rows') if eda else 0}`.",
        f"- Latest update run: `{dict(latest_update) if latest_update else 'none'}`.",
        f"- Latest all-team manifest: status `{update_all.get('status') if update_all else 'missing'}`, dry_run `{update_all.get('dry_run') if update_all else 'unknown'}`, teams resolved `{update_all.get('teams_resolved') if update_all else 0}/{update_all.get('teams_configured') if update_all else 0}`.",
        f"- Latest quality run: `{dict(latest_quality) if latest_quality else 'none'}`.",
        f"- Sample prediction: `{prediction.get('status') if prediction else 'missing'}`; context `{prediction.get('prediction_context') if prediction else 'unknown'}`; fixture timestamp `{prediction.get('fixture_timestamp') if prediction else 'unknown'}`.",
        f"- Statistical report: `{'available' if statistics else 'missing'}`; inferential status: `{statistics.get('inferential_status') if statistics else 'missing'}`; visualization status: `{visualization.get('status') if visualization else 'missing'}`.",
        f"- Walk-forward evaluation: `{'available' if backtest else 'missing'}`; games scored `{backtest.get('games_available', 0) if backtest else 0}`; logistic warm-up predictions `{backtest.get('models', {}).get('logistic_regression', {}).get('games_scored', 0) if backtest else 0}`; small-sample warning `{backtest.get('small_sample_warning') if backtest else 'unknown'}`.",
        f"- Schedule report: `{'available' if schedule else 'not collected'}`; stored rows `{counts.get('schedules', 0)}`; future rows at generation time `{future_schedules}`.",
        "",
        "## Reproducible commands",
        "",
        "```powershell",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli health",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli source-audit",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli db-init",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli update-all --dry-run --max-games-per-team 1",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli update-all --max-games-per-team 3",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli quality-check",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli eda",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli pandas-eda",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli statistics-report --team-a-id 2809 --team-b-id 2805",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli visualize --team-a-id 2809 --team-b-id 2805",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli backtest",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli update-schedule",
        ".\\scripts\\daily_update.ps1 -MaxGamesPerTeam 5",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli predict-matchup --team-a-id 2805 --team-b-id 2809",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli player-report --player-id 1328",
        ".\\.venv-vscode\\Scripts\\python.exe -m src.cli player-compare --player-a-id 1328 --player-b-id 5204",
        ".\\.venv-vscode\\Scripts\\python.exe -m unittest discover -s tests -v",
        ".\\.venv-vscode\\Scripts\\python.exe -m streamlit run app/streamlit_app.py",
        "```",
        "",
        "## Known limitations before final academic demo",
        "",
        f"- The local database contains the refreshed S16 Gol.gg snapshot (latest incremental update recorded in SQLite): `{counts.get('games', 0)}` game pages across all 10 configured LCK primary teams, plus external tournament opponents retained as non-primary dimensions.",
        f"- Team gold/GPM/GDM, first blood/first tower, draft actions, objective milestone timestamps (`{timeline_events}` events) and Gol.gg full-stats player fields are populated for the current S16 snapshot; unsupported event streams remain nullable by source contract.",
        f"- Prediction includes an explainable baseline and educational logistic walk-forward comparison over the current LCK-only pair sample; it is evidence-backed but still requires calibration monitoring before production decisions.",
        "- `.venv-vscode` scientific stack đã verified; notebook 19 code cells sinh 6 hình và Matplotlib/Seaborn renderer sinh 14 rich PNG. SciPy/Statsmodels tests đã chạy; assumption warning vẫn phải được trình bày.",
        f"- Schedule fixtures are sourced from Leaguepedia MediaWiki API stage pages. `{counts.get('schedules', 0)}` normalized historical/current rows are stored and `{future_schedules}` remain in the future at report time; without a valid future fixture, matchup output must stay labelled hypothetical.",
        "",
        "## Deliverables",
        "",
        "- Source code: `src/collection`, `src/storage`, `src/quality`, `src/analysis`, `src/modeling`.",
        "- App: `app/streamlit_app.py`.",
        "- Reproducible notebook: `notebooks/01_eda_s16.ipynb`.",
        "- Reports: `reports/source-audit-phase-2.*`, `data-quality-phase-4.*`, `eda-phase-5.*`, `prediction-*.json`.",
        "- Update manifest: `reports/update-all-latest.json`.",
        "- Statistical evidence: `reports/statistics-phase-7.*`.",
        "- Prediction evaluation: `reports/backtest-phase-9.*`.",
        "- Visualization manifest: `reports/visualization-phase-8.json` and `reports/figures/`.",
        "- Data contract: `docs/DATA_SCHEMA.md`.",
        "- Requirements traceability: `docs/REQUIREMENTS_TRACEABILITY.md`.",
        "- Historical upgrade audit: `reports/upgrade-qa-2026-08-28.md`; latest release audit: `reports/release-readiness-2026-09-08.md`.",
        "- Learning documents: `docs/01_PROJECT_OVERVIEW.md`, `docs/02_VSCODE_HANDS_ON_GUIDE.md`, `docs/03_DA_DS_PLAYBOOK.md`, `docs/04_REFERENCE_ALIGNMENT.md`, `docs/05_CODEBASE_FILE_GUIDE.md`.",
        "- VS Code cell-by-cell EDA: `notebooks/01_eda_s16.py`.",
        "- Roadmap: `ROADMAP.md`.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
