"""Run the Phase 2 T1/HLE source audit and prototype crawl."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from .http_client import CachedHttpClient, read_raw_html
from .parsers import parse_team_directory, parse_team_match_list, parse_team_summary, to_dicts
from ..config import ensure_runtime_directories, load_config


TEAM_LIST_URL = "https://gol.gg/teams/list/season-S16/split-ALL/tournament-ALL/"
ROBOTS_URL = "https://gol.gg/robots.txt"


def run_source_audit() -> dict:
    """Check robots/source structure and preserve a small T1–HLE audit."""

    config = load_config()
    ensure_runtime_directories(config)
    client = CachedHttpClient(config)
    robots_result = client.fetch(ROBOTS_URL, "robots", "golgg")
    robots_text = read_raw_html(robots_result)
    disallowed_paths = [
        line.split(":", 1)[1].strip()
        for line in robots_text.splitlines()
        if line.lower().startswith("disallow:") and line.split(":", 1)[1].strip()
    ]
    directory_result = client.fetch(TEAM_LIST_URL, "team_directory", "s16_all")
    directory_html = read_raw_html(directory_result)
    all_teams = parse_team_directory(directory_html, "https://gol.gg/teams/")

    target_names = {"T1", "Hanwha Life Esports"}
    targets = [team for team in all_teams if team.canonical_name in target_names]
    if len(targets) != 2:
        raise RuntimeError(f"Expected T1 and HLE in directory, found {[team.canonical_name for team in targets]}")

    team_reports: list[dict] = []
    for team in targets:
        stats_result = client.fetch(team.url, "team_stats", str(team.team_id))
        stats = parse_team_summary(read_raw_html(stats_result))
        team_base = "https://gol.gg/teams/"
        match_url = f"https://gol.gg/teams/team-matchlist/{team.team_id}/split-ALL/tournament-ALL/"
        match_result = client.fetch(match_url, "team_matchlist", str(team.team_id))
        matches = parse_team_match_list(read_raw_html(match_result), date.fromisoformat(config.season_start_date), team_base)
        included = [match for match in matches if match.included_from_2026]
        excluded = [match for match in matches if not match.included_from_2026]
        team_reports.append(
            {
                "team": team.canonical_name,
                "team_id": team.team_id,
                "team_url": team.url,
                "is_challenger_or_academy": team.is_challenger_or_academy,
                "stats": stats,
                "match_list_url": match_url,
                "match_count_raw": len(matches),
                "match_count_included_from_2026": len(included),
                "match_count_excluded_pre_2026": len(excluded),
                "excluded_tournaments": sorted({match.tournament for match in excluded}),
                "sample_included_matches": to_dicts(included[:3]),
            }
        )

    report = {
        "phase": "Phase 2 — Source audit and scraper prototype",
        "season": config.season,
        "season_start_date": config.season_start_date,
        "statistics_source": config.sources["statistics"],
        "robots": {
            "url": ROBOTS_URL,
            "status_code": robots_result.status_code,
            "disallowed_paths": disallowed_paths,
            "requested_paths_disallowed": any(path.startswith("/teams/") or path.startswith("/game/stats/") for path in disallowed_paths),
        },
        "team_directory_url": TEAM_LIST_URL,
        "directory_team_count": len(all_teams),
        "challenger_or_academy_count": sum(team.is_challenger_or_academy for team in all_teams),
        "targets": team_reports,
        "findings": [
            "Gol.gg exposes the S16 team directory and team-matchlist pages with stable IDs.",
            "The S16 filter includes Kespa Cup 2025 rows; calendar filtering from 2026-01-01 is mandatory.",
            "Robots.txt was checked; the requested /teams/ and /game/stats/ paths are not listed as disallowed, and the prototype applies a 1.5-second request interval.",
            "Team match-list pages expose result, score, opponent, duration, patch, week and tournament, but not a reliable played date in every row.",
            "Game-level pages provide authoritative dates and player/team facts; the current incremental collector parses and stores them after the match-list discovery step.",
        ],
    }
    report_path = config.root / "reports" / "source-audit-phase-2.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path = config.root / "reports" / "source-audit-phase-2.md"
    markdown_path.write_text(render_markdown_report(report), encoding="utf-8")
    return report


def render_markdown_report(report: dict) -> str:
    """Render the source-audit evidence and scope findings as Markdown."""

    lines = [
        "# Phase 2 Source Audit",
        "",
        f"- Season filter: `{report['season']}`",
        f"- Calendar start: `{report['season_start_date']}`",
        f"- Directory rows discovered: `{report['directory_team_count']}`",
        f"- Statistics source: {report['statistics_source']}",
        f"- robots.txt status: `{report['robots']['status_code']}`; requested paths disallowed: `{report['robots']['requested_paths_disallowed']}`",
        "",
        "## Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["findings"])
    lines.extend(["", "## T1/HLE prototype coverage", "", "| Team | Raw rows | Included from 2026 | Excluded pre-2026 |", "|---|---:|---:|---:|"])
    for target in report["targets"]:
        lines.append(
            f"| {target['team']} | {target['match_count_raw']} | {target['match_count_included_from_2026']} | {target['match_count_excluded_pre_2026']} |"
        )
    return "\n".join(lines) + "\n"
