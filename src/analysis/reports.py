"""Reusable entity reports for CLI, notebooks and Streamlit."""

from __future__ import annotations

from contextlib import closing
from typing import Any

from ..storage.database import connect_database, initialize_database
from .metrics import champion_pool, compare_players, compare_teams, head_to_head, player_summary, team_side_summary, team_summary


def _role_matchups(connection: Any, team_a_id: int, team_b_id: int) -> list[dict[str, Any]]:
    """Align current starters by role before comparing personal metrics."""

    rows = connection.execute(
        """SELECT a.role,a.player_id player_a_id,pa.canonical_name player_a,
                  b.player_id player_b_id,pb.canonical_name player_b,
                  COUNT(*) games,AVG(a.kda) kda_a,AVG(b.kda) kda_b,
                  AVG(a.cs) cs_a,AVG(b.cs) cs_b,
                  SUM(CASE WHEN ga.winner_team_id=? THEN 1 ELSE 0 END) wins_a
           FROM player_game_stats a JOIN player_game_stats b ON a.game_id=b.game_id AND a.role=b.role
           JOIN players pa ON pa.player_id=a.player_id JOIN players pb ON pb.player_id=b.player_id
           JOIN games ga ON ga.game_id=a.game_id
           WHERE a.team_id=? AND b.team_id=? AND pa.is_current_starter=1 AND pb.is_current_starter=1
           GROUP BY a.role,a.player_id,pa.canonical_name,b.player_id,pb.canonical_name
           ORDER BY CASE a.role WHEN 'TOP' THEN 1 WHEN 'JUNGLE' THEN 2 WHEN 'MID' THEN 3 WHEN 'BOT' THEN 4 WHEN 'SUPPORT' THEN 5 ELSE 6 END, games DESC""",
        (team_a_id, team_a_id, team_b_id),
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["win_rate_a"] = item["wins_a"] / item["games"] if item["games"] else None
        result.append(item)
    return result


def build_team_report(config: Any, team_id: int) -> dict[str, Any]:
    """Assemble one-team summary, form, roster and champion evidence."""

    database_path = initialize_database(config)
    with closing(connect_database(database_path)) as connection:
        summaries = {row["team_id"]: row for row in team_summary(connection)}
        summary = summaries.get(team_id)
        if summary is None:
            raise ValueError(f"Team {team_id} has no S16 data")
        starters = [dict(row) for row in connection.execute("SELECT p.canonical_name,p.primary_role,r.valid_from,r.evidence_game_id FROM players p JOIN roster_periods r ON r.player_id=p.player_id WHERE r.team_id=? AND p.is_current_starter=1 ORDER BY p.primary_role", (team_id,))]
        sides = [row for row in team_side_summary(connection) if row["team_id"] == team_id]
        champions = champion_pool(connection, team_id=team_id)
    return {"team": summary, "starters": starters, "champion_pool": champions, "side_summary": sides}


def build_h2h_report(config: Any, team_a_id: int, team_b_id: int) -> dict[str, Any]:
    """Assemble team comparison, game-level H2H and same-role matchups."""

    database_path = initialize_database(config)
    with closing(connect_database(database_path)) as connection:
        report = compare_teams(connection, team_a_id, team_b_id)
        report["head_to_head"] = head_to_head(connection, team_a_id, team_b_id)
        report["role_matchups"] = _role_matchups(connection, team_a_id, team_b_id)
        report["champion_pool_team_a"] = champion_pool(connection, team_id=team_a_id)
        report["champion_pool_team_b"] = champion_pool(connection, team_id=team_b_id)
    return report


def build_player_report(config: Any, player_id: str) -> dict[str, Any]:
    """Return a standalone S16 profile for one current starter."""
    database_path = initialize_database(config)
    with closing(connect_database(database_path)) as connection:
        starter = connection.execute("SELECT is_current_starter FROM players WHERE player_id=?", (player_id,)).fetchone()
        if starter is None or not bool(starter[0]):
            raise ValueError("Player report is restricted to the tracked current starting five")
        summary = next((row for row in player_summary(connection) if str(row["player_id"]) == str(player_id)), None)
        if summary is None:
            raise ValueError(f"Player {player_id} has no S16 data")
        champions = champion_pool(connection, player_id=player_id)
    return {"player": summary, "is_current_starter": bool(starter[0]) if starter else False, "champion_pool": champions}
