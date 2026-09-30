# Pandas EDA Upgrade

- Run at: `2026-09-29T15:47:22.889360+00:00`
- Season: `S16` from `2026-01-01`
- Team-game rows: `2`; player-game rows: `2`

## Workflow

Load → inspect → dtype/date → missing/duplicate → descriptive statistics → IQR review → categorical comparison → correlation.

## Important interpretation rules

- No missing metric is silently imputed.
- IQR identifies review candidates; it does not auto-delete genuine standout games.
- Every percentage table keeps its count denominator.
- Role summaries are required before comparing player metrics across roles.

## Generated tables

- `data/processed/pandas_eda/missingness.csv`
- `data/processed/pandas_eda/team_numeric_summary.csv`
- `data/processed/pandas_eda/player_numeric_summary.csv`
- `data/processed/pandas_eda/iqr_outlier_candidates.csv`
- `data/processed/pandas_eda/side_outcome_crosstab.csv`
- `data/processed/pandas_eda/role_summary.csv`
- `data/processed/pandas_eda/tournament_summary.csv`
- `data/processed/pandas_eda/team_metric_correlation.csv`
