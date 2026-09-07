"""Small, testable parsers for the first Gol.gg source audit."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup


GOL_ROOT = "https://gol.gg/"
GOL_TEAMS_ROOT = "https://gol.gg/teams/"


@dataclass(frozen=True)
class TeamLink:
    """One team-directory row with the stable Gol.gg team ID."""

    canonical_name: str
    url: str
    team_id: int
    is_challenger_or_academy: bool


@dataclass(frozen=True)
class TeamMatch:
    """One match-list row plus the decision to include it in S16."""

    result: str
    score: str
    opponent: str
    duration: str
    game_name: str
    patch: str
    week: str
    tournament: str
    game_url: str | None
    tournament_year: int | None
    included_from_2026: bool


def _text(node: Any) -> str:
    """Read visible text safely from an optional BeautifulSoup node."""

    return node.get_text(" ", strip=True) if node else ""


def _team_id(href: str) -> int | None:
    """Extract Gol.gg's numeric team ID from a team-stats URL."""

    match = re.search(r"/team-stats/(\d+)/", href)
    return int(match.group(1)) if match else None


def parse_team_directory(html: str, base_url: str = GOL_TEAMS_ROOT) -> list[TeamLink]:
    """Extract unique teams and flag Academy/Challengers by name."""

    soup = BeautifulSoup(html, "html.parser")
    results: list[TeamLink] = []
    seen_ids: set[int] = set()
    for anchor in soup.select("a[href*='/team-stats/']"):
        name = _text(anchor)
        href = anchor.get("href", "")
        team_id = _team_id(href)
        if not name or team_id is None or team_id in seen_ids:
            continue
        seen_ids.add(team_id)
        lowered = name.casefold()
        results.append(
            TeamLink(
                canonical_name=name,
                url=urljoin(base_url, href),
                team_id=team_id,
                is_challenger_or_academy=any(token in lowered for token in ("challenger", "academy", "youth")),
            )
        )
    return results


def parse_label_tables(html: str) -> dict[str, str]:
    """Extract simple label/value rows from Gol.gg table_list tables."""

    soup = BeautifulSoup(html, "html.parser")
    output: dict[str, str] = {}
    for row in soup.select("table.table_list tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) < 2:
            continue
        # Gol.gg sometimes renders labels as ``Region :`` with whitespace
        # before the colon; normalize both sides so callers get stable keys.
        label = _text(cells[0]).strip().rstrip(":").strip()
        value = _text(cells[1])
        if label and value and label not in output:
            output[label] = value
    return output


def parse_team_summary(html: str) -> dict[str, Any]:
    """Extract basic team labels and verify the visible S16 context."""

    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.title)
    heading = soup.find(["h1", "h2"])
    summary = parse_label_tables(html)
    return {
        "title": title,
        "team_name": _text(heading),
        "summary": summary,
        "season": "S16" if "S16" in title or "S16" in _text(heading) else None,
    }


def _extract_year(value: str) -> int | None:
    """Return the last explicit calendar year found in a label."""

    years = re.findall(r"\b(20\d{2})\b", value)
    return int(years[-1]) if years else None


def parse_team_match_list(html: str, season_start: date = date(2026, 1, 1), base_url: str = GOL_ROOT) -> list[TeamMatch]:
    """Parse match rows and quarantine rows without trustworthy 2026 scope."""

    soup = BeautifulSoup(html, "html.parser")
    table = None
    for candidate in soup.select("table"):
        headers = [_text(cell) for cell in candidate.select("tr:first-child th")]
        # The result header is team-specific (e.g. ``T1 Result`` or
        # ``HLE Result``), so identify the stable suffix instead of hardcoding
        # one team's name.
        has_result_header = any(re.search(r"\bResult$", header) for header in headers)
        if has_result_header and "Tournament" in headers:
            table = candidate
            break
    if table is None:
        return []

    matches: list[TeamMatch] = []
    for row in table.select("tr")[1:]:
        cells = row.find_all("td", recursive=False)
        values = [_text(cell) for cell in cells]
        if len(values) < 17:
            continue
        tournament = values[16]
        tournament_year = _extract_year(tournament)
        # Unknown tournament years are quarantined until a game-level date is
        # available; this prevents pre-2026 rows from entering an S16 analysis.
        included = tournament_year is not None and tournament_year >= season_start.year
        opponent = values[7]
        game_anchor = row.select_one("a[href*='/game/stats/']")
        game_url = urljoin(base_url, game_anchor.get("href")) if game_anchor else None
        matches.append(
            TeamMatch(
                result=values[0],
                score=values[1],
                opponent=opponent,
                duration=values[12],
                game_name=values[13],
                patch=values[14],
                week=values[15],
                tournament=tournament,
                game_url=game_url,
                tournament_year=tournament_year,
                included_from_2026=included,
            )
        )
    return matches


def to_dicts(items: list[Any]) -> list[dict[str, Any]]:
    """Convert parser dataclasses into JSON-serializable dictionaries."""

    return [asdict(item) for item in items]
