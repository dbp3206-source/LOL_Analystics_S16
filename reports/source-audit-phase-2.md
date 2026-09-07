# Phase 2 Source Audit

- Season filter: `S16`
- Calendar start: `2026-01-01`
- Directory rows discovered: `326`
- Statistics source: https://gol.gg/esports/home/
- robots.txt status: `200`; requested paths disallowed: `False`

## Findings

- Gol.gg exposes the S16 team directory and team-matchlist pages with stable IDs.
- The S16 filter includes Kespa Cup 2025 rows; calendar filtering from 2026-01-01 is mandatory.
- Robots.txt was checked; the requested /teams/ and /game/stats/ paths are not listed as disallowed, and the prototype applies a 1.5-second request interval.
- Team match-list pages expose result, score, opponent, duration, patch, week and tournament, but not a reliable played date in every row.
- Game-level pages provide authoritative dates and player/team facts; the current incremental collector parses and stores them after the match-list discovery step.

## T1/HLE prototype coverage

| Team | Raw rows | Included from 2026 | Excluded pre-2026 |
|---|---:|---:|---:|
| Hanwha Life Esports | 151 | 134 | 17 |
| T1 | 165 | 147 | 18 |
