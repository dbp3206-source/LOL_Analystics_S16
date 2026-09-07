# Final Data Schema

## Core dimensions

### teams

- team_id, canonical_name, short_name, region
- is_lck_primary, is_academy
- External tournament opponents may be retained for H2H context, but `is_lck_primary = 0` keeps them out of the primary LCK summaries.

### players

- player_id, canonical_name, nationality, primary_role
- is_current_starter

### champions

- champion_id, champion_name

### tournaments

- tournament_id, tournament_name, season, split
- tournament_type: domestic/international

## Core facts

### series

- series_id, tournament_id, played_at, patch, best_of
- team_a_id, team_b_id, score_a, score_b, winner_team_id

### games

- game_id, series_id, game_number, played_at, duration_seconds, patch
- blue_team_id, red_team_id, winner_team_id

### team_game_stats

- game_id, team_id, opponent_id, side, win
- kills, deaths, assists, team_gold, gpm, gdm, dpm, csm
  - `gpm`: team gold chia cho duration phút.
  - `gdm`: `(team_gold - opponent_gold)` chia cho duration phút; không phải total final gold difference.
- gd15, csd15, td15, dra15
- first_blood, first_tower
- dragons, voidgrubs, heralds, nashors, towers
- vision metrics when available

### player_game_stats

- game_id, player_id, team_id, opponent_team_id
- role, champion_id, is_starting_lineup
- kills, deaths, assists, kda, kp
- cs, csm, gold, gpm, gold_share
- damage, dpm, damage_share
- csd15, gd15, xpd15, ahead_cs15
- first_blood_participation, first_blood_victim
- solo_kills and vision metrics when available

### drafts

- game_id, side, phase, action_order, action_type, champion_id

### timeline_events

- game_id, event_order, minute, second, side
- event_type, objective, raw_label
- Source-provided milestone events: first blood, first tower, dragon, herald, voidgrubs and Nashor.

### roster_periods

- team_id, player_id, role, valid_from, valid_to
- is_primary, evidence_game_id

### schedules

- fixture_id, scheduled_at_utc, tournament_id
- team_a_id, team_b_id, best_of, status
- source_url, collected_at

## Operational tables

### crawl_manifest

- url, entity_type, entity_id
- collected_at, status_code, content_hash, raw_path, parse_status

### data_quality_results

- check_name, table_name, run_at, passed, affected_rows, details

### update_runs

- run_id, started_at, finished_at, status
- pages_requested, pages_changed, rows_upserted, error_count

## Derived tables

### team_prematch_features

Một dòng cho mỗi team trước mỗi game, gồm rolling 5/10, form weight, side, patch, objectives, economy, combat, vision và roster stability.

### matchup_prematch_features

Chênh lệch Team A minus Team B tại cùng prediction timestamp.

### prediction_log

- fixture/game ID, prediction_timestamp, data_cutoff
- model_version, feature_version
- probabilities, predicted winner, actual winner và evaluation fields

## Current implementation notes

- Game summary pages currently populate team gold, derived GPM/GDM theo đơn vị gold/minute, deaths (from opponent kills), objectives, first blood/first tower and summary draft picks/bans when those elements are present.
- `roster_periods` is refreshed from the most recent completed game per tracked team; current-starter analysis joins the latest period per `(team_id, player_id)`. `players.is_current_starter` is only a convenience flag and not a claim that every historical appearance was a starter contract.
- Full-stats player damage/economy, CS@15/GD@15/XP@15 and vision fields are populated for collected games. `timeline_events` stores source-provided first blood, first tower, dragon, herald, voidgrub and Nashor timestamps; unsupported kill/CS event streams remain nullable.

## Mandatory constraints

- Dataset chính có `season = S16`.
- `is_lck_primary = true` cho team universe.
- Academy/Challengers không đi vào phân tích chính.
- Player UI chỉ hiển thị `is_current_starter = true`.
- Một game hoàn tất có đúng hai team và một winner.
- Feature timestamp nhỏ hơn target timestamp.
- Mọi tỷ lệ champion/player lưu cả numerator và denominator hoặc số game.
