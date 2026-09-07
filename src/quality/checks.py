"""SQLite-backed integrity checks and quality report generation."""

from __future__ import annotations

import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ProjectConfig
from ..storage.database import connect_database, initialize_database
from .cleaning import clean_dimension_values


def _check(name: str, table: str, passed: bool, affected_rows: int, details: str) -> dict[str, Any]:
    """Create one consistently shaped quality-result record."""

    return {"check_name": name, "table_name": table, "passed": bool(passed), "affected_rows": int(affected_rows), "details": details}


def run_quality_checks(config: ProjectConfig, apply_cleaning: bool = True) -> dict[str, Any]:
    """Run all 12 SQL integrity gates and persist a reproducible report."""

    database_path = initialize_database(config)
    run_at = datetime.now(timezone.utc).isoformat()
    with closing(connect_database(database_path)) as connection:
        cleaning = clean_dimension_values(connection, config) if apply_cleaning else {}
        checks: list[dict[str, Any]] = []

        out_of_scope = connection.execute(
            "SELECT COUNT(*) FROM games WHERE played_at IS NULL OR played_at < ?", (config.season_start_date,)
        ).fetchone()[0]
        checks.append(_check("season_scope_games", "games", out_of_scope == 0, out_of_scope, f"played_at must be >= {config.season_start_date}"))

        invalid_game_pairs = connection.execute(
            """SELECT COUNT(*) FROM games
               WHERE blue_team_id = red_team_id
                  OR winner_team_id IS NULL
                  OR winner_team_id NOT IN (blue_team_id, red_team_id)"""
        ).fetchone()[0]
        checks.append(_check("game_two_teams_and_winner", "games", invalid_game_pairs == 0, invalid_game_pairs, "each completed game needs two distinct teams and one winner"))

        bad_team_rows = connection.execute(
            """SELECT COUNT(*) FROM (
                 SELECT game_id FROM team_game_stats GROUP BY game_id HAVING COUNT(DISTINCT team_id) <> 2
               )"""
        ).fetchone()[0]
        checks.append(_check("team_stats_two_rows_per_game", "team_game_stats", bad_team_rows == 0, bad_team_rows, "each game must have exactly two team stat rows"))

        bad_player_rows = connection.execute(
            """SELECT COUNT(*) FROM (
                 SELECT game_id,team_id FROM player_game_stats GROUP BY game_id,team_id HAVING COUNT(DISTINCT player_id) <> 5
               )"""
        ).fetchone()[0]
        checks.append(_check("starting_lineup_five_per_team", "player_game_stats", bad_player_rows == 0, bad_player_rows, "each team in a completed game must have exactly five player rows"))

        bad_current_rosters = connection.execute(
            """SELECT COUNT(*) FROM (
                 SELECT r.team_id FROM roster_periods r JOIN teams t ON t.team_id=r.team_id
                 WHERE t.is_lck_primary=1 AND r.is_primary=1
                   AND r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2
                                    WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)
                 GROUP BY r.team_id HAVING COUNT(DISTINCT r.player_id) <> 5
               )"""
        ).fetchone()[0]
        checks.append(_check("current_roster_five_players", "roster_periods", bad_current_rosters == 0, bad_current_rosters, "each tracked current roster must expose five starters"))

        invalid_numeric = connection.execute(
            """SELECT COUNT(*) FROM player_game_stats
               WHERE kills < 0 OR deaths < 0 OR assists < 0 OR cs < 0 OR kda < 0"""
        ).fetchone()[0]
        checks.append(_check("player_numeric_ranges", "player_game_stats", invalid_numeric == 0, invalid_numeric, "kills/deaths/assists/cs/kda cannot be negative"))

        invalid_team_economy = connection.execute(
            """SELECT COUNT(*) FROM team_game_stats
               WHERE (gpm IS NOT NULL AND (gpm <= 0 OR gpm > 4000))
                  OR (gdm IS NOT NULL AND ABS(gdm) > 2000)"""
        ).fetchone()[0]
        checks.append(
            _check(
                "team_economy_metric_ranges",
                "team_game_stats",
                invalid_team_economy == 0,
                invalid_team_economy,
                "GPM is positive and GDM is stored in gold per minute, not total gold difference",
            )
        )

        excluded_team_rows = connection.execute(
            """SELECT COUNT(*) FROM teams
               WHERE is_lck_primary=1 AND (is_academy=1
                  OR lower(canonical_name) LIKE '%challenger%'
                  OR lower(canonical_name) LIKE '%academy%'
                  OR lower(canonical_name) LIKE '%youth%')"""
        ).fetchone()[0]
        checks.append(_check("academy_challenger_exclusion", "teams", excluded_team_rows == 0, excluded_team_rows, "primary LCK dataset must not contain Academy/Challengers teams; external opponents may be retained as non-primary dimensions"))

        unknown_roles = connection.execute(
            "SELECT COUNT(*) FROM players WHERE primary_role IS NOT NULL AND primary_role NOT IN ('TOP','JUNGLE','MID','BOT','SUPPORT')"
        ).fetchone()[0]
        checks.append(_check("role_domain", "players", unknown_roles == 0, unknown_roles, "roles normalized to TOP/JUNGLE/MID/BOT/SUPPORT"))

        invalid_timeline = connection.execute(
            """SELECT COUNT(*) FROM timeline_events
               WHERE minute < 0 OR second < 0 OR second > 59
                  OR side NOT IN ('blue','red')"""
        ).fetchone()[0]
        checks.append(_check("timeline_event_ranges", "timeline_events", invalid_timeline == 0, invalid_timeline, "timeline timestamps use non-negative minutes and seconds in [0,59]"))

        duplicate_draft_actions = connection.execute(
            """SELECT COUNT(*) FROM (
                 SELECT game_id,side,action_type,champion_id
                 FROM drafts
                 GROUP BY game_id,side,action_type,champion_id
                 HAVING COUNT(*) > 1
               )"""
        ).fetchone()[0]
        checks.append(
            _check(
                "draft_actions_are_unique",
                "drafts",
                duplicate_draft_actions == 0,
                duplicate_draft_actions,
                "one champion can appear at most once per side/action type on a game summary",
            )
        )

        invalid_draft_counts = connection.execute(
            """SELECT COUNT(*) FROM (
                 SELECT game_id,
                        SUM(CASE WHEN action_type='pick' THEN 1 ELSE 0 END) picks,
                        SUM(CASE WHEN action_type='ban' THEN 1 ELSE 0 END) bans
                 FROM drafts GROUP BY game_id
                 HAVING picks <> 10 OR bans <> 10
               )"""
        ).fetchone()[0]
        checks.append(
            _check(
                "draft_ten_picks_ten_bans",
                "drafts",
                invalid_draft_counts == 0,
                invalid_draft_counts,
                "a parsed completed draft contains ten picks and ten bans",
            )
        )

        for item in checks:
            connection.execute(
                "INSERT INTO data_quality_results(check_name,table_name,run_at,passed,affected_rows,details) VALUES (?,?,?,?,?,?)",
                (item["check_name"], item["table_name"], run_at, int(item["passed"]), item["affected_rows"], item["details"]),
            )
        connection.commit()

    report = {
        "phase": "Phase 4 — Cleaning and data quality",
        "run_at": run_at,
        "season": config.season,
        "season_start_date": config.season_start_date,
        # Reports are committed to GitHub, so keep paths portable and avoid
        # leaking a contributor's absolute Windows user directory.
        "database": database_path.relative_to(config.root).as_posix(),
        "cleaning": cleaning,
        "checks": checks,
        "status": "passed" if all(item["passed"] for item in checks) else "failed",
    }
    report_path = config.root / "reports" / "data-quality-phase-4.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (config.root / "reports" / "data-quality-phase-4.md").write_text(render_quality_markdown(report), encoding="utf-8")
    return report


def render_quality_markdown(report: dict[str, Any]) -> str:
    """Render machine-readable quality results as a presentation-ready table."""

    lines = [
        "# Phase 4 Data Quality Report",
        "",
        f"- Status: **{report['status']}**",
        f"- Run at: `{report['run_at']}`",
        f"- Season: `{report['season']}` from `{report['season_start_date']}`",
        "",
        "## Cleaning",
        "",
        f"`{json.dumps(report['cleaning'], ensure_ascii=False)}`",
        "",
        "## Checks",
        "",
        "| Check | Table | Pass | Affected rows | Details |",
        "|---|---|:---:|---:|---|",
    ]
    for item in report["checks"]:
        lines.append(f"| {item['check_name']} | {item['table_name']} | {'✅' if item['passed'] else '❌'} | {item['affected_rows']} | {item['details']} |")
    return "\n".join(lines) + "\n"
