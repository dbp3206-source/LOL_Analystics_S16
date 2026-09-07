"""Best-effort future-fixture adapter for the supplemental schedule source."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from ..storage.database import connect_database, initialize_database
from .http_client import CachedHttpClient, read_raw_html


@dataclass(frozen=True)
class ScheduleFixture:
    """One normalized UTC fixture from the supplemental schedule source."""

    fixture_id: str
    scheduled_at_utc: str
    team_a_name: str
    team_b_name: str
    best_of: int | None
    status: str | None
    source_url: str


def _iso_datetime(value: str) -> str | None:
    """Normalize a general ISO timestamp to timezone-aware UTC."""

    value = value.strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _leaguepedia_datetime(value: str) -> str | None:
    """Parse Leaguepedia's human-readable timestamp and convert to UTC."""

    try:
        parsed = datetime.strptime(value.strip(), "%d %B %Y %H:%M:%S %z")
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc).isoformat()


def parse_schedule_page(html: str, source_url: str) -> list[ScheduleFixture]:
    """Parse JSON-LD SportsEvent records and accessible HTML schedule rows.

    The parser intentionally returns only fixtures with a timezone-aware
    timestamp and two named teams; an opaque JavaScript shell is quarantined
    rather than guessed.
    """

    fixtures: list[ScheduleFixture] = []

    # LoL Esports exposes a JSON schedule endpoint in addition to its JS shell.
    # Keep this adapter tolerant of both the documented `data.schedule.events`
    # envelope and a direct `schedule.events` payload.
    try:
        payload = json.loads(html)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        parsed_html = payload.get("parse", {}).get("text", {}).get("*") if isinstance(payload.get("parse"), dict) else None
        if isinstance(parsed_html, str) and parsed_html.strip():
            fixtures.extend(parse_schedule_page(parsed_html, source_url))
        data = payload.get("data", payload)
        schedule = data.get("schedule", data) if isinstance(data, dict) else {}
        events = schedule.get("events", []) if isinstance(schedule, dict) else []
        for event in events if isinstance(events, list) else []:
            if not isinstance(event, dict):
                continue
            match = event.get("match") if isinstance(event.get("match"), dict) else event
            teams = match.get("teams", []) if isinstance(match, dict) else []
            start = _iso_datetime(str(event.get("startTime") or event.get("startDate") or match.get("startTime", "")))
            if not start or not isinstance(teams, list) or len(teams) < 2:
                continue
            names = [str(team.get("name") or team.get("code") or "").strip() for team in teams[:2] if isinstance(team, dict)]
            if len(names) != 2 or not all(names):
                continue
            strategy = match.get("strategy") if isinstance(match, dict) else {}
            best_of = strategy.get("count") if isinstance(strategy, dict) else None
            fixture_id = str(match.get("id") or event.get("id") or f"schedule:{start}:{names[0]}:{names[1]}")
            fixtures.append(ScheduleFixture(fixture_id, start, names[0], names[1], int(best_of) if best_of else None, str(event.get("state") or event.get("status") or "scheduled"), source_url))

    soup = BeautifulSoup(html, "html.parser")

    # Leaguepedia MediaWiki API: current LCK stage cards expose the UTC
    # timestamp and two team-title links in deterministic HTML.
    for box_index, box in enumerate(soup.select("div.topschedule-box")):
        header = box.select_one(".topschedule-header")
        header_text = header.get_text(" ", strip=True) if header else ""
        if not header_text.startswith("LCK 2026"):
            continue
        vs = box.select_one(".topschedule-vs")
        names: list[str] = []
        for anchor in vs.select("a[title]") if vs else []:
            name = str(anchor.get("title", "")).strip()
            if name and name.casefold() not in {"tbd", "to be determined"} and name not in names:
                names.append(name)
        date_node = box.select_one(".countdowndate")
        start = _leaguepedia_datetime(date_node.get_text(" ", strip=True)) if date_node else None
        if not start or len(names) < 2:
            continue
        fixture_id = f"leaguepedia:{start}:{names[0]}:{names[1]}:{box_index}"
        fixtures.append(ScheduleFixture(fixture_id, start, names[0], names[1], None, "scheduled", source_url))
    for node in soup.select("script[type='application/ld+json']"):
        try:
            payload = json.loads(node.get_text(strip=True))
        except json.JSONDecodeError:
            continue
        records = payload if isinstance(payload, list) else [payload]
        for record in records:
            if not isinstance(record, dict) or record.get("@type") not in {"SportsEvent", "Event"}:
                continue
            start = _iso_datetime(str(record.get("startDate", "")))
            competitor = record.get("competitor")
            home = record.get("homeTeam") or (competitor[0] if isinstance(competitor, list) and competitor else None)
            away = record.get("awayTeam")
            if not start or not isinstance(home, dict) or not isinstance(away, dict):
                continue
            name_a, name_b = str(home.get("name", "")).strip(), str(away.get("name", "")).strip()
            if not name_a or not name_b:
                continue
            fixture_id = str(record.get("@id") or record.get("identifier") or f"schedule:{start}:{name_a}:{name_b}")
            fixtures.append(ScheduleFixture(fixture_id, start, name_a, name_b, None, str(record.get("eventStatus") or "scheduled"), source_url))

    for row_index, row in enumerate(soup.select("table tr")):
        time_node = row.select_one("time[datetime]")
        links = [node.get_text(" ", strip=True) for node in row.select("a") if node.get_text(" ", strip=True)]
        if not time_node or len(links) < 2:
            continue
        start = _iso_datetime(time_node.get("datetime", ""))
        if not start:
            continue
        text = row.get_text(" ", strip=True)
        best_of_match = re.search(r"BO\s*([135])", text, flags=re.IGNORECASE)
        fixture_id = row.get("data-fixture-id") or f"schedule:{start}:{links[0]}:{links[1]}:{row_index}"
        fixtures.append(ScheduleFixture(str(fixture_id), start, links[0], links[1], int(best_of_match.group(1)) if best_of_match else None, "scheduled", source_url))
    unique: dict[str, ScheduleFixture] = {item.fixture_id: item for item in fixtures}
    return list(unique.values())


def upsert_schedule_fixtures(config: Any, fixtures: list[ScheduleFixture]) -> dict[str, int]:
    """Resolve LCK aliases and idempotently store valid two-team fixtures."""

    database_path = initialize_database(config)
    aliases = {}
    for item in config.tracked_lck_teams:
        aliases[str(item["canonical_name"]).casefold()] = str(item["canonical_name"]).casefold()
        aliases.update({str(alias).casefold(): str(item["canonical_name"]).casefold() for alias in item.get("aliases", [])})
    inserted = 0
    skipped = 0
    with connect_database(database_path) as connection:
        team_ids = {row["canonical_name"].casefold(): row["team_id"] for row in connection.execute("SELECT team_id,canonical_name FROM teams WHERE is_lck_primary=1")}
        for fixture in fixtures:
            canonical_a = aliases.get(fixture.team_a_name.casefold())
            canonical_b = aliases.get(fixture.team_b_name.casefold())
            team_a_id, team_b_id = team_ids.get(canonical_a or ""), team_ids.get(canonical_b or "")
            if team_a_id is None or team_b_id is None or team_a_id == team_b_id:
                skipped += 1
                continue
            connection.execute(
                """INSERT INTO schedules(fixture_id,scheduled_at_utc,team_a_id,team_b_id,best_of,status,source_url,collected_at)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(fixture_id) DO UPDATE SET scheduled_at_utc=excluded.scheduled_at_utc,team_a_id=excluded.team_a_id,team_b_id=excluded.team_b_id,best_of=excluded.best_of,status=excluded.status,collected_at=excluded.collected_at""",
                (fixture.fixture_id, fixture.scheduled_at_utc, team_a_id, team_b_id, fixture.best_of, fixture.status, fixture.source_url, datetime.now(timezone.utc).isoformat()),
            )
            inserted += 1
        connection.commit()
    return {"fixtures_seen": len(fixtures), "fixtures_upserted": inserted, "fixtures_skipped": skipped}


def run_schedule_update(config: Any, source_url: str | None = None, force: bool = False) -> dict[str, Any]:
    """Fetch configured stage pages, parse fixtures and write a run report."""

    source_url = source_url or config.sources["schedule"]
    source_urls = list(config.sources.get("schedule_pages", [source_url]))
    client = CachedHttpClient(config)
    fixtures: list[ScheduleFixture] = []
    fetched_pages = []
    for index, page_url in enumerate(source_urls):
        fetched = client.fetch(page_url, "schedule", f"primary-{index}", force=force)
        fetched_pages.append(fetched)
        fixtures.extend(parse_schedule_page(read_raw_html(fetched), page_url))
    counts = upsert_schedule_fixtures(config, fixtures)
    report = {"status": "ok", "source_url": source_url, "source_urls": source_urls, "collected_at": max(item.fetched_at for item in fetched_pages), **counts}
    path = config.root / "reports" / "schedule-latest.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(path)
    return report
