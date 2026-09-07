"""Incremental team-to-game updater built on the Phase 2 match-list parser."""

from __future__ import annotations

import re
import json
import uuid
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ProjectConfig, ensure_runtime_directories
from ..storage.database import connect_database, initialize_database, upsert_fullstats, upsert_parsed_game
from .game_parsers import parse_fullstats_page, parse_game_page
from .http_client import CachedHttpClient, read_raw_html
from .parsers import parse_team_match_list
from .parsers import parse_team_directory


def _game_id_from_url(url: str) -> str | None:
    """Extract the stable game ID used for cache and database upserts."""

    match = re.search(r"/game/stats/(\d+)/", url)
    return match.group(1) if match else None


def run_team_update(
    config: ProjectConfig,
    team_id: int,
    max_games: int = 5,
    dry_run: bool = False,
    force: bool = False,
    include_fullstats: bool = False,
) -> dict[str, Any]:
    """Discover 2026 game pages for one team and incrementally upsert them.

    ``max_games=0`` means no limit. Dry-run never requests game-level pages and
    is useful for inspecting crawl volume before a full refresh.
    """

    ensure_runtime_directories(config)
    client = CachedHttpClient(config)
    match_url = f"https://gol.gg/teams/team-matchlist/{team_id}/split-ALL/tournament-ALL/"
    match_result = client.fetch(match_url, "team_matchlist", str(team_id), force=force)
    matches = parse_team_match_list(
        read_raw_html(match_result),
        season_start=date.fromisoformat(config.season_start_date),
    )
    candidate_urls: list[str] = []
    seen: set[str] = set()
    for match in matches:
        if not match.included_from_2026 or not match.game_url or match.game_url in seen:
            continue
        seen.add(match.game_url)
        candidate_urls.append(match.game_url)
    selected_urls = candidate_urls if max_games <= 0 else candidate_urls[:max_games]
    result: dict[str, Any] = {
        "team_id": team_id,
        "matchlist_url": match_url,
        "match_rows_raw": len(matches),
        "game_candidates_2026": len(candidate_urls),
        "game_urls_selected": len(selected_urls),
        "dry_run": dry_run,
        "games_upserted": 0,
        "fullstats_players_updated": 0,
        "include_fullstats": include_fullstats,
        "errors": [],
    }
    if dry_run:
        result["sample_game_urls"] = candidate_urls[:5]
        return result

    database_path = initialize_database(config)
    run_id = f"update-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    started_at = datetime.now(timezone.utc).isoformat()
    with closing(connect_database(database_path)) as connection:
        connection.execute(
            "INSERT INTO update_runs(run_id,started_at,status,pages_requested) VALUES (?,?,?,?)",
            (run_id, started_at, "running", len(selected_urls) + 1),
        )
        connection.commit()
    pages_changed = 0
    rows_upserted = 0
    for url in selected_urls:
        game_id = _game_id_from_url(url)
        if game_id is None:
            result["errors"].append({"url": url, "error": "unrecognized game URL"})
            continue
        try:
            fetched = client.fetch(url, "game_stats", game_id, force=force)
            parsed = parse_game_page(read_raw_html(fetched), game_id)
            if parsed.played_at is None or parsed.played_at < config.season_start_date:
                result["errors"].append({"game_id": game_id, "error": f"outside S16 date scope: {parsed.played_at!r}"})
                continue
            counts = upsert_parsed_game(config, parsed, fetched)
            pages_changed += int(not fetched.from_cache)
            rows_upserted += sum(counts.values())
            result["games_upserted"] += 1
            if include_fullstats:
                fullstats_url = f"https://gol.gg/game/stats/{game_id}/page-fullstats/"
                try:
                    fullstats_fetch = client.fetch(fullstats_url, "game_fullstats", game_id, force=force)
                    fullstats = parse_fullstats_page(read_raw_html(fullstats_fetch))
                    result["fullstats_players_updated"] += upsert_fullstats(config, game_id, fullstats, fullstats_fetch)
                except Exception as exc:
                    result["errors"].append({"game_id": game_id, "entity": "fullstats", "error": str(exc)})
        except Exception as exc:  # keep one malformed page from stopping the daily refresh
            result["errors"].append({"game_id": game_id, "error": str(exc)})

    finished_at = datetime.now(timezone.utc).isoformat()
    status = "success" if not result["errors"] else ("partial" if result["games_upserted"] else "failed")
    with closing(connect_database(database_path)) as connection:
        connection.execute(
            """UPDATE update_runs SET finished_at=?,status=?,pages_changed=?,rows_upserted=?,error_count=? WHERE run_id=?""",
            (finished_at, status, pages_changed, rows_upserted, len(result["errors"]), run_id),
        )
        connection.commit()
    result.update({"run_id": run_id, "status": status, "pages_changed": pages_changed, "rows_upserted": rows_upserted})
    return result


def run_all_teams_update(
    config: ProjectConfig,
    max_games_per_team: int = 1,
    dry_run: bool = True,
    force: bool = False,
    include_fullstats: bool = False,
) -> dict[str, Any]:
    """Resolve the configured 10 primary teams and run the same updater for each."""

    ensure_runtime_directories(config)
    client = CachedHttpClient(config)
    directory_url = "https://gol.gg/teams/list/season-S16/split-ALL/tournament-ALL/"
    directory = client.fetch(directory_url, "team_directory", "s16_all", force=force)
    teams = parse_team_directory(read_raw_html(directory), "https://gol.gg/teams/")
    by_name = {team.canonical_name.casefold(): team for team in teams if not team.is_challenger_or_academy}
    results: list[dict[str, Any]] = []
    for configured in config.tracked_lck_teams:
        canonical = str(configured["canonical_name"])
        team = by_name.get(canonical.casefold())
        if team is None:
            results.append({"team": canonical, "status": "missing_from_directory", "errors": ["No exact primary-team match in Gol.gg directory"]})
            continue
        result = run_team_update(config, team.team_id, max_games_per_team, dry_run, force, include_fullstats)
        result["team"] = canonical
        results.append(result)
    report = {
        "status": "ok" if all(item.get("status") not in {"failed", "missing_from_directory"} for item in results) else "partial",
        "dry_run": dry_run,
        "max_games_per_team": max_games_per_team,
        "include_fullstats": include_fullstats,
        "teams_configured": len(config.tracked_lck_teams),
        "teams_resolved": sum(item.get("status") != "missing_from_directory" for item in results),
        "results": results,
    }
    report_path = config.root / "reports" / "update-all-latest.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report
