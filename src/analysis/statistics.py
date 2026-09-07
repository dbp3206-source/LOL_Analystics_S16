"""Beginner-friendly statistical evidence for the S16 analysis.

This module deliberately separates three ideas that beginners often mix up:

1. a point estimate (for example, a 63% observed win rate);
2. uncertainty around that estimate (the Wilson confidence interval);
3. an exploratory hypothesis test (a p-value).

The SciPy and Statsmodels tests are optional.  The core report still runs when
those packages are unavailable, which keeps the project demoable on a minimal
VS Code environment.  None of the tests below establishes causality or replaces
the leakage-safe prediction backtest in ``src/modeling/backtest.py``.
"""

from __future__ import annotations

import importlib.util
import json
import math
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable

from ..config import ProjectConfig
from ..storage.database import connect_database, initialize_database


LIMITATIONS = [
    "Các kiểm định mang tính quan sát/thăm dò, không chứng minh quan hệ nhân quả.",
    "P-value không phải xác suất thắng và không thay thế mô hình dự đoán/backtest.",
    "So sánh thô chưa kiểm soát đầy đủ sức mạnh đối thủ, lịch thi đấu chồng lặp, thời gian và meta/patch.",
    "Bảng side × outcome chứa hai phía ghép cặp của cùng game, nên không thỏa hoàn toàn giả định quan sát độc lập của chi-square.",
]


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float | None, float | None]:
    """Return a Wilson score interval for a binomial rate.

    Wilson is preferred over the simple ``p ± 1.96 * standard_error`` formula
    because it behaves better with small samples or rates near zero/one.
    """

    if trials <= 0:
        return None, None
    if successes < 0 or successes > trials:
        raise ValueError("successes must satisfy 0 <= successes <= trials")

    rate = successes / trials
    denominator = 1 + (z * z / trials)
    center = (rate + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt((rate * (1 - rate) / trials) + z * z / (4 * trials * trials)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def binomial_summary(successes: int, trials: int, confidence: float = 0.95) -> dict[str, Any]:
    """Package a win rate, Wilson interval and an easy-to-read warning."""

    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    # NormalDist is in Python's standard library, so 90% or 99% intervals do
    # not need SciPy.  For 95%, this gives approximately 1.96.
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    low, high = wilson_interval(successes, trials, z=z)
    return {
        "successes": successes,
        "trials": trials,
        "rate": successes / trials if trials else None,
        "confidence": confidence,
        "ci_low": low,
        "ci_high": high,
        # A threshold of 30 is a teaching heuristic, not a universal law.
        "small_sample_warning": trials < 30,
    }


def compare_rates(
    successes_a: int,
    trials_a: int,
    successes_b: int,
    trials_b: int,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Return a descriptive difference between two binomial rates.

    This function intentionally does not call the difference "significant".
    Statistical significance is handled separately by the optional z-test.
    """

    summary_a = binomial_summary(successes_a, trials_a, confidence)
    summary_b = binomial_summary(successes_b, trials_b, confidence)
    difference = None
    if summary_a["rate"] is not None and summary_b["rate"] is not None:
        difference = summary_a["rate"] - summary_b["rate"]
    return {"group_a": summary_a, "group_b": summary_b, "rate_difference_a_minus_b": difference}


def cohens_d(values_a: Iterable[float], values_b: Iterable[float]) -> float | None:
    """Compute Cohen's d using the average of the two sample variances.

    Cohen's d expresses a mean difference in standard-deviation units.  It is
    useful beside a p-value because effect size and statistical evidence answer
    different questions.  Two observations per group are required.
    """

    a = [float(value) for value in values_a]
    b = [float(value) for value in values_b]
    if len(a) < 2 or len(b) < 2:
        return None

    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    var_a = sum((value - mean_a) ** 2 for value in a) / (len(a) - 1)
    var_b = sum((value - mean_b) ** 2 for value in b) / (len(b) - 1)
    pooled_standard_deviation = math.sqrt((var_a + var_b) / 2)
    if pooled_standard_deviation == 0:
        return 0.0 if mean_a == mean_b else None
    return (mean_a - mean_b) / pooled_standard_deviation


def _team_win_rows(connection: Any) -> list[dict[str, Any]]:
    """Load one row per primary LCK team from all official S16 games."""

    rows = connection.execute(
        """SELECT t.team_id, t.canonical_name,
                  COUNT(DISTINCT s.game_id) AS games,
                  COALESCE(SUM(s.win), 0) AS wins
           FROM teams t
           LEFT JOIN team_game_stats s ON s.team_id=t.team_id
           WHERE t.is_lck_primary=1
           GROUP BY t.team_id,t.canonical_name
           ORDER BY t.canonical_name"""
    ).fetchall()
    result = []
    for row in rows:
        games = int(row["games"] or 0)
        wins = int(row["wins"] or 0)
        result.append(
            {
                "team_id": int(row["team_id"]),
                "canonical_name": str(row["canonical_name"]),
                "games": games,
                "wins": wins,
                "confidence_interval": binomial_summary(wins, games),
            }
        )
    return result


def _dependency_status() -> dict[str, bool]:
    """Check optional scientific packages without importing them eagerly."""

    return {
        "scipy": importlib.util.find_spec("scipy") is not None,
        "statsmodels": importlib.util.find_spec("statsmodels") is not None,
    }


def _side_chi_square(connection: Any) -> dict[str, Any]:
    """Test whether side and outcome are associated for primary LCK rows."""

    # Import locally so the whole report remains usable without SciPy.
    from scipy.stats import chi2_contingency

    observed = []
    for side in ("blue", "red"):
        counts = {
            int(row["win"]): int(row["count"])
            for row in connection.execute(
                """SELECT s.win,COUNT(*) AS count
                   FROM team_game_stats s
                   JOIN teams t ON t.team_id=s.team_id AND t.is_lck_primary=1
                   WHERE s.side=? GROUP BY s.win""",
                (side,),
            ).fetchall()
        }
        observed.append([counts.get(0, 0), counts.get(1, 0)])

    if any(sum(row) == 0 for row in observed):
        return {"status": "skipped", "reason": "Cần quan sát ở cả blue side và red side."}

    chi2, p_value, degrees_of_freedom, expected = chi2_contingency(observed)
    expected_list = [[float(value) for value in row] for row in expected]
    expected_count_assumption_ok = all(value >= 5 for row in expected_list for value in row)
    # Every game contributes a blue row and a red row whose outcomes are exact
    # opposites. Therefore those rows are paired, not independent observations.
    independence_assumption_ok = False
    return {
        "status": "assumption_warning",
        "question": "Minh họa crosstab side × outcome; assumption nào ngăn kết luận xác nhận?",
        "rows": ["blue", "red"],
        "columns": ["loss", "win"],
        "observed": observed,
        "expected": expected_list,
        "chi_square": float(chi2),
        "degrees_of_freedom": int(degrees_of_freedom),
        "p_value": float(p_value),
        "assumption_expected_at_least_5": expected_count_assumption_ok,
        "assumption_independent_observations": independence_assumption_ok,
        "interpretation": (
            "Expected counts đạt yêu cầu nhưng quan sát không độc lập vì mỗi game tạo một cặp blue/red đối nghịch. "
            "Chỉ dùng p-value này để minh họa quy trình kiểm tra assumption, không dùng làm kết luận xác nhận."
        ),
    }


def _selected_pair_tests(connection: Any, team_a: dict[str, Any], team_b: dict[str, Any], dependencies: dict[str, bool]) -> dict[str, Any]:
    """Run only the simple, interpretable tests selected for the course scope."""

    team_a_id = int(team_a["team_id"])
    team_b_id = int(team_b["team_id"])
    tests: dict[str, Any] = {
        "team_a": {"team_id": team_a_id, "name": team_a["canonical_name"]},
        "team_b": {"team_id": team_b_id, "name": team_b["canonical_name"]},
        "descriptive_win_rate_difference": compare_rates(
            int(team_a["wins"]), int(team_a["games"]), int(team_b["wins"]), int(team_b["games"])
        ),
    }

    if dependencies["statsmodels"] and team_a["games"] and team_b["games"]:
        from statsmodels.stats.proportion import proportions_ztest

        z_statistic, p_value = proportions_ztest(
            [int(team_a["wins"]), int(team_b["wins"])],
            [int(team_a["games"]), int(team_b["games"])],
        )
        tests["two_proportion_z_test"] = {
            "status": "ok",
            "null_hypothesis": "Hai đội có cùng tỷ lệ thắng tổng thể trong mẫu S16.",
            "z_statistic": float(z_statistic),
            "p_value": float(p_value),
            "interpretation": (
                "Bác bỏ H0 ở ngưỡng 5%; chênh lệch quan sát có bằng chứng thống kê trong mẫu."
                if p_value < 0.05
                else "Chưa đủ bằng chứng để bác bỏ H0 ở ngưỡng 5%."
            ),
        }
    else:
        tests["two_proportion_z_test"] = {
            "status": "skipped",
            "reason": "Thiếu Statsmodels hoặc một đội chưa có trận.",
        }

    gdm_by_team: dict[int, list[float]] = {}
    for team_id in (team_a_id, team_b_id):
        gdm_by_team[team_id] = [
            float(row["gdm"])
            for row in connection.execute(
                "SELECT gdm FROM team_game_stats WHERE team_id=? AND gdm IS NOT NULL",
                (team_id,),
            ).fetchall()
        ]

    values_a = gdm_by_team[team_a_id]
    values_b = gdm_by_team[team_b_id]
    effect_size = cohens_d(values_a, values_b)
    if dependencies["scipy"] and len(values_a) >= 2 and len(values_b) >= 2:
        from scipy.stats import ttest_ind

        statistic, p_value = ttest_ind(values_a, values_b, equal_var=False, nan_policy="omit")
        tests["welch_t_test_gdm"] = {
            "status": "ok",
            "metric": "GDM (gold differential per minute)",
            "samples": {"team_a": len(values_a), "team_b": len(values_b)},
            "mean_team_a": sum(values_a) / len(values_a),
            "mean_team_b": sum(values_b) / len(values_b),
            "t_statistic": float(statistic),
            "p_value": float(p_value),
            "cohens_d": effect_size,
            "interpretation": (
                "Bác bỏ H0 về trung bình GDM bằng nhau ở ngưỡng 5%."
                if p_value < 0.05
                else "Chưa đủ bằng chứng bác bỏ H0 về trung bình GDM bằng nhau ở ngưỡng 5%."
            ),
        }
    else:
        tests["welch_t_test_gdm"] = {
            "status": "skipped",
            "reason": "Thiếu SciPy hoặc mỗi đội chưa có ít nhất hai giá trị GDM.",
            "samples": {"team_a": len(values_a), "team_b": len(values_b)},
            "cohens_d": effect_size,
        }
    return tests


def _markdown(report: dict[str, Any]) -> str:
    """Render a concise human-readable companion to the auditable JSON."""

    lines = [
        "# Phase 7 — Statistical Evidence",
        "",
        f"- Thời điểm chạy: `{report['run_at']}`",
        "- Phạm vi: các trận chính thức S16 của 10 đội LCK primary; có thể gồm giải quốc tế.",
        "- Wilson CI biểu diễn độ bất định của tỷ lệ thắng quan sát.",
        f"- Trạng thái suy luận: `{report['inferential_status']}`.",
        "",
        "## 1. Tỷ lệ thắng và Wilson 95% CI",
        "",
        "| Team | Wins | Games | Rate | 95% CI | Warning |",
        "|---|---:|---:|---:|---|---|",
    ]
    for team in report["teams"]:
        ci = team["confidence_interval"]
        rate = "N/A" if ci["rate"] is None else f"{ci['rate']:.1%}"
        interval = "N/A" if ci["ci_low"] is None else f"{ci['ci_low']:.1%}–{ci['ci_high']:.1%}"
        warning = "n < 30" if ci["small_sample_warning"] else ""
        lines.append(f"| {team['canonical_name']} | {team['wins']} | {team['games']} | {rate} | {interval} | {warning} |")

    lines.extend(["", "## 2. Kiểm định thăm dò", ""])
    if report.get("side_chi_square"):
        side = report["side_chi_square"]
        lines.append(f"- Chi-square side × outcome: `{side['status']}`; p-value = `{side.get('p_value', 'N/A')}`.")
        if not side.get("assumption_independent_observations", True):
            lines.append("  - Không dùng p-value này làm kết luận xác nhận: blue/red là hai quan sát ghép cặp của cùng game.")
    else:
        lines.append("- Chi-square side × outcome: chưa chạy vì thiếu SciPy.")

    pair = report.get("selected_pair_tests")
    if pair:
        lines.append(f"- Cặp chọn: **{pair['team_a']['name']}** và **{pair['team_b']['name']}**.")
        z_test = pair["two_proportion_z_test"]
        t_test = pair["welch_t_test_gdm"]
        lines.append(f"- Two-proportion z-test: `{z_test['status']}`; p-value = `{z_test.get('p_value', 'N/A')}`.")
        lines.append(f"- Welch t-test GDM + Cohen's d: `{t_test['status']}`; p-value = `{t_test.get('p_value', 'N/A')}`; d = `{t_test.get('cohens_d', 'N/A')}`.")
    else:
        lines.append("- Chưa chọn cặp đội; dùng `--team-a-id` và `--team-b-id` để chạy so sánh.")

    lines.extend(["", "## 3. Giới hạn bắt buộc khi diễn giải", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(
        [
            "",
            "## 4. Cách đọc đúng",
            "",
            "CI rộng nghĩa là ước lượng còn bất định. P-value < 0.05 chỉ là bằng chứng chống lại giả thuyết H0 trong mẫu và theo giả định của kiểm định. "
            "Muốn dự đoán trận kế tiếp phải dùng đặc trưng trước trận, temporal cutoff và backtest ở mô-đun modeling.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_statistics_report(
    config: ProjectConfig,
    team_a_id: int | None = None,
    team_b_id: int | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Generate JSON/Markdown statistical evidence without hiding missing deps."""

    if (team_a_id is None) != (team_b_id is None):
        raise ValueError("Supply both team_a_id and team_b_id, or neither.")
    if team_a_id is not None and team_a_id == team_b_id:
        raise ValueError("team_a_id and team_b_id must be different.")

    database_path = initialize_database(config)
    root = Path(output_root) if output_root is not None else config.root
    reports_directory = root / "reports"
    reports_directory.mkdir(parents=True, exist_ok=True)
    dependencies = _dependency_status()

    with closing(connect_database(database_path)) as connection:
        teams = _team_win_rows(connection)
        team_lookup = {int(team["team_id"]): team for team in teams}
        if team_a_id is not None:
            missing = [team_id for team_id in (team_a_id, team_b_id) if team_id not in team_lookup]
            if missing:
                raise ValueError(f"Selected IDs are not primary LCK teams with dimension rows: {missing}")

        side_test = _side_chi_square(connection) if dependencies["scipy"] else None
        pair_tests = (
            _selected_pair_tests(connection, team_lookup[int(team_a_id)], team_lookup[int(team_b_id)], dependencies)
            if team_a_id is not None and team_b_id is not None
            else None
        )

    requested_test_statuses = []
    if side_test is not None:
        requested_test_statuses.append(side_test["status"])
    if pair_tests is not None:
        requested_test_statuses.extend(
            [pair_tests["two_proportion_z_test"]["status"], pair_tests["welch_t_test_gdm"]["status"]]
        )
    if not requested_test_statuses:
        inferential_status = "skipped"
    elif all(status in {"ok", "assumption_warning"} for status in requested_test_statuses):
        inferential_status = "ok"
    elif any(status in {"ok", "assumption_warning"} for status in requested_test_statuses):
        inferential_status = "partial"
    else:
        inferential_status = "skipped"

    missing_packages = [name for name, available in dependencies.items() if not available]
    report: dict[str, Any] = {
        "phase": "Phase 7 — descriptive and introductory inferential statistics",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "season": config.season,
        "scope": "Official S16 games for the ten primary LCK teams, including eligible international tournaments.",
        "methods": [
            "Wilson 95% confidence interval",
            "Chi-square side × outcome when SciPy is available and assumptions are reported",
            "Two-proportion z-test for a selected pair when Statsmodels is available",
            "Welch t-test plus Cohen's d for selected-pair GDM when SciPy is available",
        ],
        "dependencies": dependencies,
        "missing_optional_packages": missing_packages,
        "inferential_status": inferential_status,
        "teams": teams,
        "side_chi_square": side_test,
        "selected_pair_tests": pair_tests,
        "limitations": LIMITATIONS,
    }

    json_path = reports_directory / "statistics-phase-7.json"
    markdown_path = reports_directory / "statistics-phase-7.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(_markdown(report), encoding="utf-8")

    # Return a small CLI payload while keeping full evidence in the report file.
    return {
        "status": "ok",
        "report_path": str(json_path),
        "markdown_path": str(markdown_path),
        "team_rows": len(teams),
        "inferential_status": inferential_status,
        "missing_optional_packages": missing_packages,
    }
