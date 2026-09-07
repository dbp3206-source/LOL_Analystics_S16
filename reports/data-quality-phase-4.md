# Phase 4 Data Quality Report

- Status: **passed**
- Run at: `2026-09-07T17:29:36.917266+00:00`
- Season: `S16` from `2026-01-01`

## Cleaning

`{"teams": 0, "players": 0, "champions": 0, "player_roles": 0}`

## Checks

| Check | Table | Pass | Affected rows | Details |
|---|---|:---:|---:|---|
| season_scope_games | games | ✅ | 0 | played_at must be >= 2026-01-01 |
| game_two_teams_and_winner | games | ✅ | 0 | each completed game needs two distinct teams and one winner |
| team_stats_two_rows_per_game | team_game_stats | ✅ | 0 | each game must have exactly two team stat rows |
| starting_lineup_five_per_team | player_game_stats | ✅ | 0 | each team in a completed game must have exactly five player rows |
| current_roster_five_players | roster_periods | ✅ | 0 | each tracked current roster must expose five starters |
| player_numeric_ranges | player_game_stats | ✅ | 0 | kills/deaths/assists/cs/kda cannot be negative |
| team_economy_metric_ranges | team_game_stats | ✅ | 0 | GPM is positive and GDM is stored in gold per minute, not total gold difference |
| academy_challenger_exclusion | teams | ✅ | 0 | primary LCK dataset must not contain Academy/Challengers teams; external opponents may be retained as non-primary dimensions |
| role_domain | players | ✅ | 0 | roles normalized to TOP/JUNGLE/MID/BOT/SUPPORT |
| timeline_event_ranges | timeline_events | ✅ | 0 | timeline timestamps use non-negative minutes and seconds in [0,59] |
| draft_actions_are_unique | drafts | ✅ | 0 | one champion can appear at most once per side/action type on a game summary |
| draft_ten_picks_ten_bans | drafts | ✅ | 0 | a parsed completed draft contains ten picks and ten bans |
