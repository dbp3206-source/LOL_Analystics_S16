"""Streamlit demo for the LoL Pro Analytics S16 project.

Run from the project root with:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import sys
from datetime import datetime, timezone
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


# DATA ACCESS HELPERS --------------------------------------------------------
# The dashboard keeps SQL reads in small functions.  A beginner can inspect
# the returned list-of-dictionaries before learning Streamlit presentation.

def _rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute a read-only parameterized query and close SQLite reliably."""

    config = load_config()
    connection = sqlite3.connect(config.database_path)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(query, params).fetchall()]
    finally:
        connection.close()


def _fmt(value: Any, digits: int = 2) -> str:
    """Display missing values honestly instead of turning them into zero."""

    if value is None:
        return "—"
    return f"{value:.{digits}f}" if isinstance(value, (float, int)) else str(value)


def _freshness_status(max_age_hours: int) -> dict[str, Any]:
    """Calculate whether the latest successful crawl is recent enough."""
    rows = _rows(
        """SELECT finished_at FROM update_runs
           WHERE status='success' AND finished_at IS NOT NULL
           ORDER BY finished_at DESC LIMIT 1"""
    )
    finished_at = rows[0]["finished_at"] if rows else None
    age_hours = (
        (datetime.now(timezone.utc) - datetime.fromisoformat(finished_at)).total_seconds() / 3600
        if finished_at
        else None
    )
    return {
        "status": "fresh" if age_hours is not None and age_hours <= max_age_hours else "stale_or_missing",
        "last_successful_update": finished_at,
        "age_hours": age_hours,
    }


def _team_rows() -> list[dict[str, Any]]:
    """List only the ten selectable primary LCK teams."""

    return _rows("SELECT team_id,canonical_name FROM teams WHERE is_lck_primary=1 ORDER BY canonical_name")


def _team_summary(team_id: int) -> list[dict[str, Any]]:
    """Aggregate game-level facts into one descriptive team profile."""

    return _rows(
        """SELECT t.canonical_name,COUNT(DISTINCT s.game_id) games,SUM(s.win) wins,
                  AVG(s.kills) avg_kills,AVG(s.deaths) avg_deaths,AVG(s.gpm) avg_gpm,
                  AVG(s.gdm) avg_gdm,AVG(s.dpm) avg_dpm,AVG(s.csd15) avg_csd15,
                  AVG(s.towers) avg_towers,AVG(s.dragons) avg_dragons,AVG(s.nashors) avg_nashors,
                  AVG(s.first_blood) first_blood_rate,AVG(s.first_tower) first_tower_rate
           FROM team_game_stats s JOIN teams t ON t.team_id=s.team_id
           WHERE s.team_id=? GROUP BY t.canonical_name""",
        (team_id,),
    )


def _player_rows() -> list[dict[str, Any]]:
    """List current primary-roster players used by the player selectors."""

    return _rows(
        """SELECT DISTINCT p.player_id,p.canonical_name,p.primary_role
           FROM players p JOIN roster_periods r ON r.player_id=p.player_id
           JOIN teams t ON t.team_id=r.team_id
           WHERE t.is_lck_primary=1 AND r.is_primary=1
             AND r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2
                              WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)
           ORDER BY p.primary_role,p.canonical_name"""
    )


def _player_summary(player_id: str) -> list[dict[str, Any]]:
    """Aggregate one starter's S16 games without comparing across roles."""

    return _rows(
        """SELECT p.canonical_name,p.primary_role,COUNT(DISTINCT s.game_id) games,
                  AVG(s.kda) avg_kda,AVG(s.cs) avg_cs,AVG(s.csm) avg_csm,
                  AVG(s.dpm) avg_dpm,AVG(s.gold_share) avg_gold_share,
                  AVG(s.damage_share) avg_damage_share
           FROM player_game_stats s JOIN players p ON p.player_id=s.player_id
           JOIN teams t ON t.team_id=s.team_id
           JOIN roster_periods r ON r.team_id=s.team_id AND r.player_id=s.player_id AND r.is_primary=1
           WHERE s.player_id=? AND t.is_lck_primary=1
             AND r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2
                              WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)
           GROUP BY p.canonical_name,p.primary_role""",
        (player_id,),
    )


def _rolling_rows(team_id: int) -> list[dict[str, Any]]:
    """Return chronologically ordered games for the recent-form view."""

    return _rows(
        """SELECT g.played_at,s.game_id,s.win,s.kills,s.deaths
           FROM team_game_stats s JOIN games g ON g.game_id=s.game_id
           WHERE s.team_id=? ORDER BY g.played_at,g.game_id""",
        (team_id,),
    )


def _recent_form_chart_rows(rows: list[dict[str, Any]], window: int = 5) -> list[dict[str, Any]]:
    """Add game order and a trailing win rate without leaking future games.

    The result deliberately separates a 0..1 form metric from combat counts.
    Streamlit receives a typed Pandas DataFrame later, avoiding ambiguous chart
    inference from a raw ``list[dict]``.
    """

    wins: list[float] = []
    chart_rows: list[dict[str, Any]] = []
    for game_order, row in enumerate(rows, start=1):
        wins.append(float(row["win"]))
        recent_wins = wins[-window:]
        chart_rows.append(
            {
                "game_order": game_order,
                "rolling_win_rate_5": sum(recent_wins) / len(recent_wins),
                "kills": float(row["kills"]),
                "deaths": float(row["deaths"]),
            }
        )
    return chart_rows


def _starter_rows(team_id: int) -> list[dict[str, Any]]:
    """Return the five current starters for one primary LCK team.

    The explicit ``teams`` join is important: it keeps external tournament
    opponents out of the selectable primary roster and gives the query the
    ``t`` alias used by the scope condition.
    """
    return _rows(
        """SELECT p.canonical_name,p.primary_role,r.valid_from,r.evidence_game_id
           FROM players p JOIN roster_periods r ON r.player_id=p.player_id AND r.team_id=?
           JOIN teams t ON t.team_id=r.team_id
           WHERE t.is_lck_primary=1 AND r.is_primary=1
             AND r.valid_from=(SELECT MAX(r2.valid_from) FROM roster_periods r2
                              WHERE r2.team_id=r.team_id AND r2.player_id=r.player_id AND r2.is_primary=1)
           ORDER BY CASE p.primary_role WHEN 'TOP' THEN 1 WHEN 'JUNGLE' THEN 2 WHEN 'MID' THEN 3 WHEN 'BOT' THEN 4 WHEN 'SUPPORT' THEN 5 ELSE 6 END""",
        (team_id,),
    )


def _champion_rows(team_id: int | None = None, player_id: str | None = None) -> list[dict[str, Any]]:
    """Reuse the analysis-layer champion-pool calculation in the UI."""

    from src.analysis.metrics import champion_pool

    config = load_config()
    connection = sqlite3.connect(config.database_path)
    connection.row_factory = sqlite3.Row
    try:
        return champion_pool(connection, team_id=team_id, player_id=player_id)
    finally:
        connection.close()


def _h2h_rows(team_a_id: int, team_b_id: int) -> list[dict[str, Any]]:
    """Reuse game-level head-to-head evidence instead of recomputing it."""

    from src.analysis.metrics import head_to_head

    config = load_config()
    connection = sqlite3.connect(config.database_path)
    connection.row_factory = sqlite3.Row
    try:
        return head_to_head(connection, team_a_id, team_b_id)
    finally:
        connection.close()


def _next_fixture(team_id: int) -> list[dict[str, Any]]:
    """Return at most three future fixtures involving one team."""

    return _rows(
        """SELECT s.fixture_id,s.scheduled_at_utc,s.best_of,s.status,
                  a.canonical_name team_a,b.canonical_name team_b
           FROM schedules s JOIN teams a ON a.team_id=s.team_a_id JOIN teams b ON b.team_id=s.team_b_id
           WHERE (s.team_a_id=? OR s.team_b_id=?) AND s.scheduled_at_utc>=?
           ORDER BY s.scheduled_at_utc LIMIT 3""",
        (team_id, team_id, datetime.now(timezone.utc).isoformat()),
    )


def _next_fixture_between(team_a_id: int, team_b_id: int) -> list[dict[str, Any]]:
    """Return the next stored official fixture for exactly two teams."""
    return _rows(
        """SELECT fixture_id,scheduled_at_utc,best_of,status
           FROM schedules
           WHERE ((team_a_id=? AND team_b_id=?) OR (team_a_id=? AND team_b_id=?))
             AND scheduled_at_utc>=?
           ORDER BY scheduled_at_utc LIMIT 1""",
        (team_a_id, team_b_id, team_b_id, team_a_id, datetime.now(timezone.utc).isoformat()),
    )


def _objective_timing_rows(team_id: int) -> list[dict[str, Any]]:
    """Show source-provided objective milestone timing for one team."""
    return _rows(
        """WITH owned AS (
               SELECT te.objective,te.event_type,te.minute * 60 + te.second elapsed_seconds
               FROM timeline_events te JOIN games g ON g.game_id=te.game_id
               WHERE CASE WHEN te.side='blue' THEN g.blue_team_id ELSE g.red_team_id END=?
           )
           SELECT objective,event_type,COUNT(*) events,ROUND(AVG(elapsed_seconds),1) avg_elapsed_seconds
           FROM owned GROUP BY objective,event_type ORDER BY objective""",
        (team_id,),
    )


def main() -> None:
    """Render six beginner-facing analysis modes from the same SQLite facts."""

    try:
        import streamlit as st
    except ModuleNotFoundError:
        print("Streamlit is not installed. Install requirements.txt, then run: streamlit run app/streamlit_app.py")
        return

    config = load_config()
    st.set_page_config(page_title="LoL Pro Analytics S16", page_icon="L", layout="wide")
    st.title("LoL Pro Analytics · Season 16")
    st.caption(f"Gol.gg statistics · data cutoff is controlled by the SQLite update pipeline · season starts {config.season_start_date}")
    freshness = _freshness_status(config.update_policy.max_age_hours)
    if freshness["status"] == "fresh":
        st.success(f"Data fresh · last successful update: {freshness['last_successful_update']}")
    else:
        age = f"{freshness['age_hours']:.1f} giờ" if freshness["age_hours"] is not None else "không xác định"
        st.error(
            f"Data stale/missing · age: {age}. Hãy chạy scripts/daily_update.ps1 trước khi gọi kết quả là dự đoán trận tiếp theo."
        )

    if st.sidebar.button("Refresh supplemental schedule"):
        try:
            from src.collection.schedule import run_schedule_update

            schedule_result = run_schedule_update(config)
            st.sidebar.success(f"Schedule: {schedule_result['fixtures_upserted']} fixtures upserted")
        except Exception as exc:
            st.sidebar.warning(f"Schedule refresh unavailable: {exc}")

    teams = _team_rows()
    if not teams:
        st.warning("Chưa có dữ liệu team. Hãy chạy update-team trước khi phân tích.")
        st.stop()
    team_options = {row["canonical_name"]: row["team_id"] for row in teams}
    mode = st.sidebar.selectbox("Analysis mode", ["Team overview", "Team comparison", "Player overview", "Player comparison", "Matchup prediction", "Recent form"])

    # PRESENTATION ROUTES ---------------------------------------------------
    # Each branch answers one user intent.  SQL/metrics stay in helpers above;
    # this section is responsible only for selectors, tables, charts and notes.
    if mode == "Team overview":
        name = st.sidebar.selectbox("Team", list(team_options))
        rows = _team_summary(team_options[name])
        if rows:
            row = rows[0]
            st.subheader(name)
            metrics = {
                "Games": row["games"],
                "Win rate": row["wins"] / row["games"] if row["games"] else None,
                "Avg kills": row["avg_kills"],
                "Avg deaths": row["avg_deaths"],
                "Avg DPM": row["avg_dpm"],
                "Avg CSD@15": row["avg_csd15"],
                "Avg towers": row["avg_towers"],
                "Avg dragons": row["avg_dragons"],
                "Avg Nashors": row["avg_nashors"],
                "First blood rate": row["first_blood_rate"],
                "First tower rate": row["first_tower_rate"],
            }
            st.dataframe([metrics], width="stretch", hide_index=True)
            st.subheader("Current starters")
            starters = _starter_rows(team_options[name])
            st.dataframe(starters, width="stretch", hide_index=True)
            st.subheader("Champion pool")
            st.dataframe(_champion_rows(team_options[name])[:15], width="stretch", hide_index=True)
            st.subheader("Objective timeline milestones")
            timing = _objective_timing_rows(team_options[name])
            st.dataframe(timing if timing else [{"status": "No timeline milestone collected"}], width="stretch", hide_index=True)
            st.subheader("Next scheduled fixtures")
            fixtures = _next_fixture(team_options[name])
            st.dataframe(fixtures if fixtures else [{"status": "No future fixture collected"}], width="stretch", hide_index=True)
            st.caption("Mọi tỷ lệ cần được đọc kèm Games; dữ liệu null nghĩa là nguồn game-level chưa cung cấp trường đó.")

    elif mode == "Team comparison":
        names = st.sidebar.multiselect("Teams", list(team_options), default=list(team_options)[:2], max_selections=2)
        if len(names) == 2:
            rows = [_team_summary(team_options[name])[0] for name in names if _team_summary(team_options[name])]
            view = []
            for metric in ["games", "wins", "avg_kills", "avg_deaths", "avg_gpm", "avg_gdm", "avg_dpm", "avg_csd15", "avg_towers", "avg_dragons", "avg_nashors", "first_blood_rate", "first_tower_rate"]:
                view.append({"Metric": metric, names[0]: rows[0].get(metric), names[1]: rows[1].get(metric)})
            st.subheader(f"{names[0]} vs {names[1]}")
            st.dataframe(view, width="stretch", hide_index=True)
            st.bar_chart(view, x="Metric", y=names)
            h2h = _h2h_rows(team_options[names[0]], team_options[names[1]])
            st.subheader("S16 head-to-head")
            st.dataframe(h2h if h2h else [{"status": "No S16 H2H game in database"}], width="stretch", hide_index=True)
        else:
            st.info("Chọn đúng hai đội để so sánh.")

    elif mode == "Player overview":
        players = _player_rows()
        name = st.sidebar.selectbox("Player", [row["canonical_name"] for row in players])
        player_id = next(row["player_id"] for row in players if row["canonical_name"] == name)
        rows = _player_summary(player_id)
        st.subheader(name)
        st.dataframe(rows, width="stretch", hide_index=True)
        st.subheader("Champion pool")
        st.dataframe(_champion_rows(player_id=player_id), width="stretch", hide_index=True)

    elif mode == "Player comparison":
        players = _player_rows()
        names = st.sidebar.multiselect("Players", [row["canonical_name"] for row in players], default=[row["canonical_name"] for row in players[:2]], max_selections=2)
        if len(names) == 2:
            stats = []
            for name in names:
                player_id = next(row["player_id"] for row in players if row["canonical_name"] == name)
                stats.append(_player_summary(player_id)[0])
            if stats[0].get("primary_role") != stats[1].get("primary_role"):
                st.warning("Hai tuyển thủ khác role: bảng dưới đây chỉ là mô tả raw, không dùng để kết luận ai mạnh hơn. Cần role-adjusted percentile khi có đủ dữ liệu.")
            view = [{"Metric": metric, names[0]: stats[0].get(metric), names[1]: stats[1].get(metric)} for metric in ["games", "avg_kda", "avg_cs", "avg_csm", "avg_dpm", "avg_gold_share", "avg_damage_share"]]
            st.subheader(f"{names[0]} vs {names[1]}")
            st.dataframe(view, width="stretch", hide_index=True)
            st.bar_chart(view, x="Metric", y=names)
        else:
            st.info("Chọn đúng hai tuyển thủ để so sánh.")

    elif mode == "Matchup prediction":
        names = st.sidebar.multiselect("Teams", list(team_options), default=list(team_options)[:2], max_selections=2)
        if len(names) == 2:
            from src.modeling.predictor import predict_matchup

            team_a_id, team_b_id = team_options[names[0]], team_options[names[1]]
            # Official prediction requires a stored future fixture.  Without
            # one, the same model may be explored only as a hypothetical case.
            fixtures = _next_fixture_between(team_a_id, team_b_id)
            fixture_id = fixtures[0]["fixture_id"] if fixtures else None
            try:
                prediction = predict_matchup(config, team_a_id, team_b_id, fixture_id=fixture_id, persist=False)
            except ValueError as exc:
                st.error(f"Không thể tạo prediction hợp lệ: {exc}")
                return
            st.subheader(f"{names[0]} vs {names[1]}")
            st.caption(f"Model: {prediction['model_version']} · Context: {prediction['prediction_context']} · Status: {prediction['status']} · H2H games: {prediction['head_to_head']['games']}")
            if fixtures:
                st.info(f"Official fixture: {fixtures[0]['scheduled_at_utc']} · BO{fixtures[0]['best_of'] or '?'}")
            else:
                st.info("Không tìm thấy fixture tương lai giữa hai đội; kết quả dưới đây là hypothetical matchup, không được gọi là dự đoán trận tiếp theo.")
            st.dataframe(
                [
                    {"Team": names[0], "Win probability": prediction["probability_team_a"], "Games in sample": prediction["team_a"]["games"], "90% uncertainty": prediction["team_a"]["uncertainty_90"]},
                    {"Team": names[1], "Win probability": prediction["probability_team_b"], "Games in sample": prediction["team_b"]["games"], "90% uncertainty": prediction["team_b"]["uncertainty_90"]},
                ],
                width="stretch",
                hide_index=True,
            )
            st.bar_chart(
                [{"Team": names[0], "Win probability": prediction["probability_team_a"]}, {"Team": names[1], "Win probability": prediction["probability_team_b"]}],
                x="Team",
                y="Win probability",
            )
            st.warning(prediction["confidence_note"])
            h2h = _h2h_rows(team_options[names[0]], team_options[names[1]])
            st.subheader("Game-level H2H evidence")
            st.dataframe(h2h if h2h else [{"status": "No H2H evidence"}], width="stretch", hide_index=True)
        else:
            st.info("Chọn đúng hai đội để dự đoán matchup.")

    else:
        # The final branch is the explicit "Recent form" mode.  Rows are kept
        # in game order so a learner can compare the table and both charts.
        name = st.sidebar.selectbox("Team", list(team_options))
        rows = _rolling_rows(team_options[name])
        st.subheader(f"Recent form · {name}")
        if rows:
            import matplotlib.pyplot as plt
            import pandas as pd

            st.dataframe(rows, width="stretch", hide_index=True)
            chart_frame = pd.DataFrame(_recent_form_chart_rows(rows))
            st.markdown("**Phong độ thắng — rolling 5 games**")
            form_figure, form_axis = plt.subplots(figsize=(10, 3.2))
            form_axis.plot(
                chart_frame["game_order"],
                chart_frame["rolling_win_rate_5"],
                color="#38bdf8",
                linewidth=2,
            )
            form_axis.fill_between(
                chart_frame["game_order"],
                chart_frame["rolling_win_rate_5"],
                color="#38bdf8",
                alpha=0.12,
            )
            form_axis.set(xlabel="Game order", ylabel="Rolling win rate", ylim=(0, 1))
            form_axis.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
            form_axis.grid(axis="y", alpha=0.25)
            st.pyplot(form_figure, clear_figure=True)
            plt.close(form_figure)

            st.markdown("**Nhịp giao tranh — kills và deaths theo trận**")
            combat_figure, combat_axis = plt.subplots(figsize=(10, 3.2))
            combat_axis.plot(chart_frame["game_order"], chart_frame["kills"], label="Kills", color="#22c55e", linewidth=1.8)
            combat_axis.plot(chart_frame["game_order"], chart_frame["deaths"], label="Deaths", color="#fb7185", linewidth=1.8)
            combat_axis.set(xlabel="Game order", ylabel="Count")
            combat_axis.grid(axis="y", alpha=0.25)
            combat_axis.legend(frameon=False, ncol=2)
            st.pyplot(combat_figure, clear_figure=True)
            plt.close(combat_figure)
            st.caption("Trục X là thứ tự trận, tránh nối sai qua các ngày không thi đấu; mỗi điểm rolling chỉ dùng trận hiện tại và quá khứ.")
        else:
            st.info("Chưa có game-level rows cho đội này.")


if __name__ == "__main__":
    main()
