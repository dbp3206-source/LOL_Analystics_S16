from __future__ import annotations

import unittest
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import shutil
import importlib.util

from src.config import DEFAULT_CONFIG_PATH, load_config
from src.cli import main
from src.collection.parsers import parse_team_directory, parse_team_match_list, parse_team_summary
from src.collection.game_parsers import _draft_actions, parse_fullstats_page, parse_game_page
from src.collection.schedule import parse_schedule_page
from src.storage.database import gold_differential_per_minute, initialize_database, schema_summary, table_counts, upsert_parsed_game
from src.quality.cleaning import normalize_role, normalize_text
from src.modeling.predictor import predict_matchup


class FoundationTests(unittest.TestCase):
    def test_recent_form_chart_rows_use_only_current_and_past_games(self) -> None:
        """The dashboard rolling feature must be chronological and leakage-free."""

        from app.streamlit_app import _recent_form_chart_rows

        rows = [
            {"win": 1, "kills": 10, "deaths": 5},
            {"win": 0, "kills": 4, "deaths": 9},
            {"win": 1, "kills": 12, "deaths": 7},
        ]
        chart = _recent_form_chart_rows(rows, window=2)
        self.assertEqual([row["game_order"] for row in chart], [1, 2, 3])
        self.assertEqual([row["rolling_win_rate_5"] for row in chart], [1.0, 0.5, 0.5])
        self.assertEqual(chart[-1]["kills"], 12.0)

    FIXTURES = Path(__file__).parent / "fixtures"

    def test_config_is_locked_to_s16_and_ten_teams(self) -> None:
        config = load_config(DEFAULT_CONFIG_PATH)
        self.assertEqual(config.season, "S16")
        self.assertEqual(len(config.tracked_lck_teams), 10)

    def test_cli_health(self) -> None:
        self.assertEqual(main(["health"]), 0)

    def test_cli_help_without_error(self) -> None:
        self.assertEqual(main([]), 0)

    def test_team_directory_filters_are_explicit(self) -> None:
        html = (self.FIXTURES / "team_directory.html").read_text(encoding="utf-8")
        teams = parse_team_directory(html, "https://gol.gg/teams/")
        self.assertEqual([team.team_id for team in teams], [2809, 2805, 2825])
        self.assertFalse(teams[0].is_challenger_or_academy)
        self.assertTrue(teams[2].is_challenger_or_academy)
        self.assertTrue(teams[0].url.startswith("https://gol.gg/teams/team-stats/"))

    def test_team_summary_extracts_s16_labels(self) -> None:
        html = (self.FIXTURES / "team_stats.html").read_text(encoding="utf-8")
        summary = parse_team_summary(html)
        self.assertEqual(summary["team_name"], "T1")
        self.assertEqual(summary["season"], "S16")
        self.assertEqual(summary["summary"]["Region"], "KR")

    def test_match_parser_excludes_pre_2026_tournament(self) -> None:
        html = (self.FIXTURES / "team_matchlist.html").read_text(encoding="utf-8")
        matches = parse_team_match_list(html, date(2026, 1, 1), "https://gol.gg/teams/")
        self.assertEqual(len(matches), 2)
        self.assertTrue(matches[0].included_from_2026)
        self.assertFalse(matches[1].included_from_2026)
        self.assertEqual(matches[1].tournament_year, 2025)

    def test_match_parser_accepts_team_specific_result_header(self) -> None:
        html = (self.FIXTURES / "team_matchlist.html").read_text(encoding="utf-8")
        matches = parse_team_match_list(html.replace("T1 Result", "HLE Result"))
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].result, "WIN")

    def test_match_parser_quarantines_unknown_tournament_year(self) -> None:
        html = (self.FIXTURES / "team_matchlist.html").read_text(encoding="utf-8")
        matches = parse_team_match_list(html.replace("LCK 2026", "LCK"))
        self.assertFalse(matches[0].included_from_2026)
        self.assertIsNone(matches[0].tournament_year)

    def test_database_schema_is_idempotent_and_enforces_s16(self) -> None:
        config = load_config(DEFAULT_CONFIG_PATH)
        database_path = config.root / "data" / "test_phase3.db"
        try:
            first = initialize_database(config, database_path)
            self.assertEqual(first, database_path)
            initialize_database(config, database_path)
            summary = schema_summary(database_path)
            self.assertEqual(summary["schema_version"], 1)
            self.assertGreaterEqual(len(summary["tables"]), 17)
            connection = sqlite3.connect(database_path)
            try:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "INSERT INTO tournaments(tournament_id,tournament_name,season,tournament_type) VALUES ('bad','Bad','S15','unknown')"
                    )
            finally:
                connection.close()
        finally:
            if database_path.exists():
                database_path.unlink()

    def test_game_parser_extracts_metadata_and_player_stat(self) -> None:
        html = (self.FIXTURES / "game_page.html").read_text(encoding="utf-8")
        game = parse_game_page(html)
        self.assertEqual(game.game_id, "81863")
        self.assertEqual(game.played_at, "2026-08-23")
        self.assertEqual(game.patch, "16.16")
        self.assertEqual(game.duration_seconds, 1372)
        self.assertEqual(game.winner_team_id, 2805)
        self.assertEqual(len(game.player_stats), 2)
        self.assertEqual(game.player_stats[0].champion_name, "Kennen")
        self.assertEqual(game.game_number, 2)

    def test_timeline_parser_extracts_objective_milestones(self) -> None:
        from bs4 import BeautifulSoup
        from src.collection.game_parsers import _timeline_events

        html = (self.FIXTURES / "timeline.html").read_text(encoding="utf-8")
        events = _timeline_events(BeautifulSoup(html, "html.parser"))
        self.assertEqual(len(events), 3)
        self.assertEqual((events[0].minute, events[0].second, events[0].side, events[0].event_type), (1, 45, "red", "first_blood"))
        self.assertEqual((events[1].minute, events[1].second, events[1].side, events[1].objective), (16, 4, "blue", "herald"))
        self.assertEqual(events[2].objective, "nashor")

    def test_draft_parser_ignores_parent_layout_row(self) -> None:
        """The nested Gol.gg layout must not duplicate or relabel actions."""
        from bs4 import BeautifulSoup

        html = (self.FIXTURES / "draft_section.html").read_text(encoding="utf-8")
        container = BeautifulSoup(html, "html.parser").select_one("div.col-12")
        actions = _draft_actions(container, "blue")

        self.assertEqual(len(actions), 4)
        self.assertEqual([action.action_type for action in actions], ["ban", "ban", "pick", "pick"])
        self.assertEqual([action.champion_id for action in actions], ["1", "2", "3", "4"])

    def test_fullstats_parser_extracts_advanced_metrics(self) -> None:
        html = (self.FIXTURES / "fullstats.html").read_text(encoding="utf-8")
        stats = parse_fullstats_page(html)
        self.assertEqual(len(stats), 10)
        self.assertEqual(stats[0].dpm, 500.0)
        self.assertEqual(stats[3].gold_share, 0.24)
        self.assertEqual(stats[5].role, "TOP")

    def test_game_upsert_is_idempotent(self) -> None:
        config = load_config(DEFAULT_CONFIG_PATH)
        database_path = config.root / "data" / "test_game_upsert.db"
        try:
            html = (self.FIXTURES / "game_page.html").read_text(encoding="utf-8")
            game = parse_game_page(html)
            upsert_parsed_game(config, game, database_path=database_path)
            upsert_parsed_game(config, game, database_path=database_path)
            counts = table_counts(database_path)
            self.assertEqual(counts["games"], 1)
            self.assertEqual(counts["player_game_stats"], 2)
            self.assertEqual(counts["teams"], 2)
            connection = sqlite3.connect(database_path)
            try:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM team_game_stats WHERE deaths IS NOT NULL").fetchone()[0], 2)
            finally:
                connection.close()
        finally:
            if database_path.exists():
                database_path.unlink()

    def test_cleaning_normalizes_roles_and_whitespace(self) -> None:
        self.assertEqual(normalize_role(" adc "), "BOT")
        self.assertEqual(normalize_role("support"), "SUPPORT")
        self.assertEqual(normalize_text("  Hanwha   Life Esports "), "Hanwha Life Esports")

    def test_gdm_is_gold_differential_per_minute(self) -> None:
        """A 6,000 final gold lead in 30 minutes equals +200 GDM."""

        self.assertAlmostEqual(gold_differential_per_minute(60000, 54000, 1800), 200.0)
        self.assertAlmostEqual(gold_differential_per_minute(54000, 60000, 1800), -200.0)
        self.assertIsNone(gold_differential_per_minute(None, 60000, 1800))

    def test_prediction_baseline_is_explicit_about_small_sample(self) -> None:
        config = load_config(DEFAULT_CONFIG_PATH)
        result = predict_matchup(config, 2805, 2809, persist=False)
        self.assertIn(result["status"], {"insufficient_data", "baseline_ready"})
        self.assertAlmostEqual(result["probability_team_a"] + result["probability_team_b"], 1.0)
        self.assertIn("model_version", result)
        self.assertEqual(result["prediction_context"], "hypothetical")
        self.assertIsNone(result["report_path"])
        if result["status"] == "baseline_ready":
            self.assertIn("small_sample_warning", result)

    def test_prediction_rejects_unknown_official_fixture(self) -> None:
        config = load_config(DEFAULT_CONFIG_PATH)
        with self.assertRaisesRegex(ValueError, "Unknown fixture_id"):
            predict_matchup(config, 2805, 2809, fixture_id="not-a-real-fixture", persist=False)

    def test_official_prediction_uses_future_fixture_and_isolated_database(self) -> None:
        """Official mode validates fixture teams, freshness and temporal cutoff."""
        from src.storage.database import connect_database, initialize_database

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            config_path = root / "configs" / "project.json"
            shutil.copyfile(DEFAULT_CONFIG_PATH, config_path)
            config = load_config(config_path)
            initialize_database(config)

            now = datetime.now(timezone.utc)
            future = now + timedelta(days=2)
            with closing(connect_database(config.database_path)) as connection:
                connection.executemany(
                    "INSERT INTO teams(team_id,canonical_name,is_lck_primary) VALUES (?,?,1)",
                    [(2805, "Hanwha Life Esports"), (2809, "T1")],
                )
                connection.execute(
                    "INSERT INTO games(game_id,played_at,blue_team_id,red_team_id,winner_team_id) VALUES ('g1','2026-01-15',2805,2809,2805)"
                )
                connection.executemany(
                    """INSERT INTO team_game_stats(game_id,team_id,opponent_id,side,win,kills,deaths,gpm,gdm,first_tower)
                       VALUES ('g1',?,?,?,?,?,?,?,?,?)""",
                    [
                        (2805, 2809, "blue", 1, 15, 10, 1900, 500, 1),
                        (2809, 2805, "red", 0, 10, 15, 1800, -500, 0),
                    ],
                )
                connection.execute(
                    """INSERT INTO update_runs(run_id,started_at,finished_at,status)
                       VALUES ('fresh-test',?,?, 'success')""",
                    (now.isoformat(), now.isoformat()),
                )
                connection.execute(
                    """INSERT INTO schedules(fixture_id,scheduled_at_utc,team_a_id,team_b_id,best_of,status,source_url,collected_at)
                       VALUES ('future-fixture',?,2805,2809,3,'scheduled','https://example.test',?)""",
                    (future.isoformat(), now.isoformat()),
                )
                connection.commit()

            result = predict_matchup(config, 2805, 2809, fixture_id="future-fixture", persist=False)
            self.assertEqual(result["prediction_context"], "official_fixture")
            self.assertEqual(result["fixture_timestamp"], future.isoformat())
            self.assertEqual(result["data_cutoff"], "2026-01-15")
            self.assertEqual(result["data_freshness"]["status"], "fresh")

    def test_schedule_parser_normalizes_jsonld_timestamp(self) -> None:
        html = (self.FIXTURES / "schedule.html").read_text(encoding="utf-8")
        fixtures = parse_schedule_page(html, "https://example.test/schedule")
        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0].fixture_id, "fixture-1")
        self.assertEqual(fixtures[0].scheduled_at_utc, "2026-08-29T23:00:00+00:00")

    def test_schedule_parser_accepts_lolesports_api_payload(self) -> None:
        html = (self.FIXTURES / "schedule_api.json").read_text(encoding="utf-8")
        fixtures = parse_schedule_page(html, "https://esports-api.lolesports.com/schedule")
        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0].fixture_id, "api-fixture-1")
        self.assertEqual(fixtures[0].best_of, 3)

    def test_schedule_parser_accepts_leaguepedia_mediawiki_payload(self) -> None:
        html = (self.FIXTURES / "leaguepedia_api.json").read_text(encoding="utf-8")
        fixtures = parse_schedule_page(html, "https://lol.fandom.com/api.php")
        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0].team_a_name, "KT Rolster")
        self.assertEqual(fixtures[0].team_b_name, "HANJIN BRION")
        self.assertEqual(fixtures[0].scheduled_at_utc, "2026-08-26T08:00:00+00:00")

    def test_backtest_writes_leakage_safe_report_in_isolation(self) -> None:
        from src.modeling.backtest import run_backtest

        with tempfile.TemporaryDirectory() as directory:
            run_backtest(load_config(DEFAULT_CONFIG_PATH), output_root=Path(directory))
            report = Path(directory) / "reports" / "backtest-phase-9.json"
            self.assertTrue(report.exists())
            payload = __import__("json").loads(report.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["predictions"]), payload["games_available"])
            self.assertTrue(all(item["prior_training_examples"] >= 4 for item in payload["logistic_predictions"]))

    def test_entity_report_commands_cover_single_player(self) -> None:
        self.assertEqual(main(["player-report", "--player-id", "1328"]), 0)

    def test_dashboard_starter_query_returns_primary_five(self) -> None:
        """Smoke-test the SQL used by the Team overview dashboard."""
        from app.streamlit_app import _starter_rows

        rows = _starter_rows(2809)
        self.assertEqual(len(rows), 5)
        self.assertEqual(
            {row["primary_role"] for row in rows},
            {"TOP", "JUNGLE", "MID", "BOT", "SUPPORT"},
        )

    def test_visualization_command_emits_question_driven_artifacts(self) -> None:
        from src.analysis.visualizations import generate_visualizations

        with tempfile.TemporaryDirectory() as directory:
            result = generate_visualizations(load_config(DEFAULT_CONFIG_PATH), output_root=Path(directory))
            report_path = Path(directory) / "reports" / "visualization-phase-8.json"
            report = __import__("json").loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], report["status"])
            self.assertIn(report["status"], {"ok", "fallback"})
            self.assertGreaterEqual(len(report["figures"]), 8)

    @unittest.skipUnless(importlib.util.find_spec("pandas"), "Pandas is optional in the minimal scraper environment")
    def test_pandas_eda_writes_intermediate_tables_in_isolation(self) -> None:
        """The Colab-style EDA must expose auditable intermediate outputs."""
        from src.analysis.pandas_eda import run_pandas_eda

        with tempfile.TemporaryDirectory() as directory:
            report = run_pandas_eda(load_config(DEFAULT_CONFIG_PATH), output_root=Path(directory))
            self.assertEqual(len(report["inspections"]), 2)
            self.assertGreater(report["inspections"][0]["rows"], 0)
            self.assertEqual(report["inspections"][0]["duplicate_rows"], 0)
            self.assertEqual(len(report["outputs"]), 8)
            self.assertTrue((Path(directory) / "reports" / "pandas-eda-phase.json").exists())

    @unittest.skipUnless(importlib.util.find_spec("pandas"), "Pandas is optional in the minimal scraper environment")
    def test_scientific_visualization_tables_cover_ten_primary_teams(self) -> None:
        """Rich chart inputs must be complete before plotting libraries run."""

        from src.analysis.pandas_eda import load_analysis_frames
        from src.analysis.scientific_visualizations import TEAM_METRICS, _safe_zscore, _team_aggregate

        team_games, _ = load_analysis_frames(load_config(DEFAULT_CONFIG_PATH))
        team_stats = _team_aggregate(team_games)
        standardized = _safe_zscore(team_stats.set_index("team_name")[list(TEAM_METRICS)])

        self.assertEqual(len(team_stats), 10)
        self.assertEqual(standardized.shape, (10, len(TEAM_METRICS)))
        self.assertEqual(int(standardized.isna().sum().sum()), 0)

    def test_eda_notebook_has_explanatory_markdown_for_every_code_cell(self) -> None:
        """The VS Code notebook should teach the flow, not be a four-cell shell."""

        import json

        notebook_path = DEFAULT_CONFIG_PATH.parent.parent / "notebooks" / "01_eda_s16.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        markdown_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "markdown"]
        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]

        self.assertGreaterEqual(len(code_cells), 12)
        self.assertEqual(len(markdown_cells), len(code_cells))
        self.assertTrue(all(cell["source"] for cell in markdown_cells))

    def test_statistics_report_runs_without_optional_scientific_packages(self) -> None:
        """Wilson evidence must work even when SciPy/Statsmodels are absent."""

        from src.analysis.statistics import cohens_d, run_statistics_report

        # A pure-function check makes the effect-size formula easy to audit.
        self.assertAlmostEqual(cohens_d([1, 2, 3], [2, 3, 4]), -1.0)
        with tempfile.TemporaryDirectory() as directory:
            result = run_statistics_report(
                load_config(DEFAULT_CONFIG_PATH),
                team_a_id=2809,
                team_b_id=2805,
                output_root=Path(directory),
            )
            report_path = Path(result["report_path"])
            self.assertTrue(report_path.exists())
            self.assertEqual(result["team_rows"], 10)
            self.assertIn(result["inferential_status"], {"ok", "partial", "skipped"})
            payload = __import__("json").loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["teams"]), 10)
            self.assertEqual(payload["selected_pair_tests"]["team_a"]["team_id"], 2809)


if __name__ == "__main__":
    unittest.main()
