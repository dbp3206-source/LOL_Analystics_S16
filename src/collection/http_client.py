"""Rate-limited, cache-aware HTTP client for public source pages."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from ..config import ProjectConfig


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResult:
    """Metadata that proves where one archived HTML response came from.

    The HTML body is stored on disk instead of inside this object.  Keeping
    only provenance here makes the manifest small and lets later ETL steps
    reproduce exactly which source file was parsed.
    """

    url: str
    entity_type: str
    entity_id: str
    status_code: int
    fetched_at: str
    content_hash: str
    raw_path: str
    from_cache: bool


def _safe_slug(value: str) -> str:
    """Convert a web identifier into a portable folder/file name."""

    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unknown"


class CachedHttpClient:
    """Download public pages responsibly and preserve reproducible raw data.

    This class owns four collection concerns: a daily file cache, a polite
    delay between requests, bounded retries, and a SHA-256 crawl manifest.
    Parsing is intentionally kept elsewhere so collection failures and HTML
    interpretation can be tested independently.
    """

    def __init__(self, config: ProjectConfig) -> None:
        """Create one reusable HTTP session from the central project config."""

        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.update_policy.user_agent})
        self._last_request_monotonic: float | None = None
        self.manifest_path = config.raw_data_path / "crawl_manifest.jsonl"

    def _wait_for_rate_limit(self) -> None:
        """Sleep only for the unused part of the configured request interval."""

        if self._last_request_monotonic is None:
            return
        elapsed = time.monotonic() - self._last_request_monotonic
        remaining = self.config.update_policy.rate_limit_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _raw_path(self, entity_type: str, entity_id: str, fetched_at: datetime) -> Path:
        """Build ``raw/date/entity/id.html`` so every crawl remains auditable."""

        date_folder = fetched_at.date().isoformat()
        return (
            self.config.raw_data_path
            / date_folder
            / _safe_slug(entity_type)
            / f"{_safe_slug(entity_id)}.html"
        )

    def fetch(self, url: str, entity_type: str, entity_id: str, force: bool = False) -> FetchResult:
        """Fetch a page and archive the exact response with a JSONL manifest."""

        now = datetime.now(timezone.utc)
        raw_path = self._raw_path(entity_type, entity_id, now)
        # The cache is evaluated before touching the network.  This is both
        # faster for daily demos and gentler on the public data source.
        cache_age_hours = (now.timestamp() - raw_path.stat().st_mtime) / 3600 if raw_path.exists() else None
        if raw_path.exists() and not force and cache_age_hours is not None and cache_age_hours <= self.config.update_policy.max_age_hours:
            content = raw_path.read_bytes()
            result = FetchResult(
                url=url,
                entity_type=entity_type,
                entity_id=entity_id,
                status_code=200,
                fetched_at=datetime.fromtimestamp(raw_path.stat().st_mtime, timezone.utc).isoformat(),
                content_hash=hashlib.sha256(content).hexdigest(),
                raw_path=str(raw_path),
                from_cache=True,
            )
            LOGGER.info("Cache hit: %s", url)
            return result
        if raw_path.exists() and not force:
            LOGGER.info("Cache expired (%.2fh): %s", cache_age_hours or 0, url)

        last_error: Exception | None = None
        # A bounded retry loop handles temporary network/server failures.  The
        # attempt number doubles as a simple linear backoff (1 s, 2 s, ...).
        for attempt in range(1, self.config.update_policy.max_retries + 1):
            try:
                self._wait_for_rate_limit()
                self._last_request_monotonic = time.monotonic()
                response = self.session.get(
                    url,
                    timeout=self.config.update_policy.request_timeout_seconds,
                )
                response.raise_for_status()
                content = response.content
                # Raw HTML is written before any parser runs.  If Gol.gg later
                # changes layout, we can repair the parser without re-crawling.
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(content)
                fetched_at = datetime.now(timezone.utc).isoformat()
                result = FetchResult(
                    url=url,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    status_code=response.status_code,
                    fetched_at=fetched_at,
                    # The checksum detects accidental changes and links a
                    # processed row back to the exact downloaded bytes.
                    content_hash=hashlib.sha256(content).hexdigest(),
                    raw_path=str(raw_path),
                    from_cache=False,
                )
                self._append_manifest(result)
                LOGGER.info("Fetched %s (%s bytes)", url, len(content))
                return result
            except requests.RequestException as exc:
                last_error = exc
                LOGGER.warning("Fetch attempt %s/%s failed for %s: %s", attempt, self.config.update_policy.max_retries, url, exc)
                if attempt < self.config.update_policy.max_retries:
                    time.sleep(float(attempt))

        raise RuntimeError(f"Unable to fetch {url}") from last_error

    def _append_manifest(self, result: FetchResult) -> None:
        """Append one immutable JSON line; JSONL is easy to stream and audit."""

        self.config.raw_data_path.mkdir(parents=True, exist_ok=True)
        with self.manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")


def read_raw_html(result: FetchResult) -> str:
    """Load archived HTML and replace invalid bytes instead of crashing ETL."""

    return Path(result.raw_path).read_text(encoding="utf-8", errors="replace")
