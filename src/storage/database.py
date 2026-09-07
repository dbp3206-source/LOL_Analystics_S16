"""SQLite initialization helpers with an idempotent schema migration."""

from __future__ import annotations

import sqlite3
import re
from contextlib import closing
from pathlib import Path
from typing import Any

from ..config import ProjectConfig, ensure_runtime_directories


SCHEMA_VERSION = 1
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect_database(path: Path | str) -> sqlite3.Connection:
    """Open SQLite with named rows and foreign-key enforcement enabled."""

    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(config: ProjectConfig, database_path: Path | str | None = None) -> Path:
    """Create/update SQLite schema without deleting existing rows."""

    ensure_runtime_directories(config)
    database_path = Path(database_path) if database_path is not None else config.database_path
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with closing(connect_database(database_path)) as connection:
        connection.executescript(schema_sql)
        _ensure_schema_columns(connection)
        _repair_derived_team_economy(connection)
        _repair_team_scope(connection, config)
        _repair_current_starter_flags(connection)
        connection.execute(
            "INSERT OR IGNORE INTO schema_version(version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        connection.commit()
    return database_path


def _is_academy_name(name: str) -> bool:
    """Flag Academy/Challengers naming markers for scope enforcement."""

    normalized = name.casefold()
    return any(marker in normalized for marker in ("academy", "challenger", "youth", "esports academy"))


def _is_configured_primary(config: ProjectConfig, name: str) -> bool:
    """Match a source name against configured primary-team aliases."""

    normalized = name.casefold().strip()
    for item in config.tracked_lck_teams:
        candidates = [item.get("canonical_name", ""), *item.get("aliases", [])]
        if any(normalized == str(candidate).casefold().strip() for candidate in candidates):
            return True
    return False


def _repair_team_scope(connection: sqlite3.Connection, config: ProjectConfig) -> None:
    """Keep primary-LCK and academy flags correct for external tournament opponents."""

    rows = connection.execute("SELECT team_id,canonical_name FROM teams").fetchall()
    for row in rows:
        team_id, name = int(row[0]), str(row[1])
        is_primary = int(_is_configured_primary(config, name))
        is_academy = int(_is_academy_name(name))
        connection.execute(
            "UPDATE teams SET is_lck_primary=?,is_academy=?,updated_at=datetime('now') WHERE team_id=?",
            (is_primary, is_academy, team_id),
        )


def _repair_current_starter_flags(connection: sqlite3.Connection) -> None:
    """Derive the global convenience flag from each team's latest roster period.

    The authoritative scope is `(team_id, player_id)` in `roster_periods`; the
    player dimension flag is only a UI convenience and must remain true when a
    player is current for any tracked team.
    """

    connection.execute(
        """UPDATE players SET is_current_starter=CASE WHEN EXISTS (
                   SELECT 1 FROM roster_periods r
                   WHERE r.player_id=players.player_id AND r.is_primary=1
                     AND r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2
                                       WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)
               ) THEN 1 ELSE 0 END,
               updated_at=datetime('now')"""
    )


def _ensure_schema_columns(connection: sqlite3.Connection) -> None:
    """Apply additive column migrations while keeping schema version 1 compatible."""

    existing = {row[1] for row in connection.execute("PRAGMA table_info(team_game_stats)").fetchall()}
    if "team_gold" not in existing:
        connection.execute("ALTER TABLE team_game_stats ADD COLUMN team_gold REAL")


def gold_differential_per_minute(
    team_gold: float | None,
    opponent_gold: float | None,
    duration_seconds: int | None,
) -> float | None:
    """Return GDM: final gold difference divided by game duration in minutes."""

    if team_gold is None or opponent_gold is None or not duration_seconds:
        return None
    return (float(team_gold) - float(opponent_gold)) * 60.0 / float(duration_seconds)


def _repair_derived_team_economy(connection: sqlite3.Connection) -> None:
    """Recalculate GPM/GDM from stored gold after a formula correction.

    Earlier snapshots stored total final gold difference in the ``gdm``
    column.  GDM means gold differential *per minute*, so this idempotent
    repair divides the difference by game duration. Rows without source gold
    remain untouched instead of being filled with invented values.
    """

    connection.execute(
        """UPDATE team_game_stats AS current
           SET gpm = current.team_gold * 60.0 /
                     (SELECT g.duration_seconds FROM games g WHERE g.game_id=current.game_id),
               gdm = (current.team_gold -
                     (SELECT opponent.team_gold FROM team_game_stats opponent
                      WHERE opponent.game_id=current.game_id
                        AND opponent.team_id=current.opponent_id)) * 60.0 /
                     (SELECT g.duration_seconds FROM games g WHERE g.game_id=current.game_id)
           WHERE current.team_gold IS NOT NULL
             AND EXISTS (SELECT 1 FROM team_game_stats opponent
                         WHERE opponent.game_id=current.game_id
                           AND opponent.team_id=current.opponent_id
                           AND opponent.team_gold IS NOT NULL)
             AND (SELECT g.duration_seconds FROM games g
                  WHERE g.game_id=current.game_id) > 0"""
    )


def table_counts(path: Path | str) -> dict[str, int]:
    """Return deterministic row counts for a quick smoke check."""

    with closing(connect_database(path)) as connection:
        tables = [
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        return {
            table: int(connection.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0])
            for table in tables
        }


def schema_summary(path: Path | str) -> dict[str, Any]:
    """Return schema version and table counts for health/report evidence."""

    with closing(connect_database(path)) as connection:
        version = connection.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    return {"path": str(path), "schema_version": version, "tables": table_counts(path)}


def upsert_parsed_game(config: ProjectConfig, parsed: Any, fetch_result: Any | None = None, database_path: Path | str | None = None) -> dict[str, int]:
    """Persist one parsed game and its player/team facts idempotently.

    The function deliberately accepts the parser's dataclass structurally so the
    storage layer remains independent from HTML details.
    """

    database_path = initialize_database(config, database_path)
    teams = (parsed.team_stats[0], parsed.team_stats[1])
    with closing(connect_database(database_path)) as connection:
        for team in teams:
            is_academy = int(_is_academy_name(team.team_name))
            is_primary = int(_is_configured_primary(config, team.team_name))
            connection.execute(
                """INSERT INTO teams(team_id, canonical_name, short_name, region, is_lck_primary, is_academy, source_url)
                   VALUES (?, ?, ?, 'KR', 1, 0, ?)
                   ON CONFLICT(team_id) DO UPDATE SET canonical_name=excluded.canonical_name,
                     short_name=excluded.short_name, region=excluded.region,
                     is_lck_primary=excluded.is_lck_primary, is_academy=excluded.is_academy,
                     source_url=excluded.source_url, updated_at=datetime('now')""",
                (team.team_id, team.team_name, team.team_name, f"https://gol.gg/teams/team-stats/{team.team_id}/split-ALL/tournament-ALL/"),
            )
            connection.execute(
                "UPDATE teams SET is_lck_primary=?,is_academy=? WHERE team_id=?",
                (is_primary, is_academy, team.team_id),
            )
        if parsed.tournament_name:
            tournament_id = "golgg:" + re.sub(r"[^a-z0-9]+", "-", parsed.tournament_name.casefold()).strip("-")
            tournament_type = _classify_tournament(parsed.tournament_name)
            connection.execute(
                "INSERT INTO tournaments(tournament_id,tournament_name,season,tournament_type) VALUES (?,?, 'S16',?) ON CONFLICT(tournament_id) DO UPDATE SET tournament_name=excluded.tournament_name,tournament_type=excluded.tournament_type",
                (tournament_id, parsed.tournament_name, tournament_type),
            )
        else:
            tournament_id = None
        series_id = _series_id(parsed, tournament_id)
        if series_id and tournament_id:
            connection.execute(
                """INSERT INTO series(series_id,tournament_id,played_at,patch,best_of,team_a_id,team_b_id,winner_team_id)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(series_id) DO UPDATE SET played_at=excluded.played_at,patch=excluded.patch,winner_team_id=excluded.winner_team_id""",
                (series_id, tournament_id, parsed.played_at, parsed.patch, None, min(parsed.blue_team_id, parsed.red_team_id), max(parsed.blue_team_id, parsed.red_team_id), parsed.winner_team_id),
            )
        connection.execute(
            """INSERT INTO games(game_id, series_id, game_number, played_at, duration_seconds, patch,
                                  blue_team_id, red_team_id, winner_team_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(game_id) DO UPDATE SET series_id=excluded.series_id,game_number=excluded.game_number,played_at=excluded.played_at,
                 duration_seconds=excluded.duration_seconds, patch=excluded.patch,
                 blue_team_id=excluded.blue_team_id, red_team_id=excluded.red_team_id,
                 winner_team_id=excluded.winner_team_id""",
            (parsed.game_id, series_id, parsed.game_number, parsed.played_at, parsed.duration_seconds, parsed.patch, parsed.blue_team_id, parsed.red_team_id, parsed.winner_team_id),
        )
        for team in parsed.team_stats:
            opponent_id = parsed.red_team_id if team.team_id == parsed.blue_team_id else parsed.blue_team_id
            duration_minutes = (parsed.duration_seconds or 0) / 60
            gpm = team.gold / duration_minutes if team.gold is not None and duration_minutes else None
            opponent_gold = next((other.gold for other in parsed.team_stats if other.team_id == opponent_id), None)
            # GDM is a rate, not the total final gold difference. Keeping the
            # unit gold/minute makes teams from short and long games comparable.
            gdm = gold_differential_per_minute(team.gold, opponent_gold, parsed.duration_seconds)
            opponent_kills = next((other.kills for other in parsed.team_stats if other.team_id == opponent_id), None)
            connection.execute(
                """INSERT INTO team_game_stats(game_id,team_id,opponent_id,side,win,kills,deaths,towers,dragons,nashors,team_gold,gpm,gdm,first_blood,first_tower)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(game_id,team_id) DO UPDATE SET opponent_id=excluded.opponent_id,
                     side=excluded.side, win=excluded.win, kills=excluded.kills, deaths=excluded.deaths,
                     towers=excluded.towers, dragons=excluded.dragons, nashors=excluded.nashors,
                     team_gold=excluded.team_gold,gpm=excluded.gpm,gdm=excluded.gdm,
                     first_blood=excluded.first_blood,first_tower=excluded.first_tower""",
                (parsed.game_id, team.team_id, opponent_id, team.side, int(team.win), team.kills, opponent_kills, team.towers, team.dragons, team.nashors, team.gold, gpm, gdm, int(team.first_blood) if team.first_blood is not None else None, int(team.first_tower) if team.first_tower is not None else None),
            )
        for player in parsed.player_stats:
            connection.execute(
                """INSERT INTO players(player_id,canonical_name,primary_role,is_current_starter)
                   VALUES (?,?,?,0)
                   ON CONFLICT(player_id) DO UPDATE SET canonical_name=excluded.canonical_name,
                     primary_role=excluded.primary_role, is_current_starter=excluded.is_current_starter,
                     updated_at=datetime('now')""",
                (player.player_id, player.player_name, player.role),
            )
            if player.champion_id and player.champion_name:
                connection.execute(
                    "INSERT OR IGNORE INTO champions(champion_id,champion_name) VALUES (?,?)",
                    (player.champion_id, player.champion_name),
                )
            kda = (player.kills + player.assists) / max(player.deaths, 1)
            connection.execute(
                """INSERT INTO player_game_stats(game_id,player_id,team_id,opponent_team_id,role,champion_id,
                   is_starting_lineup,kills,deaths,assists,kda,cs)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(game_id,player_id) DO UPDATE SET team_id=excluded.team_id,
                     opponent_team_id=excluded.opponent_team_id, role=excluded.role,
                     champion_id=excluded.champion_id, is_starting_lineup=excluded.is_starting_lineup,
                     kills=excluded.kills, deaths=excluded.deaths, assists=excluded.assists,
                     kda=excluded.kda, cs=excluded.cs""",
                (parsed.game_id, player.player_id, player.team_id,
                 parsed.red_team_id if player.team_id == parsed.blue_team_id else parsed.blue_team_id,
                 player.role, player.champion_id, int(player.is_starting_lineup), player.kills,
                 player.deaths, player.assists, kda, player.cs),
            )
        # Draft rows are a replaceable snapshot of one game page.  Delete the
        # previous snapshot first so a parser correction (for example fewer
        # actions after removing duplicates) cannot leave stale higher order
        # rows behind in SQLite.
        connection.execute("DELETE FROM drafts WHERE game_id=?", (parsed.game_id,))
        for draft in getattr(parsed, "drafts", ()):
            connection.execute(
                "INSERT OR IGNORE INTO champions(champion_id,champion_name) VALUES (?,?)",
                (draft.champion_id, draft.champion_name),
            )
            connection.execute(
                """INSERT OR REPLACE INTO drafts(game_id,side,phase,action_order,action_type,champion_id)
                   VALUES (?,?,?,?,?,?)""",
                (parsed.game_id, draft.side, draft.phase, draft.action_order, draft.action_type, draft.champion_id),
            )
        connection.execute("DELETE FROM timeline_events WHERE game_id=?", (parsed.game_id,))
        for event in getattr(parsed, "timeline_events", ()):
            connection.execute(
                """INSERT INTO timeline_events(game_id,event_order,minute,second,side,event_type,objective,raw_label)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (parsed.game_id, event.event_order, event.minute, event.second, event.side,
                 event.event_type, event.objective, event.raw_label),
            )
        _refresh_current_starters(connection, (parsed.blue_team_id, parsed.red_team_id))
        if fetch_result is not None:
            connection.execute(
                """INSERT OR IGNORE INTO crawl_manifest(url,entity_type,entity_id,collected_at,status_code,content_hash,raw_path,parse_status)
                   VALUES (?,?,?,?,?,?,?,'parsed')""",
                (fetch_result.url, fetch_result.entity_type, fetch_result.entity_id, fetch_result.fetched_at,
                 fetch_result.status_code, fetch_result.content_hash, fetch_result.raw_path),
            )
        connection.commit()
    return {"games": 1, "teams": len(teams), "players": len(parsed.player_stats), "team_game_stats": len(parsed.team_stats), "player_game_stats": len(parsed.player_stats)}


def upsert_fullstats(config: ProjectConfig, game_id: str, fullstats: Any, fetch_result: Any | None = None, database_path: Path | str | None = None) -> int:
    """Merge nullable player metrics from a validated Gol.gg full-stats page."""

    database_path = initialize_database(config, database_path)
    updated = 0
    with closing(connect_database(database_path)) as connection:
        for stat in fullstats:
            row = connection.execute(
                """SELECT p.player_id FROM player_game_stats p JOIN players pl ON pl.player_id=p.player_id
                   WHERE p.game_id=? AND p.role=? AND lower(pl.canonical_name)=lower(?) LIMIT 1""",
                (game_id, stat.role, stat.player_name),
            ).fetchone()
            if row is None:
                continue
            connection.execute(
                """UPDATE player_game_stats SET csm=?,gold=?,gpm=?,gold_share=?,vision_score_per_minute=?,
                   damage=?,dpm=?,damage_share=?,csd15=?,gd15=?,xpd15=?,ahead_cs15=?,solo_kills=?
                   WHERE game_id=? AND player_id=?""",
                (stat.csm, stat.gold, stat.gpm, stat.gold_share, stat.vision_score_per_minute,
                 stat.damage, stat.dpm, stat.damage_share, stat.csd15, stat.gd15, stat.xpd15,
                 stat.ahead_cs15, stat.solo_kills, game_id, row[0]),
            )
            updated += 1
        for team_row in connection.execute("SELECT DISTINCT team_id FROM player_game_stats WHERE game_id=?", (game_id,)).fetchall():
            aggregate = connection.execute(
                "SELECT SUM(dpm) dpm,SUM(csm) csm,SUM(gd15) gd15,SUM(csd15) csd15 FROM player_game_stats WHERE game_id=? AND team_id=?",
                (game_id, team_row[0]),
            ).fetchone()
            connection.execute(
                "UPDATE team_game_stats SET dpm=?,csm=?,gd15=?,csd15=? WHERE game_id=? AND team_id=?",
                (aggregate[0], aggregate[1], aggregate[2], aggregate[3], game_id, team_row[0]),
            )
        if fetch_result is not None:
            connection.execute(
                """INSERT OR IGNORE INTO crawl_manifest(url,entity_type,entity_id,collected_at,status_code,content_hash,raw_path,parse_status)
                   VALUES (?,?,?,?,?,?,?,'parsed')""",
                (fetch_result.url, fetch_result.entity_type, fetch_result.entity_id, fetch_result.fetched_at,
                 fetch_result.status_code, fetch_result.content_hash, fetch_result.raw_path),
            )
        connection.commit()
    return updated


def _classify_tournament(name: str) -> str:
    """Classify official events as domestic or international context."""

    normalized = name.casefold()
    international_markers = ("msi", "worlds", "world championship", "first stand", "esports world cup", "ewc")
    if any(marker in normalized for marker in international_markers):
        return "international"
    if "lck" in normalized or "kespa" in normalized:
        return "domestic"
    return "unknown"


def _series_id(parsed: Any, tournament_id: str | None) -> str | None:
    """Build a stable best-of series key from event, teams and date."""

    if not tournament_id or not parsed.played_at:
        return None
    return f"golgg-series:{tournament_id}:{parsed.played_at}:{min(parsed.blue_team_id, parsed.red_team_id)}-{max(parsed.blue_team_id, parsed.red_team_id)}"


def _refresh_current_starters(connection: sqlite3.Connection, team_ids: tuple[int, ...]) -> None:
    """Derive current starters from the most recent completed game per team."""

    for team_id in team_ids:
        latest = connection.execute(
            """SELECT g.game_id,g.played_at FROM games g JOIN player_game_stats p ON p.game_id=g.game_id
               WHERE p.team_id=? ORDER BY g.played_at DESC,g.game_id DESC LIMIT 1""",
            (team_id,),
        ).fetchone()
        if latest is None:
            continue
        starter_rows = connection.execute(
            "SELECT player_id,role FROM player_game_stats WHERE game_id=? AND team_id=? ORDER BY CASE role WHEN 'TOP' THEN 1 WHEN 'JUNGLE' THEN 2 WHEN 'MID' THEN 3 WHEN 'BOT' THEN 4 WHEN 'SUPPORT' THEN 5 ELSE 6 END LIMIT 5",
            (latest[0], team_id),
        ).fetchall()
        for row in starter_rows:
            connection.execute("UPDATE players SET is_current_starter=1,updated_at=datetime('now') WHERE player_id=?", (row[0],))
            connection.execute(
                """INSERT OR REPLACE INTO roster_periods(team_id,player_id,role,valid_from,valid_to,is_primary,evidence_game_id)
                   VALUES (?,?,?, ?,NULL,1,?)""",
                (team_id, row[0], row[1] or "UNKNOWN", latest[1] or "2026-01-01", latest[0]),
            )
    _repair_current_starter_flags(connection)
