"""Dependency-light EDA metrics built directly from the SQLite facts.

The functions intentionally use the Python standard library so the pipeline can
still produce auditable CSV/JSON outputs when NumPy/Pandas wheels are not
available for the local MSYS Python. Pandas/Seaborn can consume these outputs in
the next notebook/UI phase.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from ..config import ProjectConfig
from ..storage.database import connect_database, initialize_database


def _mean(values: Iterable[float | int | None]) -> float | None:
    """Compute a nullable mean without replacing missing source values."""

    numbers = [float(value) for value in values if value is not None]
    return sum(numbers) / len(numbers) if numbers else None


def team_summary(connection: Any) -> list[dict[str, Any]]:
    """Create one descriptive summary row per primary LCK team."""

    rows = connection.execute(
        """SELECT t.team_id,t.canonical_name,
                  COUNT(DISTINCT s.game_id) AS games,
                  SUM(s.win) AS wins,
                  AVG(s.kills) AS avg_kills,
                  AVG(s.deaths) AS avg_deaths,
                  AVG(s.gpm) AS avg_gpm,
                  AVG(s.gdm) AS avg_gdm,
                  AVG(s.dpm) AS avg_dpm,
                  AVG(s.csm) AS avg_csm,
                  AVG(s.gd15) AS avg_gd15,
                  AVG(s.csd15) AS avg_csd15,
                  AVG(s.td15) AS avg_td15,
                  AVG(s.dra15) AS avg_dra15,
                  AVG(s.towers) AS avg_towers,
                  AVG(s.dragons) AS avg_dragons,
                  AVG(s.nashors) AS avg_nashors,
                  AVG(s.first_blood) AS first_blood_rate,
                  AVG(s.first_tower) AS first_tower_rate
           FROM team_game_stats s JOIN teams t ON t.team_id=s.team_id
           WHERE t.is_lck_primary=1
           GROUP BY t.team_id,t.canonical_name ORDER BY wins DESC, games DESC, t.canonical_name"""
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["wins"] = int(item["wins"] or 0)
        item["losses"] = int(item["games"] or 0) - item["wins"]
        item["win_rate"] = item["wins"] / item["games"] if item["games"] else None
        result.append(item)
    return result


def player_summary(connection: Any) -> list[dict[str, Any]]:
    """Create one role-aware summary row per current starting player."""

    rows = connection.execute(
        """SELECT p.player_id,p.canonical_name,p.primary_role,
                  COUNT(DISTINCT s.game_id) AS games,
                  AVG(s.kills) AS avg_kills,
                  AVG(s.deaths) AS avg_deaths,
                  AVG(s.assists) AS avg_assists,
                  AVG(s.kda) AS avg_kda,
                  AVG(s.cs) AS avg_cs,
                  AVG(s.csm) AS avg_csm,
                  AVG(s.dpm) AS avg_dpm,
                  AVG(s.gold_share) AS avg_gold_share,
                  AVG(s.damage_share) AS avg_damage_share
           FROM player_game_stats s JOIN players p ON p.player_id=s.player_id
           JOIN teams t ON t.team_id=s.team_id
           JOIN roster_periods r ON r.team_id=s.team_id AND r.player_id=s.player_id AND r.is_primary=1
           WHERE t.is_lck_primary=1
             AND r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2
                              WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)
           GROUP BY p.player_id,p.canonical_name,p.primary_role ORDER BY avg_kda DESC, games DESC"""
    ).fetchall()
    return [dict(row) for row in rows]


def champion_pool(connection: Any, team_id: int | None = None, player_id: str | None = None) -> list[dict[str, Any]]:
    """Aggregate champion usage with denominators and a small-sample warning."""

    clauses = ["s.champion_id IS NOT NULL", "t.is_lck_primary=1", "r.is_primary=1",
               "r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2 WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)"]
    params: list[Any] = []
    if team_id is not None:
        clauses.append("s.team_id=?")
        params.append(team_id)
    if player_id is not None:
        clauses.append("s.player_id=?")
        params.append(player_id)
    where = " AND ".join(clauses)
    rows = connection.execute(
        f"""SELECT s.champion_id,c.champion_name,COUNT(*) games,
                   SUM(CASE WHEN g.winner_team_id=s.team_id THEN 1 ELSE 0 END) wins,
                   AVG(s.kda) avg_kda
            FROM player_game_stats s JOIN players p ON p.player_id=s.player_id
            JOIN teams t ON t.team_id=s.team_id
            JOIN roster_periods r ON r.team_id=s.team_id AND r.player_id=s.player_id
            JOIN champions c ON c.champion_id=s.champion_id
            JOIN games g ON g.game_id=s.game_id
            WHERE {where}
            GROUP BY s.champion_id,c.champion_name
            ORDER BY games DESC,wins DESC,c.champion_name""",
        tuple(params),
    ).fetchall()
    total = sum(int(row["games"] or 0) for row in rows)
    result = []
    for row in rows:
        item = dict(row)
        item["win_rate"] = item["wins"] / item["games"] if item["games"] else None
        item["pick_rate"] = item["games"] / total if total else None
        item["small_sample_warning"] = item["games"] < 5
        result.append(item)
    return result


def head_to_head(connection: Any, team_a_id: int, team_b_id: int) -> list[dict[str, Any]]:
    """Return every S16 game between two teams, not only an aggregate rate."""

    rows = connection.execute(
        """SELECT g.game_id,g.played_at,g.game_number,g.patch,g.winner_team_id,
                  s.series_id,t.tournament_name,
                  CASE WHEN g.winner_team_id=? THEN 1 ELSE 0 END team_a_win
           FROM games g
           LEFT JOIN series s ON s.series_id=g.series_id
           LEFT JOIN tournaments t ON t.tournament_id=s.tournament_id
           WHERE ((g.blue_team_id=? AND g.red_team_id=?) OR (g.blue_team_id=? AND g.red_team_id=?))
           ORDER BY g.played_at,g.game_id""",
        (team_a_id, team_a_id, team_b_id, team_b_id, team_a_id),
    ).fetchall()
    return [dict(row) for row in rows]


def team_side_summary(connection: Any) -> list[dict[str, Any]]:
    """Split team performance by blue/red side with game denominators."""

    rows = connection.execute(
        """SELECT s.team_id,side,COUNT(*) games,SUM(win) wins,AVG(kills) avg_kills,
                  AVG(gpm) avg_gpm,AVG(gdm) avg_gdm,AVG(towers) avg_towers,
                  AVG(dragons) avg_dragons,AVG(nashors) avg_nashors,
                  AVG(first_tower) first_tower_rate
           FROM team_game_stats s JOIN teams t ON t.team_id=s.team_id
           WHERE t.is_lck_primary=1
           GROUP BY s.team_id,side ORDER BY s.team_id,side"""
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["win_rate"] = item["wins"] / item["games"] if item["games"] else None
        result.append(item)
    return result


def objective_timing_summary(connection: Any) -> list[dict[str, Any]]:
    """Summarize objective milestones from the Gol.gg embedded timeline.

    The source exposes milestone timestamps (first blood/tower, dragon, herald,
    voidgrubs and Nashor).  We preserve the event-level facts and only derive
    transparent per-team counts and mean elapsed seconds.
    """

    rows = connection.execute(
        """WITH owned AS (
               SELECT CASE WHEN te.side='blue' THEN g.blue_team_id ELSE g.red_team_id END AS team_id,
                      te.objective, te.event_type, te.minute * 60 + te.second AS elapsed_seconds
               FROM timeline_events te JOIN games g ON g.game_id=te.game_id
           )
           SELECT o.team_id,t.canonical_name,o.objective,o.event_type,
                  COUNT(*) AS events, AVG(o.elapsed_seconds) AS avg_elapsed_seconds,
                  MIN(o.elapsed_seconds) AS first_elapsed_seconds,
                  MAX(o.elapsed_seconds) AS last_elapsed_seconds
           FROM owned o JOIN teams t ON t.team_id=o.team_id
           WHERE t.is_lck_primary=1
           GROUP BY o.team_id,t.canonical_name,o.objective,o.event_type
           ORDER BY o.team_id,o.objective"""
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for key in ("avg_elapsed_seconds", "first_elapsed_seconds", "last_elapsed_seconds"):
            if item[key] is not None:
                item[key] = round(float(item[key]), 2)
        result.append(item)
    return result


def compare_players(connection: Any, player_a_id: str, player_b_id: str) -> dict[str, Any]:
    """Compare peers and explicitly mark cross-role comparisons."""

    starter_rows = connection.execute("SELECT player_id,is_current_starter FROM players WHERE player_id IN (?,?)", (player_a_id, player_b_id)).fetchall()
    starter_map = {str(row["player_id"]): bool(row["is_current_starter"]) for row in starter_rows}
    if not starter_map.get(str(player_a_id), False) or not starter_map.get(str(player_b_id), False):
        raise ValueError("Player comparison is restricted to the tracked current starting five")
    summaries = {row["player_id"]: row for row in player_summary(connection)}
    left, right = summaries.get(player_a_id), summaries.get(player_b_id)
    if left is None or right is None:
        raise ValueError("Both players need S16 game data")
    same_role = left.get("primary_role") == right.get("primary_role")
    metrics = ("games", "avg_kda", "avg_cs", "avg_csm", "avg_dpm", "avg_gold_share", "avg_damage_share")
    delta = {metric: (left.get(metric) - right.get(metric)) if left.get(metric) is not None and right.get(metric) is not None else None for metric in metrics}
    return {
        "player_a": left,
        "player_b": right,
        "same_role": same_role,
        "comparison_mode": "raw_peer" if same_role else "role_adjusted_required",
        "delta_player_a_minus_player_b": delta,
        "warning": None if same_role else "Different roles: raw metric deltas are descriptive only; use role-adjusted percentile before ranking.",
    }


def rolling_form(connection: Any, windows: tuple[int, ...] = (5, 10)) -> list[dict[str, Any]]:
    """Calculate trailing win rate using only games up to each row."""

    rows = connection.execute(
        """SELECT s.team_id,t.canonical_name,s.game_id,g.played_at,s.win
           FROM team_game_stats s JOIN teams t ON t.team_id=s.team_id
           JOIN games g ON g.game_id=s.game_id
           WHERE t.is_lck_primary=1
           ORDER BY s.team_id,g.played_at,g.game_id"""
    ).fetchall()
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["team_id"]].append(dict(row))
    output: list[dict[str, Any]] = []
    for team_rows in grouped.values():
        for index, row in enumerate(team_rows):
            item = dict(row)
            for window in windows:
                sample = team_rows[max(0, index - window + 1) : index + 1]
                item[f"rolling_{window}_games"] = len(sample)
                item[f"rolling_{window}_win_rate"] = _mean(sample_row["win"] for sample_row in sample)
            output.append(item)
    return output


def compare_teams(connection: Any, team_a_id: int, team_b_id: int) -> dict[str, Any]:
    """Align two team summaries feature-by-feature for a comparison table."""

    summaries = {row["team_id"]: row for row in team_summary(connection)}
    left = summaries.get(team_a_id)
    right = summaries.get(team_b_id)
    if left is None or right is None:
        raise ValueError(f"Both teams need data: {team_a_id}, {team_b_id}")
    metrics = ("games", "win_rate", "avg_kills", "avg_deaths", "avg_gpm", "avg_gdm", "avg_dpm", "avg_csd15", "avg_gd15", "avg_towers", "avg_dragons", "avg_nashors", "first_blood_rate", "first_tower_rate")
    delta = {metric: (left.get(metric) - right.get(metric)) if left.get(metric) is not None and right.get(metric) is not None else None for metric in metrics}
    return {"team_a": left, "team_b": right, "delta_team_a_minus_team_b": delta}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Persist an auditable intermediate table with stable UTF-8 encoding."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_eda_report(config: ProjectConfig) -> dict[str, Any]:
    """Run dependency-light EDA and write its tables plus evidence report."""

    database_path = initialize_database(config)
    with closing(connect_database(database_path)) as connection:
        teams = team_summary(connection)
        players = player_summary(connection)
        rolling = rolling_form(connection)
        champions = champion_pool(connection)
        sides = team_side_summary(connection)
        objective_timing = objective_timing_summary(connection)
    output_dir = config.processed_data_path
    _write_csv(output_dir / "team_summary.csv", teams)
    _write_csv(output_dir / "player_summary.csv", players)
    _write_csv(output_dir / "rolling_form.csv", rolling)
    _write_csv(output_dir / "champion_pool.csv", champions)
    _write_csv(output_dir / "team_side_summary.csv", sides)
    _write_csv(output_dir / "objective_timing.csv", objective_timing)
    report = {
        "phase": "Phase 5 — EDA and feature engineering",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "season": config.season,
        "database": database_path.relative_to(config.root).as_posix(),
        "team_rows": len(teams),
        "player_rows": len(players),
        "rolling_rows": len(rolling),
        # Persist repository-relative paths so reports work after cloning and
        # do not expose the local Windows account name.
        "outputs": [
            (output_dir / filename).relative_to(config.root).as_posix()
            for filename in (
                "team_summary.csv",
                "player_summary.csv",
                "rolling_form.csv",
                "champion_pool.csv",
                "team_side_summary.csv",
                "objective_timing.csv",
            )
        ],
        "champion_rows": len(champions),
        "side_rows": len(sides),
        "objective_timing_rows": len(objective_timing),
        "notes": [
            "Metrics include sample size (games) and leave unavailable source fields as null.",
            "Champion win rates include game denominators and a small-sample warning.",
            "Interpret the refreshed S16 snapshot with its recorded data cutoff; continue daily incremental updates while the season is active.",
        ],
    }
    (config.root / "reports" / "eda-phase-5.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (config.root / "reports" / "eda-phase-5.md").write_text(render_eda_markdown(report, teams, players), encoding="utf-8")
    return report


def render_eda_markdown(report: dict[str, Any], teams: list[dict[str, Any]], players: list[dict[str, Any]]) -> str:
    """Turn EDA dictionaries into a human-readable Markdown handoff."""

    lines = [
        "# Phase 5 EDA Report",
        "",
        f"- Run at: `{report['run_at']}`",
        f"- Team rows: `{report['team_rows']}`",
        f"- Player rows: `{report['player_rows']}`",
        f"- Champion pool rows: `{report['champion_rows']}`; side rows: `{report['side_rows']}`",
        "",
        "## Team overview",
        "",
        "| Team | Games | Wins | Losses | Win rate | Avg kills | Avg deaths |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in teams:
        rate = f"{row['win_rate']:.1%}" if row.get("win_rate") is not None else "—"
        avg_kills = f"{row['avg_kills']:.2f}" if row.get("avg_kills") is not None else "—"
        avg_deaths = f"{row['avg_deaths']:.2f}" if row.get("avg_deaths") is not None else "—"
        lines.append(f"| {row['canonical_name']} | {row['games']} | {row['wins']} | {row['losses']} | {rate} | {avg_kills} | {avg_deaths} |")
    lines.extend(["", "## Player overview", "", "| Player | Role | Games | Avg KDA | Avg CS |", "|---|---|---:|---:|---:|"])
    for row in players:
        avg_kda = f"{row['avg_kda']:.2f}" if row.get("avg_kda") is not None else "—"
        avg_cs = f"{row['avg_cs']:.2f}" if row.get("avg_cs") is not None else "—"
        lines.append(f"| {row['canonical_name']} | {row.get('primary_role') or '—'} | {row['games']} | {avg_kda} | {avg_cs} |")
    lines.extend(["", "## Caveat", "", *[f"- {note}" for note in report["notes"]]])
    return "\n".join(lines) + "\n"
