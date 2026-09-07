"""Beginner-friendly Pandas/NumPy EDA for the S16 SQLite dataset.

This module mirrors the learning order used in the reference Colab:

1. load data;
2. inspect rows, columns and data types;
3. check missing values and duplicates;
4. calculate descriptive statistics;
5. flag possible outliers with IQR;
6. compare categorical groups;
7. inspect relationships with a correlation matrix.

The functions deliberately return DataFrames as well as writing CSV reports.
That makes every intermediate result visible in VS Code notebooks instead of
hiding the full analysis inside one large command.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import ProjectConfig
from ..storage.database import connect_database, initialize_database


TEAM_NUMERIC_COLUMNS = [
    "win",
    "kills",
    "deaths",
    "gpm",
    "gdm",
    "dpm",
    "csm",
    "gd15",
    "csd15",
    "first_blood",
    "first_tower",
    "dragons",
    "nashors",
    "towers",
]

PLAYER_NUMERIC_COLUMNS = [
    "kills",
    "deaths",
    "assists",
    "kda",
    "csm",
    "dpm",
    "gold_share",
    "damage_share",
    "csd15",
    "gd15",
    "xpd15",
    "vision_score_per_minute",
]


def load_analysis_frames(config: ProjectConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load analysis-ready team and current-starter rows from SQLite.

    Returns
    -------
    (team_games, player_games)
        Two Pandas DataFrames.  Each team row represents one primary LCK team
        in one game; each player row represents one tracked current starter in
        one game. International opponents remain useful context but do not
        become primary comparison entities.
    """

    database_path = initialize_database(config)
    with closing(connect_database(database_path)) as connection:
        team_games = pd.read_sql_query(
            """SELECT s.game_id,g.played_at,g.patch,g.duration_seconds,
                      s.team_id,t.canonical_name team_name,
                      s.opponent_id,op.canonical_name opponent_name,
                      s.side,s.win,s.kills,s.deaths,s.gpm,s.gdm,s.dpm,s.csm,
                      s.gd15,s.csd15,s.first_blood,s.first_tower,
                      s.dragons,s.nashors,s.towers,
                      tr.tournament_name,tr.tournament_type
               FROM team_game_stats s
               JOIN games g ON g.game_id=s.game_id
               JOIN teams t ON t.team_id=s.team_id AND t.is_lck_primary=1
               JOIN teams op ON op.team_id=s.opponent_id
               LEFT JOIN series se ON se.series_id=g.series_id
               LEFT JOIN tournaments tr ON tr.tournament_id=se.tournament_id
               WHERE g.played_at>=?
               ORDER BY g.played_at,s.game_id,s.team_id""",
            connection,
            params=(config.season_start_date,),
        )

        player_games = pd.read_sql_query(
            """SELECT s.game_id,g.played_at,g.patch,s.team_id,t.canonical_name team_name,
                      s.opponent_team_id,op.canonical_name opponent_name,
                      s.player_id,p.canonical_name player_name,s.role,
                      s.champion_id,c.champion_name,
                      s.kills,s.deaths,s.assists,s.kda,s.csm,s.dpm,
                      s.gold_share,s.damage_share,s.csd15,s.gd15,s.xpd15,
                      s.vision_score_per_minute,
                      CASE WHEN g.winner_team_id=s.team_id THEN 1 ELSE 0 END win,
                      tr.tournament_name,tr.tournament_type
               FROM player_game_stats s
               JOIN games g ON g.game_id=s.game_id
               JOIN players p ON p.player_id=s.player_id
               JOIN teams t ON t.team_id=s.team_id AND t.is_lck_primary=1
               JOIN teams op ON op.team_id=s.opponent_team_id
               JOIN roster_periods r ON r.team_id=s.team_id AND r.player_id=s.player_id AND r.is_primary=1
               LEFT JOIN champions c ON c.champion_id=s.champion_id
               LEFT JOIN series se ON se.series_id=g.series_id
               LEFT JOIN tournaments tr ON tr.tournament_id=se.tournament_id
               WHERE g.played_at>=?
                 AND r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2
                                  WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)
               ORDER BY g.played_at,s.game_id,s.role""",
            connection,
            params=(config.season_start_date,),
        )

    # Convert text dates once after loading.  Invalid source dates become NaT
    # so they remain visible in the missing-value audit instead of crashing or
    # being silently replaced with an invented date.
    for frame in (team_games, player_games):
        frame["played_at"] = pd.to_datetime(frame["played_at"], errors="coerce")

    # NumPy demonstrates vectorized calculation: every row is evaluated at
    # once, and a zero-death game uses denominator 1 to avoid division by zero.
    team_games["kill_death_ratio"] = np.divide(
        team_games["kills"].to_numpy(dtype=float),
        np.maximum(team_games["deaths"].to_numpy(dtype=float), 1.0),
    )
    return team_games, player_games


def inspect_dataframe(frame: pd.DataFrame, name: str) -> dict[str, Any]:
    """Create the equivalent of ``shape``, ``info`` and duplicate checks."""

    return {
        "name": name,
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "duplicate_rows": int(frame.duplicated().sum()),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_values": {column: int(value) for column, value in frame.isna().sum().items()},
        "unique_values": {column: int(frame[column].nunique(dropna=True)) for column in frame.columns},
    }


def numeric_summary(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return descriptive statistics plus skewness and kurtosis.

    Skewness describes asymmetry. Kurtosis indicates how heavy the tails are.
    Both are descriptive signals only; they do not automatically mean that a
    valid esports performance should be removed.
    """

    available = [column for column in columns if column in frame.columns]
    summary = frame[available].describe().T.rename(
        columns={"25%": "q1", "50%": "median", "75%": "q3"}
    )
    summary["missing"] = frame[available].isna().sum()
    summary["skewness"] = frame[available].skew(numeric_only=True)
    summary["kurtosis"] = frame[available].kurtosis(numeric_only=True)
    return summary.reset_index(names="metric")


def iqr_outlier_summary(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Flag potential outliers using the transparent 1.5 × IQR rule.

    This function only reports candidates.  It never deletes them because a
    very high DPM or KDA can be a genuine standout match rather than bad data.
    """

    rows: list[dict[str, Any]] = []
    for column in columns:
        if column not in frame.columns:
            continue
        values = frame[column].dropna()
        if values.empty:
            continue
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        candidate_count = int(((values < lower) | (values > upper)).sum())
        rows.append(
            {
                "metric": column,
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower),
                "upper_bound": float(upper),
                "candidate_outliers": candidate_count,
                "candidate_rate": candidate_count / len(values),
                "action": "review_only_do_not_auto_delete",
            }
        )
    return pd.DataFrame(rows)


def _missingness_table(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Return one row per column with missing count and percentage."""

    missing = frame.isna().sum()
    return pd.DataFrame(
        {
            "dataset": dataset,
            "column": missing.index,
            "missing_count": missing.values,
            "missing_rate": missing.values / max(len(frame), 1),
        }
    ).sort_values(["missing_rate", "column"], ascending=[False, True])


def run_pandas_eda(config: ProjectConfig, output_root: Path | None = None) -> dict[str, Any]:
    """Run the full beginner EDA workflow and persist auditable tables."""

    root = output_root or config.root
    processed_dir = root / "data" / "processed" / "pandas_eda"
    report_dir = root / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    team_games, player_games = load_analysis_frames(config)
    inspections = [
        inspect_dataframe(team_games, "team_games"),
        inspect_dataframe(player_games, "player_games"),
    ]

    missingness = pd.concat(
        [
            _missingness_table(team_games, "team_games"),
            _missingness_table(player_games, "player_games"),
        ],
        ignore_index=True,
    )
    team_numeric = numeric_summary(team_games, TEAM_NUMERIC_COLUMNS + ["kill_death_ratio"])
    player_numeric = numeric_summary(player_games, PLAYER_NUMERIC_COLUMNS)
    outliers = pd.concat(
        [
            iqr_outlier_summary(team_games, ["kills", "gpm", "gdm", "dpm", "csd15"]),
            iqr_outlier_summary(player_games, ["kda", "csm", "dpm", "csd15", "gd15", "xpd15"]),
        ],
        keys=["team_games", "player_games"],
        names=["dataset", "row"],
    ).reset_index(level="dataset").reset_index(drop=True)

    # Categorical-vs-categorical: side and match result.  Counts and row
    # percentages are both kept so a percentage is never shown without its n.
    side_counts = pd.crosstab(team_games["side"], team_games["win"])
    side_percent = pd.crosstab(team_games["side"], team_games["win"], normalize="index")
    side_crosstab = side_counts.add_prefix("count_win_").join(side_percent.add_prefix("rate_win_")).reset_index()

    # Numerical-vs-categorical: role profiles expose why raw KDA/DPM should
    # not be compared directly across roles such as SUPPORT and BOT.
    role_summary = (
        player_games.groupby("role", observed=True)
        .agg(
            games=("game_id", "count"),
            players=("player_id", "nunique"),
            median_kda=("kda", "median"),
            mean_dpm=("dpm", "mean"),
            median_dpm=("dpm", "median"),
            mean_csd15=("csd15", "mean"),
            mean_gd15=("gd15", "mean"),
            mean_vision_per_minute=("vision_score_per_minute", "mean"),
        )
        .reset_index()
    )

    tournament_summary = (
        team_games.assign(tournament_type=team_games["tournament_type"].fillna("unknown"))
        .groupby(["team_name", "tournament_type"], observed=True)
        .agg(games=("game_id", "count"), wins=("win", "sum"), avg_gpm=("gpm", "mean"), avg_gdm=("gdm", "mean"))
        .reset_index()
    )
    tournament_summary["win_rate"] = tournament_summary["wins"] / tournament_summary["games"]

    correlation_columns = [
        column
        for column in ["win", "kills", "deaths", "gpm", "gdm", "dpm", "gd15", "csd15", "first_blood", "first_tower", "dragons", "nashors", "towers"]
        if column in team_games.columns
    ]
    correlation = team_games[correlation_columns].corr(numeric_only=True)

    outputs: dict[str, pd.DataFrame] = {
        "missingness.csv": missingness,
        "team_numeric_summary.csv": team_numeric,
        "player_numeric_summary.csv": player_numeric,
        "iqr_outlier_candidates.csv": outliers,
        "side_outcome_crosstab.csv": side_crosstab,
        "role_summary.csv": role_summary,
        "tournament_summary.csv": tournament_summary,
        "team_metric_correlation.csv": correlation.reset_index(names="metric"),
    }
    for filename, frame in outputs.items():
        frame.to_csv(processed_dir / filename, index=False, encoding="utf-8")

    report = {
        "phase": "Pandas EDA upgrade",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "season": config.season,
        "source": "Gol.gg via local SQLite",
        "inspections": inspections,
        "outputs": [(processed_dir / filename).relative_to(root).as_posix() for filename in outputs],
        "methodology": [
            "No missing metric is silently imputed.",
            "IQR identifies review candidates; it does not auto-delete genuine standout games.",
            "Every percentage table keeps its count denominator.",
            "Role summaries are required before comparing player metrics across roles.",
        ],
    }
    json_path = report_dir / "pandas-eda-phase.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown = [
        "# Pandas EDA Upgrade",
        "",
        f"- Run at: `{report['run_at']}`",
        f"- Season: `{config.season}` from `{config.season_start_date}`",
        f"- Team-game rows: `{len(team_games)}`; player-game rows: `{len(player_games)}`",
        "",
        "## Workflow",
        "",
        "Load → inspect → dtype/date → missing/duplicate → descriptive statistics → IQR review → categorical comparison → correlation.",
        "",
        "## Important interpretation rules",
        "",
        *[f"- {item}" for item in report["methodology"]],
        "",
        "## Generated tables",
        "",
        *[f"- `{path}`" for path in report["outputs"]],
    ]
    (report_dir / "pandas-eda-phase.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return report
