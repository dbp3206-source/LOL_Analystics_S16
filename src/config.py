"""Project configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "project.json"


@dataclass(frozen=True)
class UpdatePolicy:
    """Network freshness, timeout, retry and politeness settings."""

    max_age_hours: int
    request_timeout_seconds: int
    max_retries: int
    rate_limit_seconds: float
    user_agent: str


@dataclass(frozen=True)
class ProjectConfig:
    """Validated project scope plus paths derived from one JSON file."""

    project_name: str
    season: str
    season_start_date: str
    timezone: str
    update_policy: UpdatePolicy
    sources: dict[str, str]
    tracked_lck_teams: tuple[dict[str, Any], ...]
    project_root: Path

    @property
    def root(self) -> Path:
        """Return the absolute project root controlled by this config."""

        return self.project_root

    @property
    def database_path(self) -> Path:
        """Return the canonical SQLite file used by every pipeline phase."""

        return self.root / "data" / "lol_analytics.db"

    @property
    def raw_data_path(self) -> Path:
        """Return the immutable/raw HTML archive directory."""

        return self.root / "data" / "raw"

    @property
    def processed_data_path(self) -> Path:
        """Return the directory for analysis-ready CSV intermediates."""

        return self.root / "data" / "processed"

    @property
    def logs_path(self) -> Path:
        """Return the local runtime log directory."""

        return self.root / "logs"


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> ProjectConfig:
    """Load the JSON configuration and enforce foundation invariants."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    required_keys = {
        "project_name",
        "season",
        "season_start_date",
        "timezone",
        "update_policy",
        "sources",
        "tracked_lck_teams",
    }
    missing = required_keys.difference(raw)
    if missing:
        raise ValueError(f"Missing configuration keys: {sorted(missing)}")

    if raw["season"] != "S16":
        raise ValueError("The project is locked to Season S16.")

    if raw["season_start_date"] < "2026-01-01":
        raise ValueError("Season S16 data is locked to calendar date 2026-01-01 or later.")

    teams = raw["tracked_lck_teams"]
    if len(teams) != 10:
        raise ValueError(f"Expected 10 tracked LCK teams, got {len(teams)}.")

    team_names = [team.get("canonical_name") for team in teams]
    if any(not name for name in team_names) or len(set(team_names)) != len(team_names):
        raise ValueError("Tracked teams must have unique canonical_name values.")

    policy = raw["update_policy"]
    return ProjectConfig(
        project_name=raw["project_name"],
        season=raw["season"],
        season_start_date=raw["season_start_date"],
        timezone=raw["timezone"],
        update_policy=UpdatePolicy(
            max_age_hours=int(policy["max_age_hours"]),
            request_timeout_seconds=int(policy["request_timeout_seconds"]),
            max_retries=int(policy["max_retries"]),
            rate_limit_seconds=float(policy["rate_limit_seconds"]),
            user_agent=str(policy["user_agent"]),
        ),
        sources=dict(raw["sources"]),
        tracked_lck_teams=tuple(teams),
        # A config stored under <project>/configs controls that project.  This
        # keeps normal usage unchanged while allowing tests and teaching
        # examples to run in a temporary isolated project root.
        project_root=config_path.resolve().parent.parent,
    )


def ensure_runtime_directories(config: ProjectConfig) -> None:
    """Create only local runtime directories; never create data from the web here."""

    directories = (
        config.raw_data_path,
        config.processed_data_path,
        config.logs_path,
        config.root / "models",
        config.root / "reports" / "figures",
        config.root / "reports" / "generated",
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
