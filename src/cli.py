"""Command-line entry point for the project foundation."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Sequence

from .config import DEFAULT_CONFIG_PATH, ensure_runtime_directories, load_config
from .logging_config import configure_logging
from .storage.database import initialize_database, schema_summary


LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Define every beginner-facing CLI command and its validated arguments."""

    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="LoL Pro Analytics S16 foundation CLI.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to project JSON configuration.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("health", help="Validate configuration and runtime directories.")
    subparsers.add_parser("show-config", help="Print the validated configuration summary.")
    subparsers.add_parser("init-runtime", help="Create local runtime directories only.")
    subparsers.add_parser("freshness", help="Show whether the latest successful update is within the configured freshness window.")
    subparsers.add_parser("source-audit", help="Run the T1/HLE Gol.gg source audit prototype.")
    subparsers.add_parser("db-init", help="Create or update the local SQLite schema idempotently.")
    update_game = subparsers.add_parser("update-game", help="Fetch and upsert one Gol.gg game-level page.")
    update_game.add_argument("--game-id", required=True, help="Gol.gg numeric game ID, for example 81863.")
    update_team = subparsers.add_parser("update-team", help="Discover and incrementally update one team's 2026 games.")
    update_team.add_argument("--team-id", required=True, type=int, help="Gol.gg team ID, for example 2809 for T1.")
    update_team.add_argument("--max-games", type=int, default=5, help="Maximum game pages; use 0 for all candidates.")
    update_team.add_argument("--dry-run", action="store_true", help="Only inspect candidate URLs; do not fetch game pages.")
    update_team.add_argument("--force", action="store_true", help="Ignore today's raw cache for requested pages.")
    update_team.add_argument("--include-fullstats", action="store_true", help="Also fetch/parse each game's All stats page.")
    update_all = subparsers.add_parser("update-all", help="Run controlled incremental updates for all configured primary LCK teams.")
    update_all.add_argument("--max-games-per-team", type=int, default=1, help="Game pages per team; 0 means all candidates.")
    update_all.add_argument("--dry-run", action="store_true", help="Resolve teams and count candidates without fetching game pages.")
    update_all.add_argument("--force", action="store_true", help="Ignore today's raw cache.")
    update_all.add_argument("--include-fullstats", action="store_true", help="Also fetch/parse each selected game's All stats page.")
    schedule = subparsers.add_parser("update-schedule", help="Fetch and normalize future fixtures from the supplemental schedule source.")
    schedule.add_argument("--source-url", default=None)
    schedule.add_argument("--force", action="store_true")
    quality = subparsers.add_parser("quality-check", help="Clean dimensions and run SQLite data-quality checks.")
    quality.add_argument("--skip-cleaning", action="store_true", help="Run checks without changing normalized dimension text.")
    subparsers.add_parser("eda", help="Generate dependency-light EDA CSVs and report from SQLite.")
    subparsers.add_parser("pandas-eda", help="Run the beginner-friendly Pandas/NumPy EDA workflow.")
    statistics = subparsers.add_parser(
        "statistics-report",
        help="Generate Wilson intervals and optional introductory inferential tests.",
    )
    statistics.add_argument("--team-a-id", type=int, default=None, help="Optional first team for pair tests.")
    statistics.add_argument("--team-b-id", type=int, default=None, help="Optional second team; supply with --team-a-id.")
    visualize = subparsers.add_parser("visualize", help="Generate question-driven static figures (Matplotlib/Seaborn or SVG fallback).")
    visualize.add_argument("--team-a-id", type=int, default=None, help="Optional first team for matchup-specific figures.")
    visualize.add_argument("--team-b-id", type=int, default=None, help="Optional second team; supply together with --team-a-id.")
    subparsers.add_parser("backtest", help="Run leakage-safe walk-forward evaluation of the S16 baseline.")
    predict = subparsers.add_parser("predict-matchup", help="Predict a team matchup with the transparent S16 baseline.")
    predict.add_argument("--team-a-id", required=True, type=int)
    predict.add_argument("--team-b-id", required=True, type=int)
    predict.add_argument("--fixture-id", default=None)
    team_report = subparsers.add_parser("team-report", help="Print a reusable one-team S16 report.")
    team_report.add_argument("--team-id", required=True, type=int)
    player_report = subparsers.add_parser("player-report", help="Print a reusable one-player S16 report.")
    player_report.add_argument("--player-id", required=True)
    player_compare = subparsers.add_parser("player-compare", help="Compare two S16 players with role warning.")
    player_compare.add_argument("--player-a-id", required=True)
    player_compare.add_argument("--player-b-id", required=True)
    h2h_report = subparsers.add_parser("h2h-report", help="Print team comparison, H2H and role matchup evidence.")
    h2h_report.add_argument("--team-a-id", required=True, type=int)
    h2h_report.add_argument("--team-b-id", required=True, type=int)
    subparsers.add_parser("final-report", help="Generate final project handoff report and runbook summary.")
    return parser


def run_health(config_path: str) -> int:
    """Validate configuration/runtime paths and return a shell exit code."""

    config = load_config(config_path)
    ensure_runtime_directories(config)
    LOGGER.info("Foundation health check passed for %s", config.project_name)
    print(json.dumps({"status": "ok", "season": config.season, "teams": len(config.tracked_lck_teams)}))
    return 0


def run_show_config(config_path: str) -> int:
    """Print the resolved project scope without exposing secret values."""

    config = load_config(config_path)
    print(
        json.dumps(
            {
                "project_name": config.project_name,
                "season": config.season,
                "season_start_date": config.season_start_date,
                "timezone": config.timezone,
                "tracked_team_count": len(config.tracked_lck_teams),
                "statistics_source": config.sources["statistics"],
                "schedule_source": config.sources["schedule"],
                "database_path": str(config.database_path),
            },
            indent=2,
        )
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse one CLI request, dispatch its phase, and return success/failure."""

    # Windows PowerShell 5.1 may expose a CP1252 stdout.  Reports contain
    # Vietnamese labels, so force UTF-8 when the real terminal supports it.
    # StringIO/captured test streams do not implement ``reconfigure`` and are
    # intentionally left untouched.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config)
    configure_logging(config.logs_path)

    if args.command == "health":
        return run_health(args.config)
    if args.command == "show-config":
        return run_show_config(args.config)
    if args.command == "init-runtime":
        ensure_runtime_directories(config)
        LOGGER.info("Runtime directories initialized")
        return 0
    if args.command == "freshness":
        database_path = initialize_database(config)
        from contextlib import closing
        from .storage.database import connect_database

        with closing(connect_database(database_path)) as connection:
            latest = connection.execute("SELECT finished_at FROM update_runs WHERE status='success' AND finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1").fetchone()
        finished_at = latest[0] if latest else None
        age_hours = None
        if finished_at:
            age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(finished_at)).total_seconds() / 3600
        print(json.dumps({"status": "fresh" if age_hours is not None and age_hours <= config.update_policy.max_age_hours else "stale_or_missing", "last_successful_update": finished_at, "age_hours": age_hours, "max_age_hours": config.update_policy.max_age_hours}, ensure_ascii=False))
        return 0
    if args.command == "source-audit":
        from .collection.source_audit import run_source_audit

        report = run_source_audit()
        print(json.dumps({"status": "ok", "report": "reports/source-audit-phase-2.json", "teams": [target["team"] for target in report["targets"]]}))
        return 0
    if args.command == "db-init":
        database_path = initialize_database(config)
        print(json.dumps({"status": "ok", "database": str(database_path), **schema_summary(database_path)}, ensure_ascii=False))
        return 0
    if args.command == "update-game":
        from .collection.game_parsers import parse_game_page
        from .collection.http_client import CachedHttpClient, read_raw_html
        from .storage.database import upsert_parsed_game

        url = f"https://gol.gg/game/stats/{args.game_id}/page-game/"
        client = CachedHttpClient(config)
        fetched = client.fetch(url, "game_stats", str(args.game_id))
        parsed = parse_game_page(read_raw_html(fetched), str(args.game_id))
        if parsed.played_at is None or parsed.played_at < config.season_start_date:
            raise RuntimeError(
                f"Game {args.game_id} is outside the S16 calendar scope or has no authoritative date: {parsed.played_at!r}"
            )
        counts = upsert_parsed_game(config, parsed, fetched)
        print(json.dumps({"status": "ok", "game_id": args.game_id, "database": str(config.database_path), "upserted": counts}, ensure_ascii=False))
        return 0
    if args.command == "update-team":
        from .collection.updater import run_team_update

        result = run_team_update(config, args.team_id, args.max_games, args.dry_run, args.force, args.include_fullstats)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("status", "success") != "failed" else 1
    if args.command == "update-all":
        from .collection.updater import run_all_teams_update

        result = run_all_teams_update(config, args.max_games_per_team, args.dry_run, args.force, args.include_fullstats)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] in {"ok", "partial"} else 1
    if args.command == "update-schedule":
        from .collection.schedule import run_schedule_update

        result = run_schedule_update(config, args.source_url, args.force)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.command == "quality-check":
        from .quality.checks import run_quality_checks

        report = run_quality_checks(config, apply_cleaning=not args.skip_cleaning)
        print(json.dumps({"status": report["status"], "report": "reports/data-quality-phase-4.json", "checks": len(report["checks"])}, ensure_ascii=False))
        return 0 if report["status"] == "passed" else 1
    if args.command == "eda":
        from .analysis.metrics import run_eda_report

        report = run_eda_report(config)
        print(json.dumps({"status": "ok", "report": "reports/eda-phase-5.json", "team_rows": report["team_rows"], "player_rows": report["player_rows"]}, ensure_ascii=False))
        return 0
    if args.command == "pandas-eda":
        from .analysis.pandas_eda import run_pandas_eda

        report = run_pandas_eda(config)
        print(json.dumps({"status": "ok", "report": "reports/pandas-eda-phase.json", "outputs": len(report["outputs"])}, ensure_ascii=False))
        return 0
    if args.command == "statistics-report":
        from .analysis.statistics import run_statistics_report

        if (args.team_a_id is None) != (args.team_b_id is None):
            parser.error("statistics-report requires both --team-a-id and --team-b-id, or neither")
        report = run_statistics_report(config, team_a_id=args.team_a_id, team_b_id=args.team_b_id)
        print(json.dumps(report, ensure_ascii=False))
        return 0
    if args.command == "visualize":
        from .analysis.visualizations import generate_visualizations

        if (args.team_a_id is None) != (args.team_b_id is None):
            parser.error("visualize requires both --team-a-id and --team-b-id, or neither")
        report = generate_visualizations(config, team_a_id=args.team_a_id, team_b_id=args.team_b_id)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["status"] in {"ok", "fallback", "skipped"} else 1
    if args.command == "backtest":
        from .modeling.backtest import run_backtest

        report = run_backtest(config)
        print(json.dumps(report, ensure_ascii=False))
        return 0
    if args.command == "predict-matchup":
        from .modeling.predictor import predict_matchup

        result = predict_matchup(config, args.team_a_id, args.team_b_id, args.fixture_id)
        print(json.dumps({"status": result["status"], "predicted_winner_team_id": result["predicted_winner_team_id"], "probability_team_a": result["probability_team_a"], "probability_team_b": result["probability_team_b"], "report": result["report_path"]}, ensure_ascii=False))
        return 0
    if args.command == "team-report":
        from .analysis.reports import build_team_report

        print(json.dumps(build_team_report(config, args.team_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "player-report":
        from .analysis.reports import build_player_report

        print(json.dumps(build_player_report(config, args.player_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "player-compare":
        from .analysis.metrics import compare_players
        from contextlib import closing
        from .storage.database import connect_database

        with closing(connect_database(initialize_database(config))) as connection:
            report = compare_players(connection, args.player_a_id, args.player_b_id)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "h2h-report":
        from .analysis.reports import build_h2h_report

        print(json.dumps(build_h2h_report(config, args.team_a_id, args.team_b_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "final-report":
        from .reporting.final_report import generate_final_report

        report_path = generate_final_report(config)
        print(json.dumps({"status": "ok", "report": str(report_path), "runbook": "docs/RUNBOOK.md"}, ensure_ascii=False))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
