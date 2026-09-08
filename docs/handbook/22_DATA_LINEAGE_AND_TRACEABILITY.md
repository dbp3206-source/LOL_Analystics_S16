# 22 — Data lineage và traceability

## 🧠 Mental Model

Mọi con số phải có đường đi: source field → raw/cache → parser field → DB column → metric formula → figure/report/prediction.

## 📱 Phone Mode

### Trace A — team win rate

`Gol.gg result → ParsedGame.team_stats.win → team_game_stats.win → team_summary wins/games → comparison bar → report claim`.

### Trace B — player DPM

`Fullstats page damage/time → player_game_stats.damage_per_minute → player_summary mean/median → player comparison chart`.

### Trace C — champion pool

`draft/player champion → player_game_stats.champion → champion_pool picks/wins → champion table/heatmap`.

### Trace D — rolling form

`dated team-game rows → chronological sort → rolling_form(window=5) → line chart → recent-form narrative`.

### Trace E — prediction

`past games before cutoff → team form/H2H features → predictor/backtest → probability → next-fixture card; future rows forbidden`.

## 📥 Input

Source URL, source timestamp, record key, SQL query, transformation function, artifact path.

## ⚙️ Step-by-Step Execution

1. Declare grain.
2. Name source field and target field.
3. Record filter/scope.
4. Record formula.
5. Link artifact and caveat.

## 📤 Output

Use existing `docs/DATA_SCHEMA.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, report appendices; this chapter explains how to read them.

## ❌ What If?

No trace → mark result non-publishable. Conflicting source → retain both values with provenance, do not silently overwrite.

## ✅ Checkpoint

Bạn chọn một number trong report và viết được 5-hop lineage tương tự các trace trên.

