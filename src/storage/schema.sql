PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    short_name TEXT,
    region TEXT,
    is_lck_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_lck_primary IN (0, 1)),
    is_academy INTEGER NOT NULL DEFAULT 0 CHECK (is_academy IN (0, 1)),
    source_url TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    nationality TEXT,
    primary_role TEXT,
    is_current_starter INTEGER NOT NULL DEFAULT 0 CHECK (is_current_starter IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS champions (
    champion_id TEXT PRIMARY KEY,
    champion_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id TEXT PRIMARY KEY,
    tournament_name TEXT NOT NULL,
    season TEXT NOT NULL CHECK (season = 'S16'),
    split TEXT,
    tournament_type TEXT NOT NULL CHECK (tournament_type IN ('domestic', 'international', 'unknown'))
);

CREATE TABLE IF NOT EXISTS series (
    series_id TEXT PRIMARY KEY,
    tournament_id TEXT REFERENCES tournaments(tournament_id),
    played_at TEXT,
    patch TEXT,
    best_of INTEGER,
    team_a_id INTEGER NOT NULL REFERENCES teams(team_id),
    team_b_id INTEGER NOT NULL REFERENCES teams(team_id),
    score_a INTEGER,
    score_b INTEGER,
    winner_team_id INTEGER REFERENCES teams(team_id),
    CHECK (team_a_id <> team_b_id)
);

CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    series_id TEXT REFERENCES series(series_id),
    game_number INTEGER,
    played_at TEXT,
    duration_seconds INTEGER,
    patch TEXT,
    blue_team_id INTEGER NOT NULL REFERENCES teams(team_id),
    red_team_id INTEGER NOT NULL REFERENCES teams(team_id),
    winner_team_id INTEGER REFERENCES teams(team_id),
    CHECK (blue_team_id <> red_team_id),
    CHECK (winner_team_id IS NULL OR winner_team_id IN (blue_team_id, red_team_id))
);

CREATE TABLE IF NOT EXISTS team_game_stats (
    game_id TEXT NOT NULL REFERENCES games(game_id),
    team_id INTEGER NOT NULL REFERENCES teams(team_id),
    opponent_id INTEGER NOT NULL REFERENCES teams(team_id),
    side TEXT NOT NULL CHECK (side IN ('blue', 'red')),
    win INTEGER NOT NULL CHECK (win IN (0, 1)),
    kills REAL, deaths REAL, assists REAL,
    team_gold REAL, gpm REAL, gdm REAL, dpm REAL, csm REAL,
    gd15 REAL, csd15 REAL, td15 REAL, dra15 REAL,
    first_blood INTEGER CHECK (first_blood IS NULL OR first_blood IN (0, 1)),
    first_tower INTEGER CHECK (first_tower IS NULL OR first_tower IN (0, 1)),
    dragons REAL, voidgrubs REAL, heralds REAL, nashors REAL, towers REAL,
    vision_score_per_minute REAL, wards_per_minute REAL,
    PRIMARY KEY (game_id, team_id)
);

CREATE TABLE IF NOT EXISTS player_game_stats (
    game_id TEXT NOT NULL REFERENCES games(game_id),
    player_id TEXT NOT NULL REFERENCES players(player_id),
    team_id INTEGER NOT NULL REFERENCES teams(team_id),
    opponent_team_id INTEGER REFERENCES teams(team_id),
    role TEXT,
    champion_id TEXT REFERENCES champions(champion_id),
    is_starting_lineup INTEGER NOT NULL DEFAULT 0 CHECK (is_starting_lineup IN (0, 1)),
    kills REAL, deaths REAL, assists REAL, kda REAL, kp REAL,
    cs REAL, csm REAL, gold REAL, gpm REAL, gold_share REAL,
    damage REAL, dpm REAL, damage_share REAL,
    csd15 REAL, gd15 REAL, xpd15 REAL, ahead_cs15 INTEGER,
    first_blood_participation INTEGER CHECK (first_blood_participation IS NULL OR first_blood_participation IN (0, 1)),
    first_blood_victim INTEGER CHECK (first_blood_victim IS NULL OR first_blood_victim IN (0, 1)),
    solo_kills REAL,
    vision_score_per_minute REAL,
    PRIMARY KEY (game_id, player_id)
);

CREATE TABLE IF NOT EXISTS drafts (
    game_id TEXT NOT NULL REFERENCES games(game_id),
    side TEXT NOT NULL CHECK (side IN ('blue', 'red')),
    phase TEXT NOT NULL,
    action_order INTEGER NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('ban', 'pick')),
    champion_id TEXT NOT NULL REFERENCES champions(champion_id),
    PRIMARY KEY (game_id, side, phase, action_order)
);

CREATE TABLE IF NOT EXISTS timeline_events (
    game_id TEXT NOT NULL REFERENCES games(game_id),
    event_order INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    second INTEGER NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('blue', 'red')),
    event_type TEXT NOT NULL,
    objective TEXT NOT NULL,
    raw_label TEXT NOT NULL,
    PRIMARY KEY (game_id, event_order)
);

CREATE TABLE IF NOT EXISTS roster_periods (
    team_id INTEGER NOT NULL REFERENCES teams(team_id),
    player_id TEXT NOT NULL REFERENCES players(player_id),
    role TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    is_primary INTEGER NOT NULL DEFAULT 1 CHECK (is_primary IN (0, 1)),
    evidence_game_id TEXT REFERENCES games(game_id),
    PRIMARY KEY (team_id, player_id, valid_from)
);

CREATE TABLE IF NOT EXISTS schedules (
    fixture_id TEXT PRIMARY KEY,
    scheduled_at_utc TEXT NOT NULL,
    tournament_id TEXT REFERENCES tournaments(tournament_id),
    team_a_id INTEGER NOT NULL REFERENCES teams(team_id),
    team_b_id INTEGER NOT NULL REFERENCES teams(team_id),
    best_of INTEGER,
    status TEXT,
    source_url TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    CHECK (team_a_id <> team_b_id)
);

CREATE TABLE IF NOT EXISTS crawl_manifest (
    url TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    parse_status TEXT NOT NULL DEFAULT 'pending',
    PRIMARY KEY (entity_type, entity_id, content_hash)
);

CREATE TABLE IF NOT EXISTS data_quality_results (
    check_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    run_at TEXT NOT NULL,
    passed INTEGER NOT NULL CHECK (passed IN (0, 1)),
    affected_rows INTEGER NOT NULL DEFAULT 0,
    details TEXT,
    PRIMARY KEY (check_name, table_name, run_at)
);

CREATE TABLE IF NOT EXISTS update_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    pages_requested INTEGER NOT NULL DEFAULT 0,
    pages_changed INTEGER NOT NULL DEFAULT 0,
    rows_upserted INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS team_prematch_features (
    fixture_or_game_id TEXT NOT NULL,
    team_id INTEGER NOT NULL REFERENCES teams(team_id),
    feature_timestamp TEXT NOT NULL,
    rolling_games INTEGER NOT NULL,
    win_rate REAL,
    form_weight REAL,
    side TEXT,
    patch TEXT,
    objectives_score REAL,
    economy_score REAL,
    combat_score REAL,
    vision_score REAL,
    roster_stability REAL,
    PRIMARY KEY (fixture_or_game_id, team_id)
);

CREATE TABLE IF NOT EXISTS matchup_prematch_features (
    fixture_or_game_id TEXT PRIMARY KEY,
    team_a_id INTEGER NOT NULL REFERENCES teams(team_id),
    team_b_id INTEGER NOT NULL REFERENCES teams(team_id),
    feature_timestamp TEXT NOT NULL,
    feature_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prediction_log (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_or_game_id TEXT NOT NULL,
    prediction_timestamp TEXT NOT NULL,
    data_cutoff TEXT NOT NULL,
    model_version TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    probability_team_a REAL,
    probability_team_b REAL,
    predicted_winner_team_id INTEGER REFERENCES teams(team_id),
    actual_winner_team_id INTEGER REFERENCES teams(team_id),
    evaluation_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_games_played_at ON games(played_at);
CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_game_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_schedule_time ON schedules(scheduled_at_utc);
CREATE INDEX IF NOT EXISTS idx_crawl_manifest_url ON crawl_manifest(url);
CREATE INDEX IF NOT EXISTS idx_timeline_game ON timeline_events(game_id, minute, second);
