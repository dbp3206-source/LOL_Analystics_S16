# 10 — EDA, metrics và câu hỏi nghiệp vụ

## 🧠 Mental Model

EDA trả lời “dữ liệu đang kể câu chuyện gì và có đáng tin không?” Metrics chuyển fact thành bằng chứng: win rate, KDA, DPM, CSM, GD@15, CSD@15, champion pool, side split, objective timing.

## 📱 Phone Mode

Snapshot **RUNTIME-VERIFIED**: 6,670/6,670 DPM/CSM, 6,660/6,670 GD15/CSD15 trong player-game scope. Đừng đọc “6,660” như 6,660 games: đó là player-game rows có metric.

## 📥 Input

Curated team/player/game tables và câu hỏi: đội nào ổn định? tuyển thủ nào vượt role baseline? matchup nào có lợi?

## ⚙️ Step-by-Step Execution

1. Define question và unit of analysis.
2. Describe counts/missing/duplicates.
3. Compute team/player/champion summaries.
4. Compare recent rolling form với season aggregate.
5. Segment by side, role, tournament, opponent.
6. Visualize uncertainty/context.
7. Write insight + caveat + action.

Hàm production: `team_summary`, `player_summary`, `champion_pool`, `head_to_head`, `rolling_form`, `compare_players`, `compare_teams`.

## 📤 Output

Một insight tốt gồm: metric, numerator/denominator, comparison baseline, time window, limitation.

Ví dụ: “T1 có 8/12 wins = 66.7% trong selected scope; không đồng nghĩa xác suất trận tới là 66.7%.”

## 🔍 Đọc output

KDA cao nhưng sample 2 games không thể xếp trên 30 games nếu không báo sample size. DPM cần hiểu thời lượng game và role.

## 🧪 Simulated Lab

| team | wins | games | win_rate |
|---|---:|---:|---:|
| T1 | 8 | 12 | 0.667 |
| HLE | 7 | 12 | 0.583 |

Khoảng cách 8.4 điểm phần trăm là mô tả; cần uncertainty/statistical test trước claim mạnh.

## ❌ What If?

- Aggregate và recent form trái chiều: trình bày cả hai, không chọn số “đẹp”.
- Champion win rate 100% trên 1 game: label small sample.
- Role mismatch: compare cùng role trước, rồi mới cross-role exploratory.

## 💻 Try It Yourself

Đọc `docs/03_DA_DS_PLAYBOOK.md`, sau đó chạy commands trong `docs/RUNBOOK.md` cho team/player/compare.

## 🧪 Automated Test

`tests/test_metrics.py`, `tests/test_eda.py` và `tests/test_backtest.py`; 31/31 pass (**TEST-VERIFIED**).

## 🛠 Nếu kết quả sai thì debug ở đâu?

Metric definition → SQL grain → filters → denominator → rounding → chart annotation.

## 🎤 Bạn phải tự giải thích được

KDA không phải skill tổng quát; CSD@15 là lane pressure proxy; win rate là outcome; DPM là damage efficiency phụ thuộc role/game state.

## ✅ Checkpoint

Bạn trả lời được một câu hỏi bằng bảng số, một biểu đồ, một uncertainty/caveat và một khuyến nghị có điều kiện.

### 📍 Good stopping point

Chuyển sang statistics khi EDA đã phát hiện pattern nhưng bạn chưa gọi đó là “có ý nghĩa”.

