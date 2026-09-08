# 04 — Repository Architecture

**Prerequisites:** 01–03. **Phone mode:** đầy đủ. **Source:** `README.md`, `docs/05_CODEBASE_FILE_GUIDE.md`, package tree.

## 🧠 Mental Model

```text
CLI / Streamlit / notebook
          ↓
collection → storage → quality → analysis → modeling → reporting
          ↘ tests + fixtures protect contracts
```

Mỗi layer có trách nhiệm riêng. Parser không nên tự vẽ chart; dashboard không nên tự scrape HTML; model không nên tự quyết định season.

## 🗂 Structure

| Path | Vai trò |
|---|---|
| `configs/` | Scope và operational policy |
| `src/collection/` | HTTP, source audit, HTML/JSON parsers, updater |
| `src/storage/` | SQL schema, connection, upsert, derived repair |
| `src/quality/` | Normalize và gates |
| `src/analysis/` | Metrics, EDA, statistics, figures |
| `src/modeling/` | Predictor và walk-forward backtest |
| `src/reporting/` | Final handoff report |
| `app/` | Streamlit UI |
| `scripts/` | Setup, notebook sync, daily/offline orchestration |
| `tests/fixtures/` | Stable source-shaped inputs |
| `reports/` | Evidence artifacts |

## 📱 Phone Mode — file call graph

```text
src.cli.main
 ├─ run_health → config.load_config
 ├─ update-all → updater.run_all_teams_update
 │                 → CachedHttpClient
 │                 → parsers/game_parsers
 │                 → database.upsert_*
 ├─ quality-check → quality.run_quality_checks
 ├─ pandas-eda → pandas_eda.run_pandas_eda
 ├─ visualize → scientific_visualizations.generate_...
 └─ backtest → backtest.run_backtest
```

## 🔗 Data ownership

| Layer | Owns | Does not own |
|---|---|---|
| Collection | source retrieval/parse | business chart |
| Storage | persistence/grain | model interpretation |
| Quality | canonical values/invariants | deleting every outlier |
| Analysis | descriptive metrics | future leakage |
| Modeling | features/probability/evaluation | source scraping |
| App | presentation/input routing | hidden data mutation |

## 🧪 Simulated Lab — trace team win rate

Dashboard asks `team_summary` → SQL reads team-game rows → `win` values `[1,0,1]` → mean `2/3 = 66.7%` → table/chart. If chart says 80%, inspect DataFrame then SQL then parser; do not start by changing color/axis.

## 💻 Try It Yourself

```powershell
rg -n "def |from src|import src" src app scripts
```

Then open `docs/05_CODEBASE_FILE_GUIDE.md` and follow one module end-to-end.

## ❌ What If?

If a source change causes parser + storage + report edits in one function, coupling increases and tests become hard to localize. Keep transformation boundaries explicit.

## 🎤 Defense

- Why SQLite instead of one giant CSV? Relational grain, constraints, joins, idempotent upsert.
- Why separate `reports.py` and `metrics.py`? Reusable metrics vs assembled entity reports.
- Why fixtures? Offline deterministic regression tests.

## ✅ Checkpoint

- [ ] Tôi biết file nào chịu trách nhiệm mỗi layer.
- [ ] Tôi trace được CLI đến output.
- [ ] Tôi hiểu dashboard không phải source of truth.
