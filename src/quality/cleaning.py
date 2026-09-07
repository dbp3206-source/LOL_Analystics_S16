"""Deterministic normalization steps applied before analysis."""

from __future__ import annotations

import sqlite3

from ..config import ProjectConfig


ROLE_MAP = {
    "TOP": "TOP",
    "TOPLANE": "TOP",
    "JUNGLE": "JUNGLE",
    "JG": "JUNGLE",
    "MID": "MID",
    "MIDLANE": "MID",
    "BOT": "BOT",
    "ADC": "BOT",
    "AD CARRY": "BOT",
    "BOTTOM": "BOT",
    "SUP": "SUPPORT",
    "SUPPORT": "SUPPORT",
}


def normalize_role(value: str | None) -> str | None:
    """Map source role aliases to TOP/JUNGLE/MID/BOT/SUPPORT."""

    if value is None:
        return None
    normalized = " ".join(value.strip().upper().split())
    return ROLE_MAP.get(normalized, normalized or None)


def normalize_text(value: str | None) -> str | None:
    """Collapse repeated whitespace while preserving a true missing value."""

    if value is None:
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def clean_dimension_values(connection: sqlite3.Connection, config: ProjectConfig) -> dict[str, int]:
    """Normalize source text in-place and return affected-row counts."""

    changed = {"teams": 0, "players": 0, "champions": 0, "player_roles": 0}
    alias_map: dict[str, str] = {}
    for team in config.tracked_lck_teams:
        canonical = normalize_text(team["canonical_name"])
        alias_map[canonical.casefold()] = canonical
        for alias in team.get("aliases", []):
            alias_map[normalize_text(alias).casefold()] = canonical

    for row in connection.execute("SELECT team_id, canonical_name FROM teams").fetchall():
        current = normalize_text(row["canonical_name"])
        canonical = alias_map.get((current or "").casefold(), current)
        if canonical != row["canonical_name"]:
            connection.execute("UPDATE teams SET canonical_name=?, updated_at=datetime('now') WHERE team_id=?", (canonical, row["team_id"]))
            changed["teams"] += 1

    for row in connection.execute("SELECT player_id, canonical_name, primary_role FROM players").fetchall():
        name = normalize_text(row["canonical_name"])
        role = normalize_role(row["primary_role"])
        if name != row["canonical_name"] or role != row["primary_role"]:
            connection.execute(
                "UPDATE players SET canonical_name=?, primary_role=?, updated_at=datetime('now') WHERE player_id=?",
                (name, role, row["player_id"]),
            )
            changed["players"] += 1
            if role != row["primary_role"]:
                changed["player_roles"] += 1

    for row in connection.execute("SELECT champion_id, champion_name FROM champions").fetchall():
        name = normalize_text(row["champion_name"])
        if name != row["champion_name"]:
            connection.execute("UPDATE champions SET champion_name=? WHERE champion_id=?", (name, row["champion_id"]))
            changed["champions"] += 1
    connection.commit()
    return changed
