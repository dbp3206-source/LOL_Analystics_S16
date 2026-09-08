# 06 — Scraping và parsing: từ HTML đến record chuẩn

## 🧠 Mental Model

Collector không “lấy mọi thứ trên web”. Nó tải HTML có cache, parser biến HTML thành record có schema, rồi storage mới chịu trách nhiệm ghi dữ liệu. Gol.gg là nguồn thống kê chính; lịch bổ sung chỉ dùng cho fixture.

Luồng: `URL → CachedHttpClient → HTML → parser → ParsedGame/TeamMatch → quality → database`.

## 📱 Phone Mode

Hãy đọc một record giả lập:

```text
input URL: https://gol.gg/game/stats/62810/page-game/
HTTP: 200, cache_hit=false
parser: parse_game_page
output: game_id=62810, teams=HLE/T1, players=10, drafts=20, timeline_events=...
```

Đây là **SOURCE-DERIVED SIMULATION**; số lượng được kiểm chứng trong snapshot là 667 games và 20 draft actions/game, không phải một lần tải internet mới.

## 📥 Input

- Directory/team links: `parse_team_directory`.
- Team match table: `parse_team_match_list`.
- Game page: `parse_game_page`.
- Fullstats page: `parse_fullstats_page`.
- Schedule HTML/Leaguepedia: `parse_schedule_page`.

## ⚙️ Step-by-Step Execution

1. `CachedHttpClient.get()` tạo path cache theo URL an toàn.
2. `read_raw_html()` đọc lại fixture/cache để parser chạy offline.
3. Parser chuẩn hoá text, href/id, số, duration, date.
4. `ParsedGame` tách team stats, player stats, draft và timeline.
5. Updater deduplicate theo game/series/player key.
6. Quality checks bắt missing key, duplicate và S16 scope.

Các hàm chính nằm trong `src/collection/http_client.py`, `game_parsers.py`, `parsers.py`, `schedule.py`.

## 📤 Output

| Record | Dùng cho |
|---|---|
| `ParsedGame` | game/series/team/player/champion/timeline |
| `GameDraftAction` | draft/pick-ban |
| `GameTimelineEvent` | objective timing |
| `ScheduleFixture` | next fixture |

## 🔍 Đọc output

Nếu `players != 10`, parser không được coi game là hoàn chỉnh. Nếu `drafts != 20`, draft analysis phải đánh dấu thiếu. Nếu page không có ngày hoặc team id, record đi vào lỗi/skip có log.

## 🧪 Simulated Lab

HTML tối thiểu:

```html
<table><tr><th>Team</th><th>Result</th></tr><tr><td>T1</td><td>Win</td></tr></table>
```

Kỳ vọng: parser lấy `T1` và `Win`; không suy diễn thêm player/score. Đây là cách kiểm thử parser bằng fixture nhỏ.

## ❌ What If?

- HTML đổi class: parser trả ít rows → xem fixture và `parse_*` trước, không sửa metric.
- HTTP lỗi: cache giúp chạy lại; không coi lỗi mạng là 0 thắng.
- Page Academy xuất hiện: scope repair loại khỏi primary LCK.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m unittest discover -s tests -v
.\.venv-vscode\Scripts\python.exe -m src.cli health
```

## 🧪 Automated Test

`tests/test_parsers.py`, `tests/test_game_parser.py`, `tests/test_schedule.py` bảo vệ parser và schedule. **TEST-VERIFIED**: toàn bộ suite gần nhất `Ran 31 tests ... OK`.

## 🛠 Nếu kết quả sai thì debug ở đâu?

1. `data/raw/` hoặc fixture source.
2. parser dataclass field.
3. `tests/fixtures/` và parser tests.
4. `src/quality/checks.py`.
5. Chỉ sau đó xem `storage/database.py`.

## 🎤 Bạn phải tự giải thích được

Vì sao cache quan trọng? Vì parser phải deterministic và demo được offline. Vì sao không parse bằng regex toàn trang? Vì bảng HTML có cấu trúc, parser theo field giúp phát hiện schema drift.

## ✅ Checkpoint

Bạn vẽ được `HTML → parser → dataclass → DB`, phân biệt raw/parsed/curated và biết log nào chứng minh parser bỏ qua record.

### 📍 Good stopping point

Đọc xong chương này khi bạn có thể viết một fixture HTML 5 dòng và dự đoán output parser trước khi chạy.

