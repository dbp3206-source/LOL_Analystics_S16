"""EDA S16 theo kiểu VS Code cells.

Mở file này trong VS Code rồi bấm ``Run Cell`` từ trên xuống. File cũng có
thể chạy như Python script bình thường. Mỗi cell nêu rõ mục tiêu, input,
xử lý và output để người mới không phải đoán luồng dữ liệu.
"""

# %% [markdown]
# # Cell 1 — Chuẩn bị project
#
# **Mục tiêu:** tìm project root và cho Python biết nơi chứa package `src`.
# **Input:** vị trí file notebook hiện tại.
# **Output:** biến `ROOT` và import path hợp lệ.

# %%
from pathlib import Path
import sys

# Windows Terminal có thể mặc định CP1252 và lỗi khi in chú thích tiếng Việt.
# ``reconfigure`` chỉ đổi cách stdout mã hóa text, không đổi dữ liệu phân tích.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Khi chạy file `.py`, `__file__` tồn tại và root nằm trên thư mục notebooks.
# Khi copy cell sang `.ipynb`, fallback `Path.cwd()` giúp dùng thư mục VS Code.
ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
if not (ROOT / "src").exists():
    raise FileNotFoundError("Hãy mở/chạy notebook từ project lol-pro-analytics-s16.")

# Python tìm module theo thứ tự trong sys.path. Chèn root ở vị trí đầu giúp
# câu lệnh `from src...` luôn dùng code trong project hiện tại.
sys.path.insert(0, str(ROOT))
print(f"Project root: {ROOT}")


# %% [markdown]
# # Cell 2 — Import thư viện và đọc cấu hình
#
# **Mục tiêu:** nạp Pandas/NumPy và khóa phạm vi phân tích ở S16.
# **Input:** `configs/project.json`.
# **Output:** object `config` cùng thông tin season/source.

# %%
import numpy as np
import pandas as pd

from src.analysis.pandas_eda import (
    PLAYER_NUMERIC_COLUMNS,
    TEAM_NUMERIC_COLUMNS,
    inspect_dataframe,
    iqr_outlier_summary,
    load_analysis_frames,
    numeric_summary,
)
from src.config import load_config

config = load_config(ROOT / "configs" / "project.json")
print(
    {
        "project": config.project_name,
        "season": config.season,
        "season_start": config.season_start_date,
        "primary_teams": len(config.tracked_lck_teams),
        "stats_source": config.sources["statistics"],
    }
)


# %% [markdown]
# # Cell 3 — Load bảng phân tích
#
# **Mục tiêu:** chuyển các truy vấn SQLite thành hai DataFrame.
# **Input:** `data/lol_analytics.db`.
# **Output:** `team_games` (một đội/game) và `player_games` (một tuyển thủ/game).

# %%
team_games, player_games = load_analysis_frames(config)

# `shape` trả tuple (số dòng, số cột). Đây là kiểm tra đầu tiên để biết quy mô
# dữ liệu và phát hiện ngay tình huống query vô tình trả về 0 hoặc quá nhiều dòng.
print("team_games shape:", team_games.shape)
print("player_games shape:", player_games.shape)

# `head()` không thay đổi dữ liệu; nó chỉ xem năm dòng đầu.
print(team_games.head())


# %% [markdown]
# # Cell 4 — Hiểu cấu trúc, dtype, missing và duplicate
#
# **Câu hỏi:** dữ liệu có đúng grain và kiểu chưa, cột nào thiếu, dòng nào trùng?

# %%
team_inspection = inspect_dataframe(team_games, "team_games")
player_inspection = inspect_dataframe(player_games, "player_games")

print("Team duplicate rows:", team_inspection["duplicate_rows"])
print("Player duplicate rows:", player_inspection["duplicate_rows"])

# Sắp xếp missing giảm dần để nhìn cột đáng chú ý trước. Missing là “chưa biết”,
# không được tự thay bằng 0 vì 0 có ý nghĩa là metric thật sự bằng không.
team_missing = (
    team_games.isna()
    .sum()
    .rename("missing_count")
    .to_frame()
    .assign(missing_rate=lambda frame: frame["missing_count"] / len(team_games))
    .sort_values("missing_rate", ascending=False)
)
print(team_missing.head(10))


# %% [markdown]
# # Cell 5 — Thống kê mô tả
#
# **Câu hỏi:** central tendency, spread và distribution của metric ra sao?

# %%
team_summary = numeric_summary(
    team_games,
    TEAM_NUMERIC_COLUMNS + ["kill_death_ratio"],
)
player_summary = numeric_summary(player_games, PLAYER_NUMERIC_COLUMNS)

# Một bảng có count/mean/std/quartile tốt hơn việc chỉ báo một giá trị trung bình.
print(team_summary.loc[team_summary["metric"].isin(["gpm", "gdm", "dpm", "gd15"])])
print(player_summary.loc[player_summary["metric"].isin(["kda", "csm", "dpm", "gd15"])])


# %% [markdown]
# # Cell 6 — Rà soát outlier bằng IQR
#
# **Câu hỏi:** metric nào có nhiều giá trị cực đoan cần kiểm tra lại?
# **Lưu ý:** kết quả chỉ là candidate, không phải lệnh xóa dữ liệu.

# %%
team_outliers = iqr_outlier_summary(
    team_games,
    ["kills", "gpm", "gdm", "dpm", "csd15"],
)
print(team_outliers.sort_values("candidate_rate", ascending=False))


# %% [markdown]
# # Cell 7 — So sánh theo side bằng crosstab
#
# **Câu hỏi:** blue/red side có tỷ lệ thắng mô tả khác nhau không?

# %%
side_counts = pd.crosstab(team_games["side"], team_games["win"])
side_rates = pd.crosstab(team_games["side"], team_games["win"], normalize="index")

# Luôn trình bày count trước rate để người xem biết mẫu số.
print("Counts by side and result")
print(side_counts)
print("Rates by side and result")
print(side_rates)


# %% [markdown]
# # Cell 8 — Baseline theo role trước khi so sánh player
#
# **Câu hỏi:** distribution tự nhiên của KDA/DPM/CSM khác nhau theo role ra sao?

# %%
role_summary = (
    player_games.groupby("role", observed=True)
    .agg(
        games=("game_id", "count"),
        players=("player_id", "nunique"),
        median_kda=("kda", "median"),
        median_csm=("csm", "median"),
        mean_dpm=("dpm", "mean"),
        mean_gd15=("gd15", "mean"),
        mean_vision_per_minute=("vision_score_per_minute", "mean"),
    )
    .reset_index()
)
print(role_summary)


# %% [markdown]
# # Cell 9 — So sánh hai đội bằng cùng định nghĩa metric
#
# Thay hai tên dưới đây để tạo query phân tích khác. Filter dùng `isin` để chỉ
# giữ những dòng thuộc hai đội, sau đó `groupby` gom các game của từng đội.

# %%
TEAM_A = "T1"
TEAM_B = "Hanwha Life Esports"

selected_teams = team_games[team_games["team_name"].isin([TEAM_A, TEAM_B])].copy()
team_comparison = (
    selected_teams.groupby("team_name", observed=True)
    .agg(
        games=("game_id", "count"),
        wins=("win", "sum"),
        avg_gpm=("gpm", "mean"),
        avg_gdm=("gdm", "mean"),
        avg_dpm=("dpm", "mean"),
        avg_gd15=("gd15", "mean"),
        first_blood_rate=("first_blood", "mean"),
        first_tower_rate=("first_tower", "mean"),
    )
    .reset_index()
)
team_comparison["win_rate"] = team_comparison["wins"] / team_comparison["games"]
print(team_comparison)


# %% [markdown]
# # Cell 10 — Correlation để sinh giả thuyết
#
# **Câu hỏi:** feature nào có quan hệ tuyến tính với win trong snapshot hiện tại?
# Correlation chỉ gợi ý hướng điều tra, không chứng minh nguyên nhân.

# %%
correlation_columns = [
    "win",
    "kills",
    "deaths",
    "gpm",
    "gdm",
    "dpm",
    "gd15",
    "csd15",
    "first_blood",
    "first_tower",
    "dragons",
    "nashors",
    "towers",
]
correlation = team_games[correlation_columns].corr(numeric_only=True)
correlation_with_win = correlation["win"].sort_values(ascending=False)
print(correlation_with_win)


# %% [markdown]
# # Cell 11 — Recent form không nhìn vào tương lai
#
# `sort_values` bảo đảm đúng trình tự. `rolling(5)` chỉ dùng tối đa năm game ở
# thời điểm hiện tại; trong prediction chính, fixture cutoff còn loại cả ngày
# trận cần dự đoán để tránh leakage từ timestamp không đủ chi tiết.

# %%
t1_form = (
    team_games.loc[team_games["team_name"] == TEAM_A, ["played_at", "game_id", "win"]]
    .sort_values(["played_at", "game_id"])
    .assign(rolling_win_rate_5=lambda frame: frame["win"].rolling(5, min_periods=1).mean())
)
print(t1_form.tail(10))


# %% [markdown]
# # Cell 12 — Kết luận đúng chuẩn
#
# Khi viết report, dùng cấu trúc:
#
# 1. **Finding:** A cao/thấp hơn B ở metric nào.
# 2. **Evidence:** con số, sample, time window.
# 3. **Interpretation:** ý nghĩa trong game.
# 4. **Limitation:** opponent/role/patch/missing/sample.
# 5. **Scenario:** điều kiện khiến lợi thế phát huy.

# %%
print(
    "EDA hoàn tất. Hãy đọc bảng so sánh cùng sample size; "
    "không kết luận nhân quả từ correlation và không xếp hạng champion từ 1 game."
)


# %% [markdown]
# # Cell 13 — Chuẩn bị Matplotlib/Seaborn an toàn
#
# **Mục tiêu:** bật phần biểu đồ khi scientific stack đã được cài.
# **Vì sao kiểm tra trước?** Notebook vẫn phải chạy được phần Pandas cốt lõi trên
# máy chưa có package; nó không được dừng giữa bài chỉ vì thiếu thư viện optional.

# %%
import importlib.util
import os

# Đặt cache trong project để Matplotlib không cần ghi vào user home bị hạn chế.
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

HAS_PLOTS = all(
    importlib.util.find_spec(package) is not None
    for package in ("matplotlib", "seaborn")
)

if HAS_PLOTS:
    import matplotlib

    # Khi chạy file `.py` từ terminal, dùng backend không cần cửa sổ/Tk và lưu
    # PNG. Trong VS Code notebook, ipykernel giữ backend inline để hiện hình.
    HEADLESS = "ipykernel" not in sys.modules
    if HEADLESS:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Một theme chung làm màu, font và grid nhất quán giữa các figure.
    sns.set_theme(style="whitegrid", context="notebook")
    FIGURE_DIR = ROOT / "reports" / "figures" / "notebook"
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Visualization ready; figures sẽ lưu ở {FIGURE_DIR}")
else:
    print(
        "Bỏ qua Cell 14–19 vì chưa có Matplotlib/Seaborn. "
        "Chạy scripts/setup_vscode.ps1 sau khi được phép cài package."
    )


# %% [markdown]
# # Cell 14 — Univariate: histogram/KDE và boxplot
#
# **Câu hỏi:** GDM phân bố ra sao, có lệch hoặc có observation cực đoan không?
# Histogram/KDE cho hình dạng phân phối; boxplot cho median, IQR và outlier candidate.

# %%
if HAS_PLOTS:
    figure, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    sns.histplot(data=team_games, x="gdm", bins=30, kde=True, color="#00A6A6", ax=axes[0])
    axes[0].axvline(0, color="#333333", linewidth=1, linestyle="--")
    axes[0].set(title="Phân phối GDM của các đội LCK S16", xlabel="Gold differential / minute", ylabel="Số team-game")

    sns.boxplot(data=team_games, x="gdm", color="#F4B942", ax=axes[1])
    axes[1].axvline(0, color="#333333", linewidth=1, linestyle="--")
    axes[1].set(title="Boxplot phát hiện GDM cực đoan", xlabel="Gold differential / minute")
    figure.suptitle(f"Univariate EDA • n={len(team_games):,} team-game", fontweight="bold")
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "01_gdm_distribution.png", dpi=160, bbox_inches="tight")
    if not HEADLESS:
        plt.show()
    plt.close(figure)


# %% [markdown]
# # Cell 15 — Numerical × categorical: violin theo role
#
# **Câu hỏi:** DPM có distribution khác nhau thế nào giữa TOP/JUNGLE/MID/BOT/SUPPORT?
# Violin thể hiện mật độ, box bên trong giúp đọc median/quartile. Không so raw DPM
# khác role để kết luận tuyển thủ nào “giỏi hơn” vì nhiệm vụ trong game khác nhau.

# %%
if HAS_PLOTS:
    role_order = ["TOP", "JUNGLE", "MID", "BOT", "SUPPORT"]
    figure, axis = plt.subplots(figsize=(11, 5))
    sns.violinplot(
        data=player_games,
        x="role",
        y="dpm",
        order=role_order,
        hue="role",
        palette="Set2",
        inner="quartile",
        cut=0,
        legend=False,
        ax=axis,
    )
    axis.set(
        title=f"DPM phải được đọc trong baseline của từng role • n={player_games['dpm'].notna().sum():,}",
        xlabel="Vị trí",
        ylabel="Damage per minute",
    )
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "02_player_dpm_by_role.png", dpi=160, bbox_inches="tight")
    if not HEADLESS:
        plt.show()
    plt.close(figure)


# %% [markdown]
# # Cell 16 — Categorical × categorical: 100% stacked bar
#
# **Câu hỏi:** tỷ trọng thắng/thua ở blue side và red side khác nhau thế nào?
# Dùng tỷ lệ giúp so sánh dù số trận mỗi side khác nhau; bảng count ở Cell 7 vẫn
# phải đi kèm để người đọc biết mẫu số.

# %%
if HAS_PLOTS:
    side_plot = side_rates.rename(columns={0: "Thua", 1: "Thắng"})
    axis = side_plot.plot(
        kind="barh",
        stacked=True,
        color=["#E45756", "#00A6A6"],
        figsize=(9, 4),
    )
    axis.set(title="Kết quả theo side — tỷ trọng trong từng nhóm", xlabel="Tỷ trọng", ylabel="Side")
    axis.xaxis.set_major_formatter(lambda value, position: f"{value:.0%}")
    axis.legend(title="Kết quả", loc="lower right")
    axis.figure.tight_layout()
    axis.figure.savefig(FIGURE_DIR / "03_side_outcome_stacked.png", dpi=160, bbox_inches="tight")
    if not HEADLESS:
        plt.show()
    plt.close(axis.figure)


# %% [markdown]
# # Cell 17 — Numerical × numerical: bubble scatter
#
# **Câu hỏi:** khả năng tạo lợi thế kinh tế trung bình có đi cùng win rate không?
# Mỗi điểm là một đội; kích thước bubble là số game để không che giấu sample size.
# Đường trend/correlation chỉ mô tả association, không chứng minh GDM gây ra thắng.

# %%
if HAS_PLOTS:
    team_bubbles = (
        team_games.groupby("team_name", observed=True)
        .agg(games=("game_id", "count"), win_rate=("win", "mean"), avg_gdm=("gdm", "mean"))
        .reset_index()
    )
    figure, axis = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=team_bubbles,
        x="avg_gdm",
        y="win_rate",
        size="games",
        sizes=(100, 500),
        hue="win_rate",
        palette="viridis",
        legend="brief",
        ax=axis,
    )
    for row in team_bubbles.itertuples():
        axis.annotate(row.team_name, (row.avg_gdm, row.win_rate), xytext=(5, 4), textcoords="offset points", fontsize=8)
    axis.axvline(0, color="#555555", linewidth=1, linestyle="--")
    axis.set(title="Lợi thế kinh tế và win rate của 10 đội LCK S16", xlabel="Average GDM", ylabel="Win rate")
    axis.yaxis.set_major_formatter(lambda value, position: f"{value:.0%}")
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "04_team_economy_win_bubble.png", dpi=160, bbox_inches="tight")
    if not HEADLESS:
        plt.show()
    plt.close(figure)


# %% [markdown]
# # Cell 18 — Correlation heatmap
#
# **Câu hỏi:** các metric số biến thiên cùng nhau theo hướng nào?
# Heatmap giúp scan nhiều cặp feature; khi hai feature tương quan quá cao, cần cẩn
# trọng multicollinearity trước khi đưa cả hai vào Logistic Regression.

# %%
if HAS_PLOTS:
    figure, axis = plt.subplots(figsize=(11, 8))
    sns.heatmap(
        correlation,
        cmap="vlag",
        center=0,
        vmin=-1,
        vmax=1,
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.4,
        cbar_kws={"label": "Pearson correlation"},
        ax=axis,
    )
    axis.set_title("Correlation matrix — dùng để sinh giả thuyết, không kết luận nhân quả")
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "05_correlation_heatmap.png", dpi=160, bbox_inches="tight")
    if not HEADLESS:
        plt.show()
    plt.close(figure)


# %% [markdown]
# # Cell 19 — Time-series: phong độ rolling
#
# **Câu hỏi:** form 5 game của hai đội thay đổi theo thứ tự trận thế nào?
# Trục x dùng thứ tự game thay vì ép các ngày thiếu trận thành dữ liệu giả. Rolling
# window làm mượt nhiễu nhưng vẫn phải đọc kèm kết quả từng game và đối thủ.

# %%
if HAS_PLOTS:
    form_comparison = (
        selected_teams[["team_name", "played_at", "game_id", "win"]]
        .sort_values(["team_name", "played_at", "game_id"])
        .assign(
            game_order=lambda frame: frame.groupby("team_name").cumcount() + 1,
            rolling_win_rate_5=lambda frame: frame.groupby("team_name")["win"].transform(
                lambda series: series.rolling(5, min_periods=1).mean()
            ),
        )
    )
    figure, axis = plt.subplots(figsize=(12, 5))
    sns.lineplot(
        data=form_comparison,
        x="game_order",
        y="rolling_win_rate_5",
        hue="team_name",
        palette=["#E45756", "#00A6A6"],
        linewidth=2,
        ax=axis,
    )
    axis.set(title=f"Rolling 5-game form: {TEAM_A} vs {TEAM_B}", xlabel="Thứ tự game trong S16", ylabel="Rolling win rate (5 game)")
    axis.yaxis.set_major_formatter(lambda value, position: f"{value:.0%}")
    figure.tight_layout()
    figure.savefig(FIGURE_DIR / "06_rolling_form_comparison.png", dpi=160, bbox_inches="tight")
    if not HEADLESS:
        plt.show()
    plt.close(figure)
