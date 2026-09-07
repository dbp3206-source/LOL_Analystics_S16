"""Leakage-safe walk-forward evaluation for baseline and logistic models."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..storage.database import connect_database, initialize_database


FEATURE_NAMES = ["win_rate_diff", "prior_games_diff", "gpm_diff", "gdm_diff", "kills_diff", "first_tower_diff"]


def _log_loss(probability: float, actual: int) -> float:
    """Score probability confidence while clipping unsafe log(0) values."""

    probability = max(1e-6, min(1 - 1e-6, probability))
    return -(actual * math.log(probability) + (1 - actual) * math.log(1 - probability))


def _metrics(predictions: list[dict[str, Any]]) -> dict[str, float | None]:
    """Calculate accuracy, Brier score and log loss from scored rows."""

    if not predictions:
        return {"accuracy": None, "brier_score": None, "log_loss": None}
    accuracy = sum(int((item["probability_team_a"] >= 0.5) == bool(item["actual_team_a_win"])) for item in predictions) / len(predictions)
    brier = sum((item["probability_team_a"] - item["actual_team_a_win"]) ** 2 for item in predictions) / len(predictions)
    log_loss = sum(_log_loss(item["probability_team_a"], item["actual_team_a_win"]) for item in predictions) / len(predictions)
    return {"accuracy": accuracy, "brier_score": brier, "log_loss": log_loss}


def _team_average(history: dict[str, float], key: str) -> float:
    """Return a cumulative pre-game average, or zero before any history."""

    count = history.get(f"{key}_count", 0.0)
    return history.get(f"{key}_sum", 0.0) / count if count else 0.0


def _features(left: dict[str, float], right: dict[str, float]) -> list[float]:
    """Create interpretable team-A minus team-B feature differences."""

    left_rate = (left["wins"] + 1.0) / (left["games"] + 2.0)
    right_rate = (right["wins"] + 1.0) / (right["games"] + 2.0)
    return [
        left_rate - right_rate,
        (left["games"] - right["games"]) / 10.0,
        (_team_average(left, "gpm") - _team_average(right, "gpm")) / 500.0,
        # After the data-contract correction, GDM is gold/minute. Scaling by
        # 500 keeps this educational feature near the same order as the other
        # feature differences before standardization.
        (_team_average(left, "gdm") - _team_average(right, "gdm")) / 500.0,
        (_team_average(left, "kills") - _team_average(right, "kills")) / 20.0,
        _team_average(left, "first_tower") - _team_average(right, "first_tower"),
    ]


def _fit_logistic(examples: list[tuple[list[float], int]], epochs: int = 80, learning_rate: float = 0.08, l2: float = 0.1) -> tuple[list[float], float, list[float], list[float]] | None:
    """Fit a small standardized L2 logistic model using earlier games only."""

    if len(examples) < 4 or len({target for _, target in examples}) < 2:
        return None
    dimension = len(FEATURE_NAMES)
    means = [sum(row[index] for row, _ in examples) / len(examples) for index in range(dimension)]
    scales = []
    for index in range(dimension):
        variance = sum((row[index] - means[index]) ** 2 for row, _ in examples) / len(examples)
        scales.append(math.sqrt(variance) or 1.0)
    normalized = [([(value - means[index]) / scales[index] for index, value in enumerate(row)], target) for row, target in examples]
    weights = [0.0] * dimension
    intercept = 0.0
    for _ in range(epochs):
        grad_w = [0.0] * dimension
        grad_b = 0.0
        for row, target in normalized:
            score = intercept + sum(weight * value for weight, value in zip(weights, row))
            probability = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, score))))
            error = probability - target
            grad_b += error
            for index, value in enumerate(row):
                grad_w[index] += error * value
        denominator = len(normalized)
        intercept -= learning_rate * grad_b / denominator
        for index in range(dimension):
            weights[index] -= learning_rate * ((grad_w[index] / denominator) + l2 * weights[index])
    return weights, intercept, means, scales


def _predict_logistic(model: tuple[list[float], float, list[float], list[float]], row: list[float]) -> float:
    """Apply stored scaling and logistic weights to one feature row."""

    weights, intercept, means, scales = model
    score = intercept + sum(weight * ((value - means[index]) / scales[index]) for index, (weight, value) in enumerate(zip(weights, row)))
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, score))))


def run_backtest(config: Any, output_root: Path | None = None) -> dict[str, Any]:
    """Evaluate pre-game information chronologically, without target leakage.

    ``output_root`` lets automated tests write evidence into a temporary
    directory instead of changing the real project reports.
    """

    database_path = initialize_database(config)
    with closing(connect_database(database_path)) as connection:
        rows = connection.execute(
            """SELECT g.game_id,g.played_at,g.winner_team_id,
                      a.team_id team_a_id,b.team_id team_b_id,
                      a.gpm a_gpm,b.gpm b_gpm,a.gdm a_gdm,b.gdm b_gdm,
                      a.kills a_kills,b.kills b_kills,
                      a.first_tower a_first_tower,b.first_tower b_first_tower
               FROM games g
               JOIN team_game_stats a ON a.game_id=g.game_id
               JOIN team_game_stats b ON b.game_id=g.game_id AND b.team_id<>a.team_id
               JOIN teams ta ON ta.team_id=a.team_id AND ta.is_lck_primary=1
               JOIN teams tb ON tb.team_id=b.team_id AND tb.is_lck_primary=1
               WHERE g.played_at>=? AND g.winner_team_id IS NOT NULL AND a.team_id<b.team_id
               ORDER BY g.played_at,g.game_id,a.team_id""",
            (config.season_start_date,),
        ).fetchall()

    history: dict[int, dict[str, float]] = defaultdict(lambda: {"games": 0.0, "wins": 0.0})
    examples: list[tuple[list[float], int]] = []
    scored: list[dict[str, Any]] = []
    logistic_scored: list[dict[str, Any]] = []
    logistic_model: tuple[list[float], float, list[float], list[float]] | None = None
    last_logistic_fit_examples = -10
    for row in rows:
        a_id, b_id = int(row["team_a_id"]), int(row["team_b_id"])
        left, right = history[a_id], history[b_id]
        vector = _features(left, right)
        left_rate = (left["wins"] + 1.0) / (left["games"] + 2.0)
        right_rate = (right["wins"] + 1.0) / (right["games"] + 2.0)
        baseline_probability = left_rate / (left_rate + right_rate)
        # Refit at deterministic checkpoints.  Every fit still sees only
        # examples strictly before the target game, while avoiding an
        # unnecessary O(n^2) full optimizer run for every historical row.
        if len(examples) >= 4 and (logistic_model is None or len(examples) - last_logistic_fit_examples >= 10):
            logistic_model = _fit_logistic(examples)
            last_logistic_fit_examples = len(examples)
        model = logistic_model
        actual = int(row["winner_team_id"] == a_id)
        item = {
            "game_id": row["game_id"], "played_at": row["played_at"], "team_a_id": a_id, "team_b_id": b_id,
            "probability_team_a": baseline_probability, "actual_team_a_win": actual,
            "prior_games_team_a": int(left["games"]), "prior_games_team_b": int(right["games"]), "prior_training_examples": len(examples), "feature_values": dict(zip(FEATURE_NAMES, vector)),
        }
        scored.append(item)
        if model is not None:
            logistic_item = dict(item)
            logistic_item["probability_team_a"] = _predict_logistic(model, vector)
            logistic_scored.append(logistic_item)
        examples.append((vector, actual))
        for team, prefix in ((left, "a"), (right, "b")):
            team["games"] += 1.0
            team["wins"] += actual if prefix == "a" else 1 - actual
            for metric in ("gpm", "gdm", "kills", "first_tower"):
                value = row[f"{prefix}_{metric}"]
                if value is not None:
                    team[f"{metric}_sum"] = team.get(f"{metric}_sum", 0.0) + float(value)
                    team[f"{metric}_count"] = team.get(f"{metric}_count", 0.0) + 1.0

    baseline_metrics = _metrics(scored)
    logistic_metrics = _metrics(logistic_scored)
    report = {
        "phase": "Phase 9 — Walk-forward model evaluation", "run_at": datetime.now(timezone.utc).isoformat(), "season": config.season,
        "feature_names": FEATURE_NAMES,
        "leakage_control": "Each row uses only team history before the current game; target is appended after scoring. Logistic model is fit only on earlier rows.",
        "games_available": len(scored), "models": {
            "laplace_baseline": {"games_scored": len(scored), "metrics": baseline_metrics},
            "logistic_regression": {"games_scored": len(logistic_scored), "metrics": logistic_metrics, "training_minimum": 4, "fit_interval_examples": 10, "optimizer": "standardized gradient descent with L2 (80 epochs per checkpoint fit)"},
        },
        "small_sample_warning": len(scored) < 30 or len(logistic_scored) < 10,
        "predictions": scored, "logistic_predictions": logistic_scored,
        "limitations": ["The logistic model is an educational dependency-light implementation, not a production-trained model.", "Current sample is too small for generalization or model selection claims."],
    }
    report_dir = (output_root or config.root) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "backtest-phase-9.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Phase 9 Walk-forward Model Evaluation", "", f"- Games available: `{len(scored)}`", f"- Baseline games scored: `{len(scored)}`", f"- Logistic games scored after warm-up: `{len(logistic_scored)}`", "", "| Model | Accuracy | Brier score | Log loss |", "|---|---:|---:|---:|"]
    for name, metrics in (("Laplace baseline", baseline_metrics), ("Logistic regression", logistic_metrics)):
        lines.append(f"| {name} | {metrics['accuracy']:.1%} | {metrics['brier_score']:.4f} | {metrics['log_loss']:.4f} |" if metrics["accuracy"] is not None else f"| {name} | — | — | — |")
    lines += ["", "- Leakage control: each prediction uses only rows dated before the current game; the current result is appended after scoring.", "- Warning: results are descriptive until a materially larger S16 sample is collected."]
    (report_dir / "backtest-phase-9.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"status": "ok", "report_path": str(path), "games_scored": len(scored), "metrics": baseline_metrics, "logistic_games_scored": len(logistic_scored), "logistic_metrics": logistic_metrics, "small_sample_warning": report["small_sample_warning"]}
