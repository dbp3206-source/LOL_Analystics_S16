# 30 — Master cheatsheet (đọc trên điện thoại)

## One-line workflow

`Question → config → cached scrape → parse → SQLite → clean/quality → EDA/metrics → visual/statistics → predict/backtest → report/Streamlit`.

## Commands

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli health
.\.venv-vscode\Scripts\python.exe -m src.cli show-config
.\.venv-vscode\Scripts\python.exe -m unittest discover -s tests -v
.\.venv-vscode\Scripts\python.exe -m streamlit run src\app\streamlit_app.py
```

Exact data/report commands: `docs/RUNBOOK.md`.

## Formulas

- `win_rate = wins / games`
- `KDA = (kills + assists) / max(deaths, 1)` (confirm report definition)
- `DPM = damage / minutes`
- `CSD@15 = player CS@15 − opponent CS@15`
- `GD@15 = team gold@15 − opponent gold@15`
- `p = sigmoid(z)`

## Always report

Season, league, source, as-of, sample/denominator, missingness, uncertainty, limitation.

## Top files

`src/config.py`, `src/collection/game_parsers.py`, `src/storage/database.py`, `src/analysis/metrics.py`, `src/analysis/visualizations.py`, `src/modeling/backtest.py`, `src/app/streamlit_app.py`, `tests/`, `docs/RUNBOOK.md`.

## Top defense reminders

No future data. No denominator-free rate. No causal claim from observational match stats. No “fresh” claim without timestamp. No chart without question.

## 10-second answer

“Em define scope S16/LCK, ingest cached Gol.gg HTML, parse into typed records, upsert into SQLite, validate/clean, calculate explainable DA metrics, visualize with contextual charts, evaluate a time-safe logistic baseline, and publish reproducible reports/UI with caveats.”

