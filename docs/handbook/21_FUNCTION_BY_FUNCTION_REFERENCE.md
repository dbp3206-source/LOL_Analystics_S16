# 21 — Function-by-function reference

| Module | Function/class | Input → output | Ý nghĩa |
|---|---|---|---|
| `config.py` | `load_config` | env/files → `ProjectConfig` | single source of settings |
| `config.py` | `ensure_runtime_directories` | config → dirs | safe runtime paths |
| `http_client.py` | `CachedHttpClient` | URL → cached response | reproducible fetch |
| `parsers.py` | `parse_team_directory` | HTML → `TeamLink[]` | team discovery |
| `parsers.py` | `parse_team_match_list` | HTML → `TeamMatch[]` | match list |
| `game_parsers.py` | `parse_game_page` | HTML → `ParsedGame` | core game record |
| `game_parsers.py` | `parse_fullstats_page` | HTML → stats | extra player stats |
| `schedule.py` | `parse_schedule_page` | HTML → fixtures | future/current matches |
| `updater.py` | `run_team_update` | team/config → counts | orchestration |
| `database.py` | `initialize_database` | config → schema | idempotent DB |
| `database.py` | `upsert_parsed_game` | record → DB | deduplicated write |
| `database.py` | `table_counts` | DB → dict | observability |
| `cleaning.py` | `normalize_text`, `normalize_role` | raw → canonical | consistent joins |
| `checks.py` | `run_quality_checks` | DB/config → checks | publish gate |
| `metrics.py` | `team_summary` | DB/team → frame | team KPI |
| `metrics.py` | `player_summary` | DB/player → frame | player KPI |
| `metrics.py` | `champion_pool` | DB/player → frame | picks/wins |
| `metrics.py` | `head_to_head` | teams → frame | H2H |
| `metrics.py` | `rolling_form` | team/window → frame | recent trend |
| `pandas_eda.py` | `run_pandas_eda` | DB → report | descriptive audit |
| `statistics.py` | `wilson_interval`, `cohens_d` | samples → stats | uncertainty/effect |
| `visualizations.py` | `generate_visualizations` | metrics → files | core figures |
| `scientific_visualizations.py` | `generate_scientific_visualizations` | metrics → files | advanced figures |
| `predictor.py` | `predict_matchup` | A/B → prediction | conditional probability |
| `backtest.py` | `run_backtest` | history → folds/metrics | time-safe validation |
| `final_report.py` | `generate_final_report` | artifacts → report | delivery narrative |
| `streamlit_app.py` | `main` | UI → interactive app | demo surface |

## 📱 Phone Mode

Đọc mỗi row như một contract: ai gọi, field nào vào, object nào ra, và downstream consumer nào dùng.

## 🧪 Simulated Lab

Nếu `team_summary` trả win rate nhưng không games/wins, đó là output khó audit; sửa contract/report chứ không chỉ đổi format.

## ✅ Checkpoint

Bạn có thể trace một function từ test → caller → output artifact.

