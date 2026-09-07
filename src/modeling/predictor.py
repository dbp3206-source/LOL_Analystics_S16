"""Explainable S16 matchup baseline.

This is intentionally an empirical baseline, not a claim of a calibrated
production ML model. It uses Laplace/Beta smoothing, sample size and
optional S16 head-to-head evidence, so the dashboard can communicate both a
prediction and when the evidence is too thin.
"""

from __future__ import annotations

import json
import math
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ProjectConfig
from ..storage.database import connect_database, initialize_database


MODEL_VERSION = "empirical-strength-v1"
FEATURE_VERSION = "s16-win-rate-h2h-economy-v3-gdm-per-minute"


def _team_form(
    connection: Any,
    team_id: int,
    season_start_date: str,
    cutoff_date_exclusive: str,
) -> dict[str, Any] | None:
    """Aggregate only games known before the prediction cutoff date."""
    row = connection.execute(
        """SELECT t.team_id,t.canonical_name,COUNT(DISTINCT s.game_id) games,
                  COALESCE(SUM(s.win),0) wins,
                  AVG(s.gpm) avg_gpm,AVG(s.gdm) avg_gdm,
                  AVG(s.kills) avg_kills,AVG(s.deaths) avg_deaths,
                  AVG(s.first_tower) first_tower_rate,
                  MAX(g.played_at) data_cutoff
           FROM teams t JOIN team_game_stats s ON s.team_id=t.team_id
                  JOIN games g ON g.game_id=s.game_id
           WHERE t.team_id=? AND g.played_at>=? AND g.played_at<?
           GROUP BY t.team_id,t.canonical_name""",
        (team_id, season_start_date, cutoff_date_exclusive),
    ).fetchone()
    if row is None:
        return None
    games = int(row["games"] or 0)
    wins = int(row["wins"] or 0)
    # Uniform Beta(1,1) prior avoids 0/1 certainty from tiny samples.
    posterior_mean = (wins + 1) / (games + 2)
    se = math.sqrt(posterior_mean * (1 - posterior_mean) / (games + 3))
    return {
        "team_id": team_id,
        "team": row["canonical_name"],
        "games": games,
        "wins": wins,
        "losses": games - wins,
        "raw_win_rate": wins / games if games else None,
        "posterior_win_rate": posterior_mean,
        "uncertainty_90": min(0.5, 1.645 * se),
        "avg_gpm": row["avg_gpm"],
        "avg_gdm": row["avg_gdm"],
        "avg_kills": row["avg_kills"],
        "avg_deaths": row["avg_deaths"],
        "first_tower_rate": row["first_tower_rate"],
        "data_cutoff": row["data_cutoff"],
    }


def _head_to_head(
    connection: Any,
    team_a_id: int,
    team_b_id: int,
    season_start_date: str,
    cutoff_date_exclusive: str,
) -> dict[str, Any]:
    """Return S16 head-to-head evidence available before the cutoff."""
    rows = connection.execute(
        """SELECT a.win AS a_win
           FROM team_game_stats a JOIN team_game_stats b ON a.game_id=b.game_id
           JOIN games g ON g.game_id=a.game_id
           WHERE a.team_id=? AND b.team_id=? AND g.played_at>=? AND g.played_at<?""",
        (team_a_id, team_b_id, season_start_date, cutoff_date_exclusive),
    ).fetchall()
    games = len(rows)
    wins_a = sum(int(row["a_win"]) for row in rows)
    return {
        "games": games,
        "wins_team_a": wins_a,
        "wins_team_b": games - wins_a,
        "team_a_rate": wins_a / games if games else None,
    }


def predict_matchup(config: ProjectConfig, team_a_id: int, team_b_id: int, fixture_id: str | None = None, persist: bool = True) -> dict[str, Any]:
    """Predict an official future fixture or an explicitly hypothetical matchup.

    When ``fixture_id`` is supplied, the stored schedule is authoritative: the
    teams must match, the fixture must still be in the future, and features use
    only games dated before the fixture day.  Without a fixture ID the result
    is labelled hypothetical and uses today as an exclusive cutoff.
    """
    if team_a_id == team_b_id:
        raise ValueError("team_a_id and team_b_id must be different")
    database_path = initialize_database(config)
    prediction_timestamp = datetime.now(timezone.utc).isoformat()
    with closing(connect_database(database_path)) as connection:
        latest_update = connection.execute(
            """SELECT finished_at FROM update_runs
               WHERE status='success' AND finished_at IS NOT NULL
               ORDER BY finished_at DESC LIMIT 1"""
        ).fetchone()
        latest_update_at = str(latest_update[0]) if latest_update else None
        freshness_age_hours = (
            (datetime.fromisoformat(prediction_timestamp) - datetime.fromisoformat(latest_update_at)).total_seconds() / 3600
            if latest_update_at
            else None
        )
        data_is_fresh = freshness_age_hours is not None and freshness_age_hours <= config.update_policy.max_age_hours

        fixture_timestamp = None
        prediction_context = "hypothetical"
        if fixture_id is not None:
            fixture = connection.execute(
                """SELECT fixture_id,scheduled_at_utc,team_a_id,team_b_id,status
                   FROM schedules WHERE fixture_id=?""",
                (fixture_id,),
            ).fetchone()
            if fixture is None:
                raise ValueError(f"Unknown fixture_id: {fixture_id}")
            if {int(fixture["team_a_id"]), int(fixture["team_b_id"])} != {team_a_id, team_b_id}:
                raise ValueError("fixture teams do not match the requested matchup")
            fixture_timestamp = str(fixture["scheduled_at_utc"])
            if datetime.fromisoformat(fixture_timestamp) <= datetime.fromisoformat(prediction_timestamp):
                raise ValueError("official fixture is not in the future")
            if not data_is_fresh:
                raise ValueError("official fixture prediction requires a successful data update within the freshness window")
            prediction_context = "official_fixture"

        # Gol.gg stores the authoritative game date but not a reliable start
        # timestamp for every historical row.  Excluding the entire cutoff day
        # is conservative and prevents same-day target leakage.
        feature_cutoff_exclusive = (fixture_timestamp or prediction_timestamp)[:10]
        team_a = _team_form(connection, team_a_id, config.season_start_date, feature_cutoff_exclusive)
        team_b = _team_form(connection, team_b_id, config.season_start_date, feature_cutoff_exclusive)
        if team_a is None or team_b is None:
            raise ValueError("Both teams need S16 games before the prediction cutoff")
        h2h = _head_to_head(connection, team_a_id, team_b_id, config.season_start_date, feature_cutoff_exclusive)
        # Strength ratio combines smoothed result evidence with available
        # economy/combat signals. Each component is descriptive and keeps its
        # own null when Gol.gg has not exposed that metric.
        def ratio(a: Any, b: Any) -> float | None:
            """Express A's share of two non-missing positive signals."""

            if a is None or b is None or float(a) + float(b) == 0:
                return None
            return float(a) / (float(a) + float(b))

        def centered_difference(a: Any, b: Any, scale: float) -> float | None:
            """Map a signed metric difference to [0, 1] around neutral 0.5."""

            if a is None or b is None:
                return None
            difference = max(-scale, min(scale, float(a) - float(b)))
            return 0.5 + difference / (2.0 * scale)

        components = {
            "posterior_win_rate": ratio(team_a["posterior_win_rate"], team_b["posterior_win_rate"]),
            "avg_gpm": ratio(team_a["avg_gpm"], team_b["avg_gpm"]),
            "avg_gdm": centered_difference(team_a["avg_gdm"], team_b["avg_gdm"], 1000.0),
            "combat_rate": ratio((team_a["avg_kills"] or 0) + 1, (team_b["avg_kills"] or 0) + 1),
            "first_tower_rate": ratio(team_a["first_tower_rate"], team_b["first_tower_rate"]),
        }
        available = [value for value in components.values() if value is not None]
        p_a = sum(available) / len(available) if available else 0.5
        blend_weight = min(0.25, h2h["games"] / 20) if h2h["games"] else 0.0
        if h2h["team_a_rate"] is not None:
            p_a = (1 - blend_weight) * p_a + blend_weight * ((h2h["wins_team_a"] + 1) / (h2h["games"] + 2))
        p_a = max(0.01, min(0.99, p_a))
        p_b = 1 - p_a
        sample_size = team_a["games"] + team_b["games"]
        data_cutoff = max(item["data_cutoff"] for item in (team_a, team_b) if item["data_cutoff"] is not None) if any(item["data_cutoff"] for item in (team_a, team_b)) else None
        status = "insufficient_data" if min(team_a["games"], team_b["games"]) < 5 else "baseline_ready"
        winner = team_a_id if p_a >= p_b else team_b_id
        fixture_id = fixture_id or f"s16-{team_a_id}-vs-{team_b_id}-{prediction_timestamp[:10]}"
        result = {
            "fixture_id": fixture_id,
            "prediction_timestamp": prediction_timestamp,
            "prediction_context": prediction_context,
            "fixture_timestamp": fixture_timestamp,
            "feature_cutoff_exclusive": feature_cutoff_exclusive,
            "data_freshness": {
                "status": "fresh" if data_is_fresh else "stale_or_missing",
                "last_successful_update": latest_update_at,
                "age_hours": freshness_age_hours,
                "max_age_hours": config.update_policy.max_age_hours,
            },
            "data_cutoff": data_cutoff,
            "feature_values": components,
            "model_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "status": status,
            "sample_size_total": sample_size,
            "small_sample_warning": min(team_a["games"], team_b["games"]) < 20,
            "team_a": team_a,
            "team_b": team_b,
            "head_to_head": h2h,
            "probability_team_a": p_a,
            "probability_team_b": p_b,
            "predicted_winner_team_id": winner,
            "confidence_note": "Transparent, uncalibrated educational baseline; interpret with sample size and backtest metrics.",
        }
        if persist:
            connection.execute(
                """INSERT INTO prediction_log(fixture_or_game_id,prediction_timestamp,data_cutoff,model_version,feature_version,
                   probability_team_a,probability_team_b,predicted_winner_team_id)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (fixture_id, prediction_timestamp, data_cutoff or prediction_timestamp, MODEL_VERSION, FEATURE_VERSION, p_a, p_b, winner),
            )
            connection.commit()
    report_path = config.root / "reports" / f"prediction-{team_a_id}-vs-{team_b_id}.json"
    if persist:
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["report_path"] = str(report_path)
    else:
        # Tests and notebook experiments can evaluate without mutating the
        # project's real report directory.
        result["report_path"] = None
    return result
