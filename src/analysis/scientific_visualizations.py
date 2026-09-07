"""Matplotlib/Seaborn visualization suite for the S16 academic demo.

The figure set follows the reference Colab's EDA progression:

* data coverage;
* univariate numerical distributions;
* categorical frequencies;
* numerical-vs-numerical relationships;
* numerical-vs-categorical comparisons;
* categorical-vs-categorical comparisons;
* multivariate and time-based views.

Every chart is tied to a LoL analysis question.  The goal is not to display as
many chart types as possible; it is to choose a visual encoding that makes a
specific comparison easier to understand.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ProjectConfig
from .pandas_eda import load_analysis_frames


TEAM_METRICS = {
    "win_rate": "Win rate",
    "avg_gpm": "GPM",
    "avg_gdm": "GDM",
    "avg_kills": "Kills",
    "first_tower_rate": "First tower",
    "avg_dragons": "Dragons",
    "avg_nashors": "Nashors",
}


def _safe_zscore(frame: Any) -> Any:
    """Standardize columns; keep a constant column at zero instead of NaN."""

    standard_deviation = frame.std(ddof=0).replace(0, 1)
    return (frame - frame.mean()) / standard_deviation


def _team_aggregate(team_games: Any) -> Any:
    """Create one auditable row per primary LCK team."""

    grouped = (
        team_games.groupby(["team_id", "team_name"], observed=True)
        .agg(
            games=("game_id", "count"),
            wins=("win", "sum"),
            avg_gpm=("gpm", "mean"),
            avg_gdm=("gdm", "mean"),
            avg_kills=("kills", "mean"),
            avg_deaths=("deaths", "mean"),
            first_tower_rate=("first_tower", "mean"),
            avg_dragons=("dragons", "mean"),
            avg_nashors=("nashors", "mean"),
        )
        .reset_index()
    )
    grouped["win_rate"] = grouped["wins"] / grouped["games"]
    return grouped


def _figure_note(config: ProjectConfig, sample: str) -> str:
    """Return a consistent, short provenance note for every figure."""

    return f"Source: Gol.gg · {config.season} from {config.season_start_date} · {sample}"


def generate_scientific_visualizations(
    config: ProjectConfig,
    output_root: Path | None = None,
    team_a_id: int | None = None,
    team_b_id: int | None = None,
) -> dict[str, Any]:
    """Render the full scientific figure set and return a detailed manifest.

    Parameters are optional because the global EDA should always run.  When
    both team IDs are supplied, two additional context-specific comparison
    figures are created for the requested matchup.
    """

    # Imports stay inside the function so the scraper/quality workflow still
    # works in a minimal environment and can report a clear plotting fallback.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns

    root = output_root or config.root
    report_dir = root / "reports"
    output_dir = report_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    team_games, player_games = load_analysis_frames(config)
    team_stats = _team_aggregate(team_games)

    sns.set_theme(style="whitegrid", context="notebook")
    palette = {
        "navy": "#17324D",
        "blue": "#2F6BFF",
        "cyan": "#16A6B6",
        "gold": "#E3A008",
        "red": "#D94A4A",
        "muted": "#667085",
    }
    artifacts: list[dict[str, Any]] = []

    def save(fig: Any, filename: str, question: str, chart_type: str, sample: str) -> None:
        """Save, close and register one figure in the reproducibility manifest."""

        path = output_dir / filename
        fig.text(0.01, 0.005, _figure_note(config, sample), fontsize=8, color=palette["muted"])
        fig.tight_layout(rect=(0, 0.035, 1, 1))
        fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        artifacts.append(
            {
                "file": path.relative_to(root).as_posix(),
                "question": question,
                "chart_type": chart_type,
                "sample": sample,
            }
        )

    # 1) Data coverage mirrors the Colab missing-data inspection but aggregates
    # percentages. A 6,000-column-wide raw missing heatmap would be unreadable.
    # A blank cell means the metric is not defined at that grain.  It must not
    # be shown as 100% missing, which would confuse “not applicable” with a
    # failed parser.
    coverage_specs = {
        "Team-game": (team_games, ["gpm", "gdm", "dpm", "csm", "gd15", "csd15", "dragons", "nashors"]),
        "Player-game": (player_games, ["dpm", "csm", "gd15", "csd15", "vision_score_per_minute"]),
    }
    coverage_index = ["gpm", "gdm", "dpm", "csm", "gd15", "csd15", "dragons", "nashors", "vision_score_per_minute"]
    coverage = pd.DataFrame(index=coverage_index, columns=coverage_specs, dtype=float)
    for dataset, (frame, relevant_columns) in coverage_specs.items():
        for column in relevant_columns:
            coverage.loc[column, dataset] = float(frame[column].isna().mean())
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(coverage * 100, mask=coverage.isna(), annot=True, fmt=".1f", cmap="YlOrRd", vmin=0, vmax=100, ax=ax, cbar_kws={"label": "Missing (%)"})
    ax.set_title("Dữ liệu nào đủ để phân tích?", loc="left", weight="bold")
    ax.set_xlabel("Dataset grain")
    ax.set_ylabel("Metric")
    save(fig, "01_missingness_heatmap.png", "Metric nào còn thiếu dữ liệu?", "aggregated missingness heatmap", f"team n={len(team_games)}, player n={len(player_games)}")

    # 2) A lollipop chart is lighter than another filled bar chart and keeps
    # the exact denominator beside each team.
    ordered = team_stats.sort_values("win_rate")
    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(ordered))
    ax.hlines(y, 0, ordered["win_rate"], color="#C7D2E3", linewidth=2)
    ax.scatter(ordered["win_rate"], y, s=95, color=palette["blue"], zorder=3)
    ax.set_yticks(y, ordered["team_name"])
    ax.set_xlim(0, max(0.75, float(ordered["win_rate"].max()) + 0.08))
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlabel("Win rate")
    ax.set_ylabel("")
    ax.set_title("Đội nào có tỷ lệ thắng S16 cao nhất?", loc="left", weight="bold")
    for position, (_, row) in enumerate(ordered.iterrows()):
        ax.text(row["win_rate"] + 0.012, position, f"{row['win_rate']:.1%} · n={int(row['games'])}", va="center", fontsize=9)
    sns.despine(ax=ax, left=True)
    save(fig, "02_team_win_rate_lollipop.png", "Đội nào có tỷ lệ thắng cao nhất?", "lollipop", f"{int(team_stats['games'].sum())} primary-team game rows")

    # 3) Numerical-vs-numerical: economy against result with sample encoded as
    # bubble size. Labels make the chart useful without a separate legend map.
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=team_stats, x="avg_gpm", y="win_rate", size="games", sizes=(100, 320), color=palette["cyan"], edgecolor="white", linewidth=1.2, legend=False, ax=ax)
    for _, row in team_stats.iterrows():
        ax.annotate(row["team_name"], (row["avg_gpm"], row["win_rate"]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlabel("Average GPM")
    ax.set_ylabel("Win rate")
    ax.set_title("Tạo vàng nhanh có đi cùng thắng nhiều hơn không?", loc="left", weight="bold")
    save(fig, "03_economy_vs_win_scatter.png", "GPM và win rate có quan hệ như thế nào?", "annotated bubble scatter", f"10 teams, bubble size = games")

    # 4) Multivariate overview: z-score is used only for comparison because the
    # source metrics have incompatible units such as percentages and gold/min.
    heatmap_source = team_stats.set_index("team_name")[list(TEAM_METRICS)]
    heatmap_z = _safe_zscore(heatmap_source)
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.heatmap(heatmap_z, cmap="vlag", center=0, annot=True, fmt=".1f", linewidths=0.5, ax=ax, cbar_kws={"label": "Z-score trong 10 đội"})
    ax.set_xticklabels([TEAM_METRICS[column] for column in heatmap_z.columns], rotation=25, ha="right")
    ax.set_title("Hồ sơ điểm mạnh/yếu tương đối của 10 đội", loc="left", weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    save(fig, "04_team_metric_profile_heatmap.png", "Mỗi đội nổi trội ở nhóm metric nào?", "standardized heatmap", "10 primary teams; standardized per metric")

    # 5) Numerical-vs-categorical: boxplots show spread, median and outliers;
    # this is more honest than comparing only one average DPM per role.
    role_order = ["TOP", "JUNGLE", "MID", "BOT", "SUPPORT"]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=player_games, x="role", y="dpm", order=role_order, hue="role", palette="Set2", legend=False, showfliers=False, ax=ax)
    ax.set_title("DPM phân bố khác nhau thế nào giữa các role?", loc="left", weight="bold")
    ax.set_xlabel("Role")
    ax.set_ylabel("Damage per minute")
    save(fig, "05_player_dpm_boxplot_by_role.png", "DPM distribution khác nhau theo role ra sao?", "boxplot", f"{len(player_games)} current-starter game rows")

    # 6) Violin reveals density shape. Display is clipped at the 99th
    # percentile only; underlying rows are neither deleted nor modified.
    kda_display = player_games[["role", "kda"]].dropna().copy()
    kda_cap = float(kda_display["kda"].quantile(0.99))
    kda_display["kda_display"] = kda_display["kda"].clip(upper=kda_cap)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(data=kda_display, x="role", y="kda_display", order=role_order, hue="role", palette="pastel", legend=False, inner="quartile", cut=0, ax=ax)
    ax.set_title("KDA có cùng dạng phân phối ở mọi role không?", loc="left", weight="bold")
    ax.set_xlabel("Role")
    ax.set_ylabel(f"KDA (display clipped at p99={kda_cap:.1f})")
    save(fig, "06_player_kda_violin_by_role.png", "KDA distribution khác nhau theo role ra sao?", "violin plot", f"{len(kda_display)} rows; display-only p99 clipping")

    # 7) Categorical-vs-categorical: a 100% stacked bar answers the side question
    # directly while retaining the raw count annotations.
    side_counts = pd.crosstab(team_games["side"], team_games["win"]).reindex(columns=[0, 1], fill_value=0)
    side_rates = side_counts.div(side_counts.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(side_rates.index, side_rates[0], label="Loss", color="#D8DEE9")
    ax.bar(side_rates.index, side_rates[1], bottom=side_rates[0], label="Win", color=palette["blue"])
    for index, side in enumerate(side_rates.index):
        ax.text(index, side_rates.loc[side, 0] / 2, f"{side_counts.loc[side, 0]} losses", ha="center", va="center", fontsize=9)
        ax.text(index, side_rates.loc[side, 0] + side_rates.loc[side, 1] / 2, f"{side_counts.loc[side, 1]} wins", ha="center", va="center", color="white", fontsize=9, weight="bold")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of outcomes")
    ax.set_xlabel("Side")
    ax.set_title("Blue và red side có outcome khác nhau trong mẫu S16?", loc="left", weight="bold")
    ax.legend(frameon=False, ncol=2, loc="upper center")
    save(fig, "07_side_outcome_stacked.png", "Side và match result liên hệ mô tả ra sao?", "100% stacked bar", f"n={len(team_games)} team-game rows")

    # 8) Correlation is a hypothesis generator, never a causal conclusion.
    corr_columns = ["win", "kills", "deaths", "gpm", "gdm", "dpm", "gd15", "csd15", "first_blood", "first_tower", "dragons", "nashors", "towers"]
    correlation = team_games[corr_columns].corr(numeric_only=True)
    mask = np.triu(np.ones_like(correlation, dtype=bool), k=1)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(correlation, mask=mask, cmap="vlag", center=0, vmin=-1, vmax=1, annot=True, fmt=".2f", square=True, linewidths=0.4, ax=ax, cbar_kws={"label": "Pearson r"})
    ax.set_title("Các team metrics biến thiên cùng nhau như thế nào?", loc="left", weight="bold")
    save(fig, "08_team_correlation_heatmap.png", "Metric nào có tương quan tuyến tính?", "lower-triangle correlation heatmap", f"n={len(team_games)}; correlation is not causation")

    # 9) Sequential small multiples avoid ten overlapping lines.  Game order is
    # used instead of calendar time because drawing a line across a six-week
    # break with no games would visually imply a trend that was never observed.
    form = team_games.sort_values(["team_name", "played_at", "game_id"]).copy()
    form["rolling_win_rate_5"] = form.groupby("team_name", observed=True)["win"].transform(lambda series: series.rolling(5, min_periods=1).mean())
    form["game_order"] = form.groupby("team_name", observed=True).cumcount() + 1
    names = sorted(form["team_name"].unique())
    fig, axes = plt.subplots(5, 2, figsize=(13, 14), sharey=True)
    for ax, name in zip(axes.flat, names):
        rows = form[form["team_name"] == name]
        ax.step(rows["game_order"], rows["rolling_win_rate_5"], where="post", color=palette["blue"], linewidth=1.8)
        ax.axhline(0.5, color="#AAB2BF", linestyle="--", linewidth=0.8)
        ax.set_title(name, loc="left", fontsize=10, weight="bold")
        ax.set_ylim(0, 1)
        ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        ax.set_xlabel("Thứ tự game S16", fontsize=8)
        ax.tick_params(axis="x", labelsize=7)
    fig.suptitle("Phong độ rolling 5 game thay đổi thế nào theo thứ tự trận?", x=0.06, ha="left", weight="bold", fontsize=15)
    save(fig, "09_rolling_form_small_multiples.png", "Recent form của 10 đội biến động ra sao?", "sequential small multiples", "10 teams; rolling window=5; x=game order")

    # 10) Champion pool: games is x, win rate is y and bubble size is average
    # DPM. Only champions with a useful denominator are labeled.
    champion = (
        player_games.dropna(subset=["champion_name"])
        .groupby("champion_name", observed=True)
        .agg(games=("game_id", "count"), wins=("win", "sum"), avg_dpm=("dpm", "mean"))
        .reset_index()
    )
    champion["win_rate"] = champion["wins"] / champion["games"]
    champion = champion[champion["games"] >= 8].sort_values("games", ascending=False).head(25)
    if not champion.empty:
        fig, ax = plt.subplots(figsize=(11, 7))
        sizes = 70 + 260 * (champion["avg_dpm"] - champion["avg_dpm"].min()) / max(float(champion["avg_dpm"].max() - champion["avg_dpm"].min()), 1.0)
        ax.scatter(champion["games"], champion["win_rate"], s=sizes, color=palette["gold"], alpha=0.72, edgecolor="white")
        for _, row in champion.head(15).iterrows():
            ax.annotate(row["champion_name"], (row["games"], row["win_rate"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
        ax.axhline(0.5, color="#AAB2BF", linestyle="--", linewidth=1)
        ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        ax.set_xlabel("Games picked by current LCK starters")
        ax.set_ylabel("Win rate")
        ax.set_title("Champion nào vừa được dùng đủ nhiều vừa có kết quả tốt?", loc="left", weight="bold")
        save(fig, "10_champion_pool_bubble.png", "Champion usage và win rate cân bằng thế nào?", "bubble scatter", f"champions with n>=8; size=average DPM")

    # 11) Domestic/international is a compact categorical grouping that uses
    # the international events requested as supporting evidence.
    tournament = (
        team_games.assign(tournament_type=team_games["tournament_type"].fillna("unknown"))
        .groupby(["team_name", "tournament_type"], observed=True)
        .agg(games=("game_id", "count"), win_rate=("win", "mean"))
        .reset_index()
    )
    tournament_pivot = tournament.pivot(index="team_name", columns="tournament_type", values="win_rate")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(tournament_pivot * 100, annot=True, fmt=".1f", cmap="YlGnBu", vmin=0, vmax=100, linewidths=0.5, ax=ax, cbar_kws={"label": "Win rate (%)"})
    ax.set_title("Phong độ nội địa và quốc tế có khác nhau?", loc="left", weight="bold")
    ax.set_xlabel("Tournament type")
    ax.set_ylabel("")
    save(fig, "11_tournament_context_heatmap.png", "Đội thể hiện khác nhau theo loại giải ra sao?", "grouped heatmap", "all official S16 tournaments involving primary LCK teams")

    # 12) Role baselines explain why cross-role raw comparison is invalid.
    role_profile = (
        player_games.groupby("role", observed=True)
        .agg(kda=("kda", "median"), csm=("csm", "mean"), dpm=("dpm", "mean"), gd15=("gd15", "mean"), vision=("vision_score_per_minute", "mean"))
        .reindex(role_order)
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(_safe_zscore(role_profile), cmap="vlag", center=0, annot=True, fmt=".1f", linewidths=0.5, ax=ax, cbar_kws={"label": "Z-score across roles"})
    ax.set_title("Vì sao không nên so raw stats giữa hai role khác nhau?", loc="left", weight="bold")
    ax.set_xlabel("Role-level metric profile")
    ax.set_ylabel("")
    save(fig, "12_role_baseline_heatmap.png", "Baseline metric khác nhau tự nhiên theo role thế nào?", "standardized role heatmap", f"{len(player_games)} current-starter game rows")

    # Optional matchup figure: a dumbbell is ideal for comparing exactly two
    # objects across repeated fields, provided values are standardized first.
    if team_a_id is not None and team_b_id is not None:
        selected = team_stats[team_stats["team_id"].isin([team_a_id, team_b_id])].copy()
        if len(selected) == 2:
            standardized = _safe_zscore(team_stats.set_index("team_name")[list(TEAM_METRICS)])
            names_by_id = dict(zip(selected["team_id"], selected["team_name"]))
            name_a, name_b = names_by_id[team_a_id], names_by_id[team_b_id]
            a_values = standardized.loc[name_a]
            b_values = standardized.loc[name_b]
            labels = [TEAM_METRICS[column] for column in standardized.columns]
            y = np.arange(len(labels))
            fig, ax = plt.subplots(figsize=(10, 6))
            for index in range(len(labels)):
                ax.plot([a_values.iloc[index], b_values.iloc[index]], [index, index], color="#C7D2E3", linewidth=2)
            ax.scatter(a_values, y, color=palette["blue"], s=90, label=name_a, zorder=3)
            ax.scatter(b_values, y, color=palette["red"], s=90, label=name_b, zorder=3)
            ax.axvline(0, color="#98A2B3", linestyle="--", linewidth=1)
            ax.set_yticks(y, labels)
            ax.set_xlabel("Z-score trong 10 đội")
            ax.set_ylabel("")
            ax.set_title(f"{name_a} và {name_b}: lợi thế tương đối nằm ở đâu?", loc="left", weight="bold")
            ax.legend(frameon=False)
            save(fig, "13_selected_team_dumbbell.png", "Hai đội khác nhau ở feature nào?", "standardized dumbbell", f"team IDs {team_a_id} vs {team_b_id}")

            # Same-role player z-scores create a fairer role matchup view.
            player_means = (
                player_games.groupby(["player_id", "player_name", "team_id", "role"], observed=True)
                .agg(kda=("kda", "mean"), dpm=("dpm", "mean"), csm=("csm", "mean"), gd15=("gd15", "mean"), csd15=("csd15", "mean"), vision=("vision_score_per_minute", "mean"))
                .reset_index()
            )
            metric_columns = ["kda", "dpm", "csm", "gd15", "csd15", "vision"]
            z_parts = []
            for _, role_rows in player_means.groupby("role", observed=True):
                normalized = role_rows.copy()
                normalized[metric_columns] = _safe_zscore(role_rows[metric_columns])
                z_parts.append(normalized)
            player_z = pd.concat(z_parts, ignore_index=True)
            matchup = player_z[player_z["team_id"].isin([team_a_id, team_b_id])].copy()
            matchup["label"] = matchup["role"] + " · " + matchup["player_name"]
            matchup = matchup.sort_values(["role", "team_id"])
            if not matchup.empty:
                fig, ax = plt.subplots(figsize=(10, max(6, len(matchup) * 0.45)))
                sns.heatmap(matchup.set_index("label")[metric_columns], cmap="vlag", center=0, annot=True, fmt=".1f", linewidths=0.4, ax=ax, cbar_kws={"label": "Z-score within role"})
                ax.set_title("Đối đầu cùng vị trí: ai nổi trội so với baseline role?", loc="left", weight="bold")
                ax.set_xlabel("Metric normalized within role")
                ax.set_ylabel("")
                save(fig, "14_role_matchup_heatmap.png", "Từng cặp cùng role có điểm mạnh/yếu nào?", "within-role standardized heatmap", f"current starters for team IDs {team_a_id} vs {team_b_id}")

    report = {
        "status": "ok",
        "renderer": "matplotlib-seaborn",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "source": "Gol.gg via local SQLite",
        "season": config.season,
        "cutoff_start": config.season_start_date,
        "team_game_rows": int(len(team_games)),
        "player_game_rows": int(len(player_games)),
        "selected_team_ids": [team_a_id, team_b_id] if team_a_id is not None and team_b_id is not None else [],
        "figures": artifacts,
        "interpretation_rules": [
            "Percentages are presented with sample size.",
            "Outlier clipping is display-only and never mutates source data.",
            "Correlation is descriptive, not causal.",
            "Cross-role raw player metrics are not used for ability ranking.",
            "Champion win rate requires a minimum game denominator in the bubble view.",
        ],
    }
    report_path = report_dir / "visualization-phase-8.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
