"""Route visualization to Matplotlib/Seaborn or an honest SVG fallback."""

from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path
from typing import Any

from ..config import ProjectConfig
from ..storage.database import connect_database, initialize_database
from .metrics import champion_pool, rolling_form, team_side_summary, team_summary


# Keep Matplotlib's font/config cache inside the writable project.  This avoids
# a Windows permission warning when VS Code/Codex runs with a restricted home.
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(__file__).resolve().parents[2] / ".matplotlib-cache"),
)


def _svg_text(value: Any) -> str:
    """Escape a dynamic label before inserting it into SVG markup."""

    return escape(str(value), quote=True)


def _svg_frame(title: str, subtitle: str, body: str, width: int = 1000, height: int = 560) -> str:
    """Wrap chart marks in a consistent dependency-free SVG canvas."""

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f8fafc"/><text x="48" y="48" font-family="Arial,sans-serif" font-size="25" font-weight="700" fill="#0f172a">{_svg_text(title)}</text>
<text x="48" y="76" font-family="Arial,sans-serif" font-size="13" fill="#475569">{_svg_text(subtitle)}</text>{body}
<text x="48" y="540" font-family="Arial,sans-serif" font-size="11" fill="#64748b">Source: Gol.gg · Season S16 · cutoff 2026-01-01 onward · descriptive sample</text></svg>'''


def _svg_bar_chart(
    path: Path,
    title: str,
    subtitle: str,
    labels: list[str],
    values: list[float],
    value_format: str = "{:.1%}",
    annotations: list[str] | None = None,
    colors: list[str] | None = None,
) -> None:
    """Write a basic bar chart for environments without plotting packages."""

    width, left, right, top, bottom = 1000, 70, 35, 115, 90
    chart_width = width - left - right
    chart_height = 560 - top - bottom
    maximum = max(values) if values else 1
    maximum = maximum if maximum > 0 else 1
    step = chart_width / max(len(values), 1)
    bar_width = min(58, step * 0.68)
    pieces = [
        f'<line x1="{left}" y1="{top + chart_height}" x2="{width - right}" y2="{top + chart_height}" stroke="#94a3b8"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" stroke="#94a3b8"/>',
    ]
    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + index * step + (step - bar_width) / 2
        height = max(2, value / maximum * chart_height)
        y = top + chart_height - height
        color = colors[index] if colors and index < len(colors) else "#2563eb"
        annotation = annotations[index] if annotations and index < len(annotations) else value_format.format(value)
        pieces.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{height:.1f}" rx="4" fill="{color}"/>'
            f'<text x="{x + bar_width / 2:.1f}" y="{max(top - 4, y - 7):.1f}" text-anchor="middle" font-family="Arial" font-size="11" fill="#0f172a">{_svg_text(annotation)}</text>'
        )
        pieces.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{top + chart_height + 22}" text-anchor="end" transform="rotate(-42 {x + bar_width / 2:.1f},{top + chart_height + 22})" font-family="Arial" font-size="11" fill="#334155">{_svg_text(label)}</text>'
        )
    path.write_text(_svg_frame(title, subtitle, "".join(pieces)), encoding="utf-8")


def _generate_svg_fallback(config: ProjectConfig, output_dir: Path, report_dir: Path) -> dict[str, Any]:
    """Produce eight SVG figures while reporting their reduced fidelity."""

    connection = connect_database(initialize_database(config))
    try:
        teams = team_summary(connection)
        sides = team_side_summary(connection)
        champions = champion_pool(connection)
        rolling = rolling_form(connection)
    finally:
        connection.close()

    figures: list[str] = []

    def add_bar(
        filename: str,
        title: str,
        subtitle: str,
        rows: list[dict[str, Any]],
        label_key: str,
        value_key: str,
        color: str,
        value_format: str = "{:.1f}",
        annotations: list[str] | None = None,
    ) -> None:
        """Avoid repeating the same file-registration boilerplate."""

        if not rows:
            return
        path = output_dir / filename
        _svg_bar_chart(
            path,
            title,
            subtitle,
            [str(row[label_key]) for row in rows],
            [float(row.get(value_key) or 0) for row in rows],
            value_format=value_format,
            annotations=annotations,
            colors=[color] * len(rows),
        )
        figures.append(path.relative_to(report_dir.parent).as_posix())

    ordered = sorted(teams, key=lambda row: row.get("win_rate") or 0, reverse=True)
    add_bar(
        "team_win_rate.svg",
        "S16 LCK team win rate",
        "Win rate with the denominator above every bar",
        ordered,
        "canonical_name",
        "win_rate",
        "#2563eb",
        annotations=[f"n={row['games']} · {(row.get('win_rate') or 0):.0%}" for row in ordered],
    )
    gpm_rows = sorted([row for row in teams if row.get("avg_gpm") is not None], key=lambda row: row["avg_gpm"], reverse=True)
    add_bar("team_gpm.svg", "Average team gold per minute", "Economy comparison; interpret alongside sample size", gpm_rows, "canonical_name", "avg_gpm", "#16a34a", "{:.0f}")
    objective_rows = sorted([row for row in teams if row.get("avg_towers") is not None], key=lambda row: row["avg_towers"], reverse=True)
    add_bar("objective_control.svg", "Average objective control", "Average towers per game", objective_rows, "canonical_name", "avg_towers", "#ea580c")
    combat_rows = sorted([row for row in teams if row.get("avg_kills") is not None], key=lambda row: row["avg_kills"], reverse=True)
    add_bar("team_combat_kills.svg", "Average team kills", "Combat output; interpret with sample size", combat_rows, "canonical_name", "avg_kills", "#0891b2")
    early_rows = sorted([row for row in teams if row.get("first_tower_rate") is not None], key=lambda row: row["first_tower_rate"], reverse=True)
    add_bar("early_objective_rate.svg", "First-tower rate", "Early objective signal; not causal evidence", early_rows, "canonical_name", "first_tower_rate", "#9333ea", "{:.0%}")
    add_bar("champion_pool_usage.svg", "Champion pool usage", "Ranked by games, not small-sample win rate", champions[:15], "champion_name", "games", "#7c3aed", "{:.0f}")

    if sides:
        labels = [f"{row['team_id']} · {row['side']}" for row in sides]
        path = output_dir / "side_win_rate.svg"
        _svg_bar_chart(
            path,
            "Blue/red side win rate",
            "Side performance by team; n shown above every bar",
            labels,
            [float(row.get("win_rate") or 0) for row in sides],
            annotations=[f"n={row['games']} · {(row.get('win_rate') or 0):.0%}" for row in sides],
            colors=["#2563eb" if row["side"] == "blue" else "#dc2626" for row in sides],
        )
        figures.append(path.relative_to(report_dir.parent).as_posix())

    if rolling:
        team_id = rolling[0]["team_id"]
        rows = [row for row in rolling if row["team_id"] == team_id]
        points = []
        for index, row in enumerate(rows):
            x = 100 + index * (800 / max(len(rows) - 1, 1))
            y = 430 - (row.get("rolling_5_games_win_rate") or 0) * 270
            points.append(f"{x:.1f},{y:.1f}")
        body = (
            '<line x1="70" y1="430" x2="930" y2="430" stroke="#94a3b8"/>'
            '<line x1="70" y1="160" x2="70" y2="430" stroke="#94a3b8"/>'
            '<polyline fill="none" stroke="#2563eb" stroke-width="3" points="'
            + " ".join(points)
            + '"/><text x="75" y="150" font-family="Arial" font-size="12" fill="#334155">rolling 5-game win rate</text>'
        )
        path = output_dir / "rolling_form.svg"
        path.write_text(_svg_frame(f"Rolling form — team {team_id}", "Recent-form trajectory", body), encoding="utf-8")
        figures.append(path.relative_to(report_dir.parent).as_posix())

    report = {
        "status": "fallback",
        "renderer": "stdlib-svg",
        "figures": figures,
        "source": "Gol.gg",
        "season": config.season,
        "cutoff": config.season_start_date,
        "limitations": [
            "This proves the data-to-figure flow but not the final Matplotlib/Seaborn requirement.",
            "Run again after completing the scientific environment to create the 12+ chart suite.",
        ],
    }
    (report_dir / "visualization-phase-8.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def generate_visualizations(
    config: ProjectConfig,
    output_root: Path | None = None,
    team_a_id: int | None = None,
    team_b_id: int | None = None,
) -> dict[str, Any]:
    """Generate rich figures when possible and an explicit fallback otherwise."""

    report_dir = (output_root or config.root) / "reports"
    output_dir = report_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib  # noqa: F401 - an intentional availability check
        import seaborn  # noqa: F401 - rich mode requires both libraries
    except ModuleNotFoundError as exc:
        report = _generate_svg_fallback(config, output_dir, report_dir)
        report["reason"] = f"Scientific renderer unavailable: {exc}"
        (report_dir / "visualization-phase-8.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    from .scientific_visualizations import generate_scientific_visualizations

    return generate_scientific_visualizations(config, output_root, team_a_id, team_b_id)
