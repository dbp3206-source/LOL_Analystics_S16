"""Parser for the stable, game-level summary page on Gol.gg."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .parsers import _text


# DATA CONTRACTS ------------------------------------------------------------
# Each dataclass states the "grain" (one row represents what) before data is
# inserted into SQLite.  Nullable fields are deliberate: a missing value is
# analytically different from inventing a zero when Gol.gg omits a statistic.

@dataclass(frozen=True)
class GamePlayerStat:
    """One player's basic box-score row in one professional game."""

    player_id: str
    player_name: str
    team_id: int
    role: str
    champion_id: str | None
    champion_name: str | None
    kills: int
    deaths: int
    assists: int
    cs: float | None
    is_starting_lineup: bool = True


@dataclass(frozen=True)
class GameTeamStat:
    """One team-side row in one game; therefore each game normally has two."""

    team_id: int
    team_name: str
    side: str
    win: bool
    kills: int | None
    towers: int | None
    dragons: int | None
    nashors: int | None
    gold: float | None
    first_blood: bool | None = None
    first_tower: bool | None = None


@dataclass(frozen=True)
class GameDraftAction:
    """One ordered champion pick or ban for one side of a game."""

    side: str
    phase: str
    action_order: int
    action_type: str
    champion_id: str
    champion_name: str


@dataclass(frozen=True)
class GameTimelineEvent:
    """One first-event or neutral-objective marker on the game timeline."""

    event_order: int
    minute: int
    second: int
    side: str
    event_type: str
    objective: str
    raw_label: str


@dataclass(frozen=True)
class FullPlayerStat:
    """One player's advanced per-game metrics parsed from the Full Stats page."""

    player_name: str
    role: str
    csm: float | None = None
    gold: float | None = None
    gpm: float | None = None
    gold_share: float | None = None
    vision_score_per_minute: float | None = None
    damage: float | None = None
    dpm: float | None = None
    damage_share: float | None = None
    csd15: float | None = None
    gd15: float | None = None
    xpd15: float | None = None
    ahead_cs15: int | None = None
    solo_kills: float | None = None


@dataclass(frozen=True)
class ParsedGame:
    """Validated in-memory aggregate returned by the game-page parser."""

    game_id: str
    played_at: str | None
    tournament_name: str | None
    patch: str | None
    duration_seconds: int | None
    blue_team_id: int
    blue_team_name: str
    red_team_id: int
    red_team_name: str
    winner_team_id: int | None
    game_number: int | None
    team_stats: tuple[GameTeamStat, ...]
    player_stats: tuple[GamePlayerStat, ...]
    drafts: tuple[GameDraftAction, ...] = ()
    timeline_events: tuple[GameTimelineEvent, ...] = ()


# SMALL PARSING HELPERS ------------------------------------------------------

def _id_from_href(href: str, pattern: str) -> int | None:
    """Extract a numeric Gol.gg entity ID from a hyperlink, if present."""

    match = re.search(pattern, href or "")
    return int(match.group(1)) if match else None


def _number(text: str) -> int | None:
    """Read the first numeric token and return ``None`` for absent data."""

    match = re.search(r"\b(\d+(?:\.\d+)?)\b", text.replace(",", ""))
    return int(float(match.group(1))) if match else None


def _duration_seconds(value: str) -> int | None:
    """Normalize ``MM:SS`` into seconds for filtering and aggregation."""

    match = re.search(r"^(\d+):(\d{2})$", value.strip())
    return int(match.group(1)) * 60 + int(match.group(2)) if match else None


def _date_from_page(soup: BeautifulSoup) -> str | None:
    """Find an ISO game date in visible page text."""

    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", soup.get_text(" ", strip=True))
    return match.group(1) if match else None


def _team_headers(soup: BeautifulSoup) -> dict[str, tuple[int, str, bool]]:
    """Map blue/red sides to team ID, display name, and win flag."""

    result: dict[str, tuple[int, str, bool]] = {}
    for header in soup.select(".blue-line-header, .red-line-header"):
        anchor = header.select_one("a[href*='/teams/team-stats/']")
        if not anchor:
            continue
        team_id = _id_from_href(anchor.get("href", ""), r"team-stats/(\d+)")
        if team_id is None:
            continue
        text = _text(header)
        result["blue" if "blue-line-header" in (header.get("class") or []) else "red"] = (
            team_id,
            _text(anchor),
            bool(re.search(r"\bWIN\b", text)),
        )
    return result


def _team_stat_value(container: Any, icon: str) -> int | None:
    """Read a team metric located beside a semantic image ``alt`` label."""

    image = container.select_one(f"img[alt='{icon}']")
    return _number(_text(image.parent if image and image.parent else image)) if image else None


def _draft_actions(container: Any, side: str) -> list[GameDraftAction]:
    """Extract the compact bans/picks shown on Gol.gg's game summary page.

    Gol.gg nests the real ``Bans`` and ``Picks`` rows inside a parent layout
    row whose combined text is also ``Bans | Picks``.  Reading every nested
    ``div.row`` and then searching recursively for ``.col-2`` therefore
    counts the same champions twice and can label picks as bans.  A real
    action row is identified by a *direct* ``.col-2`` child with an exact
    label, which deliberately ignores the parent layout row.
    """

    actions: list[GameDraftAction] = []
    order = 0
    for row in container.select("div.row"):
        label_node = row.find("div", class_="col-2", recursive=False)
        label = _text(label_node)
        if label not in {"Bans", "Picks"}:
            continue
        action_type = "ban" if label == "Bans" else "pick"
        for anchor in row.select("a[href*='/champion/champion-stats/']"):
            champion_id = _id_from_href(anchor.get("href", ""), r"champion-stats/(\d+)")
            image = anchor.select_one("img[alt]")
            if champion_id is None or image is None:
                continue
            order += 1
            actions.append(GameDraftAction(side, "summary", order, action_type, str(champion_id), image.get("alt", "")))
    return actions


def _timeline_events(soup: BeautifulSoup) -> list[GameTimelineEvent]:
    """Extract objective timestamps embedded in Gol.gg's summary timeline.

    Only events with a known analytical meaning are retained.  Decorative or
    unknown icons are skipped rather than guessed, which protects data quality
    when the source website adds a new marker.
    """
    table = next((table for table in soup.select("table.table_list") if "Gold graph & Timeline" in _text(table)), None)
    if table is None:
        return []
    timeline = table.select_one("div.flex-wrap")
    if timeline is None:
        return []
    events: list[GameTimelineEvent] = []
    for outer in timeline.select(":scope > span"):
        for action in outer.select(":scope > span.blue_action, :scope > span.red_action"):
            text = _text(action)
            timestamp = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
            image = action.select_one("img[alt]")
            if timestamp is None or image is None:
                continue
            label = image.get("alt", "").strip()
            label_lower = label.casefold()
            if "first blood" in label_lower:
                event_type, objective = "first_blood", "first_blood"
            elif "first tower" in label_lower:
                event_type, objective = "first_tower", "first_tower"
            elif "dragon" in label_lower or "drake" in label_lower:
                event_type, objective = "objective", "dragon"
            elif "herald" in label_lower:
                event_type, objective = "objective", "herald"
            elif "nashor" in label_lower or "baron" in label_lower:
                event_type, objective = "objective", "nashor"
            elif "voidgrub" in label_lower or "voidgrug" in label_lower:
                event_type, objective = "objective", "voidgrubs"
            else:
                continue
            events.append(GameTimelineEvent(len(events) + 1, int(timestamp.group(1)), int(timestamp.group(2)), "blue" if "blue_action" in (action.get("class") or []) else "red", event_type, objective, label))
    return events


def parse_game_page(html: str, game_id: str | None = None) -> ParsedGame:
    """Turn one Gol.gg game-summary HTML document into typed records.

    The function first extracts game/team context, then draft and timeline,
    and finally the ten player rows.  Returning one aggregate keeps related
    tables consistent when the storage layer inserts them transactionally.
    """

    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.title)
    if game_id is None:
        game_match = re.search(r"gameid\s*=\s*(\d+)", html)
        game_id = game_match.group(1) if game_match else "unknown"
    headers = _team_headers(soup)
    # Both sides are mandatory context.  Failing early is safer than storing a
    # half-game that would silently bias win rates and head-to-head analysis.
    if "blue" not in headers or "red" not in headers:
        raise ValueError("Game page does not expose both blue and red team headers")

    blue_id, blue_name, blue_win = headers["blue"]
    red_id, red_name, red_win = headers["red"]
    duration_heading = soup.find(string=lambda value: value and value.strip() == "Game Time")
    duration = _duration_seconds(_text(duration_heading.find_next("h1")) if duration_heading else "")
    patch_match = re.search(r"\bv(\d+\.\d+)\b", soup.get_text(" ", strip=True))
    tournament_link = soup.select_one("h1 ~ .row a[href*='/tournament/tournament-stats/']")
    game_number_match = re.search(r"\bgame\s+(\d+)\b", title, flags=re.IGNORECASE)

    team_stats: list[GameTeamStat] = []
    # The same extraction logic runs for blue and red, producing a tidy table
    # where rows can later be grouped by team, side, tournament, or outcome.
    for side, (team_id, team_name, win) in headers.items():
        header = next(
            (node for node in soup.select(f".{side}-line-header") if node.select_one("a[href*='/teams/team-stats/']")),
            None,
        )
        card = header.find_parent("div", class_="col-12") if header else None
        card_text = _text(card)
        team_stats.append(
            GameTeamStat(
                team_id=team_id,
                team_name=team_name,
                side=side,
                win=win,
                kills=_team_stat_value(card, "Kills") if card else None,
                towers=_team_stat_value(card, "Towers") if card else None,
                dragons=_team_stat_value(card, "Dragons") if card else None,
                nashors=_team_stat_value(card, "Nashor") if card else None,
                gold=_number(re.search(r"\b(\d+(?:\.\d+)?)k\b", card_text).group(1)) * 1000 if re.search(r"\b(\d+(?:\.\d+)?)k\b", card_text) else None,
                first_blood=bool(card and card.select_one("img[alt='First Blood']")),
                first_tower=bool(card and card.select_one("img[alt='First Tower']")),
            )
        )

    drafts: list[GameDraftAction] = []
    for side in ("blue", "red"):
        header = next(
            (node for node in soup.select(f".{side}-line-header") if node.select_one("a[href*='/teams/team-stats/']")),
            None,
        )
        card = header.find_parent("div", class_="col-12") if header else None
        if card:
            drafts.extend(_draft_actions(card, side))
    timeline_events = _timeline_events(soup)

    player_stats: list[GamePlayerStat] = []
    # Gol.gg orders the five player rows by role.  ``enumerate`` converts that
    # positional HTML convention into an explicit analytical role column.
    roles = ("TOP", "JUNGLE", "MID", "BOT", "SUPPORT")
    for table in soup.select("table.playersInfosLine"):
        header = table.select_one("thead tr")
        classes = header.get("class", []) if header else []
        side = "blue" if "blue-line-header" in classes else "red"
        team_id = headers[side][0]
        for index, row in enumerate(table.find_all("tr", recursive=False)):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 4:
                continue
            player_anchor = cells[0].select_one("a[href*='/players/player-stats/']")
            if not player_anchor:
                continue
            player_id = _id_from_href(player_anchor.get("href", ""), r"player-stats/(\d+)")
            if player_id is None:
                continue
            champion_anchor = cells[0].select_one("a[href*='/champion/champion-stats/']")
            champion_id = _id_from_href(champion_anchor.get("href", ""), r"champion-stats/(\d+)") if champion_anchor else None
            champion_image = champion_anchor.select_one("img") if champion_anchor else None
            kda_match = re.match(r"(\d+)/(\d+)/(\d+)", _text(cells[2]))
            if not kda_match:
                continue
            player_stats.append(
                GamePlayerStat(
                    player_id=str(player_id),
                    player_name=_text(player_anchor),
                    team_id=team_id,
                    role=roles[index] if index < len(roles) else "UNKNOWN",
                    champion_id=str(champion_id) if champion_id is not None else None,
                    champion_name=champion_image.get("alt") if champion_image else None,
                    kills=int(kda_match.group(1)),
                    deaths=int(kda_match.group(2)),
                    assists=int(kda_match.group(3)),
                    cs=float(_text(cells[3]).replace(",", "")) if re.match(r"^\d+(?:\.\d+)?$", _text(cells[3])) else None,
                )
            )

    return ParsedGame(
        game_id=str(game_id),
        played_at=_date_from_page(soup),
        tournament_name=_text(tournament_link) or None,
        patch=patch_match.group(1) if patch_match else None,
        duration_seconds=duration,
        blue_team_id=blue_id,
        blue_team_name=blue_name,
        red_team_id=red_id,
        red_team_name=red_name,
        winner_team_id=blue_id if blue_win else red_id if red_win else None,
        game_number=int(game_number_match.group(1)) if game_number_match else None,
        team_stats=tuple(team_stats),
        player_stats=tuple(player_stats),
        drafts=tuple(drafts),
        timeline_events=tuple(timeline_events),
    )


def _float_value(value: str, percentage: bool = False) -> float | None:
    """Normalize table text to float; percentages become proportions 0..1."""

    cleaned = value.strip().replace(",", "")
    if not cleaned or cleaned.lower() in {"perfect kda", "—", "-"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    number = float(match.group(0))
    return number / 100 if percentage or "%" in cleaned else number


def parse_fullstats_page(html: str) -> tuple[FullPlayerStat, ...]:
    """Parse Gol.gg's wide All Stats table into player-level nullable metrics.

    Gol.gg presents metrics as rows and players as columns.  The loop performs
    a small reshape (wide source -> one object per player), which is the same
    idea as a Pandas transpose/melt before analysis.
    """

    soup = BeautifulSoup(html, "html.parser")
    table = next((table for table in soup.select("table") if "DPM" in table.get_text(" ", strip=True) and "GD@15" in table.get_text(" ", strip=True)), None)
    if table is None:
        raise ValueError("Full-stats page does not expose the expected player metrics table")
    rows: dict[str, list[str]] = {}
    # Build a label -> values dictionary first so column order changes do not
    # force every metric to be addressed by a fragile hard-coded row number.
    for row in table.select("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select(":scope > th, :scope > td")]
        if len(cells) >= 2 and cells[0]:
            rows[cells[0].strip()] = cells[1:]
    names = rows.get("Player", [])
    roles = rows.get("Role", [])
    result: list[FullPlayerStat] = []
    for index, name in enumerate(names):
        role = roles[index] if index < len(roles) else "UNKNOWN"
        role = "BOT" if role.upper() in {"ADC", "AD CARRY", "BOTTOM"} else role.upper()
        csd15 = _float_value(rows.get("CSD@15", [""] * len(names))[index]) if index < len(rows.get("CSD@15", [])) else None
        result.append(
            FullPlayerStat(
                player_name=name,
                role=role,
                csm=_float_value(rows.get("CSM", [""] * len(names))[index]) if index < len(rows.get("CSM", [])) else None,
                gold=_float_value(rows.get("Golds", [""] * len(names))[index]) if index < len(rows.get("Golds", [])) else None,
                gpm=_float_value(rows.get("GPM", [""] * len(names))[index]) if index < len(rows.get("GPM", [])) else None,
                gold_share=_float_value(rows.get("GOLD%", [""] * len(names))[index], percentage=True) if index < len(rows.get("GOLD%", [])) else None,
                vision_score_per_minute=_float_value(rows.get("VSPM", [""] * len(names))[index]) if index < len(rows.get("VSPM", [])) else None,
                damage=_float_value(rows.get("Total damage to Champion", [""] * len(names))[index]) if index < len(rows.get("Total damage to Champion", [])) else None,
                dpm=_float_value(rows.get("DPM", [""] * len(names))[index]) if index < len(rows.get("DPM", [])) else None,
                damage_share=_float_value(rows.get("DMG%", [""] * len(names))[index], percentage=True) if index < len(rows.get("DMG%", [])) else None,
                csd15=csd15,
                gd15=_float_value(rows.get("GD@15", [""] * len(names))[index]) if index < len(rows.get("GD@15", [])) else None,
                xpd15=_float_value(rows.get("XPD@15", [""] * len(names))[index]) if index < len(rows.get("XPD@15", [])) else None,
                ahead_cs15=1 if csd15 is not None and csd15 > 0 else 0 if csd15 is not None else None,
                solo_kills=_float_value(rows.get("Solo kills", [""] * len(names))[index]) if index < len(rows.get("Solo kills", [])) else None,
            )
        )
    if len(result) != 10:
        # A professional game should contain exactly five players per side.
        # Treating another count as a schema change prevents corrupted joins.
        raise ValueError(f"Expected ten player full-stats columns, found {len(result)}")
    return tuple(result)


def parsed_game_to_dict(parsed: ParsedGame) -> dict[str, Any]:
    """Convert nested immutable records to JSON-serializable dictionaries."""

    return {
        **asdict(parsed),
        "team_stats": [asdict(item) for item in parsed.team_stats],
        "player_stats": [asdict(item) for item in parsed.player_stats],
    }
