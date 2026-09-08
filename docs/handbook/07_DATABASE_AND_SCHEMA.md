# 07 — SQLite, schema và database-first thinking

## 🧠 Mental Model

Database là “nguồn sự thật đã chuẩn hoá” cho app, không phải nơi giấu lỗi collector. Dimension (`teams`, `players`, `champions`) mô tả thực thể; fact (`games`, `player_game_stats`, `team_game_stats`, `draft_actions`, `timeline_events`) mô tả sự kiện.

## 📱 Phone Mode

Snapshot **RUNTIME-VERIFIED**:

```text
games 667 | series 271 | draft_actions 13,340 | players 152
player_game_stats 6,670 | team_game_stats 1,248
```

Một game có 10 player rows và 20 draft actions; đó là grain, không phải “số trận thắng”.

## 📥 Input

`connect_database()` nhận `Path`; `initialize_database()` chạy schema/migrations; `upsert_parsed_game()` nhận `ParsedGame`; `upsert_fullstats()` nhận fullstats bổ sung.

## ⚙️ Step-by-Step Execution

1. Load config và đảm bảo runtime directories.
2. Connect SQLite với foreign keys.
3. Tạo bảng/idempotent schema.
4. Upsert dimension trước, fact sau.
5. Refresh current-starter flags và derived economy.
6. Chạy `table_counts`, quality checks, EDA.

`src/storage/database.py` còn sửa scope team và loại academy theo config. Không sửa record bằng tay trong DB để “làm đẹp” kết quả.

## 📤 Output

Các bảng chính xem tại `docs/DATA_SCHEMA.md`. Query ví dụ:

```sql
SELECT team_name, COUNT(*) AS games, AVG(win) AS win_rate
FROM team_game_stats GROUP BY team_name;
```

## 🔍 Đọc output

`AVG(win)` là tỷ lệ thắng nếu `win` nhị phân. Luôn kiểm tra denominator (`COUNT(*)`) và season/tournament scope trước khi so sánh.

## 🧪 Simulated Lab

| game_id | team | win |
|---:|---|---:|
| 1 | T1 | 1 |
| 2 | T1 | 0 |

`COUNT=2`, `AVG=0.5`; một record thiếu win không được tự coi là 0.

## ❌ What If?

- Duplicate game: xem unique key và upsert, không cộng lần hai.
- `table_counts` lệch: tìm ingestion log rồi chạy lại idempotent.
- DB stale: xem freshness, không suy luận “đội yếu”.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli health
.\.venv-vscode\Scripts\python.exe -m src.cli show-config
```

## 🧪 Automated Test

`tests/test_database.py`, `tests/test_schema.py`, `tests/test_upsert.py` kiểm tra schema, key và idempotence. **TEST-VERIFIED**: 31/31 pass ở lần chạy gần nhất.

## 🛠 Nếu kết quả sai thì debug ở đâu?

Theo thứ tự: schema → upsert key → scope repair → derived columns → metric query. Không bắt đầu ở chart.

## 🎤 Bạn phải tự giải thích được

Grain của `player_game_stats` là player-game; grain của `team_game_stats` là team-game. Join sai grain là nguyên nhân phổ biến làm nhân đôi games.

## ✅ Checkpoint

Bạn đọc được schema, viết một `GROUP BY` có denominator, và giải thích vì sao upsert chạy lại không tạo duplicate.

### 📍 Good stopping point

Bạn sẵn sàng sang cleaning khi đã phân biệt được raw table, curated table và derived metric.

