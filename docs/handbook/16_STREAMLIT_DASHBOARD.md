# 16 — Streamlit dashboard: biến pipeline thành sản phẩm

## 🧠 Mental Model

Streamlit là presentation layer đọc curated DB và reports; không nên âm thầm scrape/mutate data trong mỗi lần người dùng đổi filter.

## 📱 Phone Mode

Các tab dự kiến: Overview, Team, Player, Compare, Prediction, Data Health. Mỗi tab phải nói source/as-of/freshness và empty state.

## 📥 Input

URL/local app, selected team/player, date/season filters, SQLite snapshot và generated reports.

## ⚙️ Step-by-Step Execution

1. App load config.
2. Connect/read-only DB.
3. Build rows via `_team_rows`, `_player_rows`, `_h2h_rows`…
4. Render tables/charts.
5. Render next fixture/prediction với caveat.
6. Freshness banner báo stale/missing.

## 📤 Output

Interactive tables, Plotly/Matplotlib/Streamlit charts (tuỳ current implementation), prediction card và links to artifacts.

## 🔍 Đọc output

Kiểm tra scope badge `S16`, source, last update, denominator, not just headline number.

## 🧪 Simulated Lab

Chọn `T1` → team summary → player rows → champion pool → next fixture. Nếu chọn đội không tồn tại, app phải empty state chứ không crash.

## ❌ What If?

- DB missing: hướng dẫn chạy sync; không tạo fake rows.
- Stale: cảnh báo và link update command.
- Phone width: bảng dài cần scroll/column selection.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m streamlit run src\app\streamlit_app.py
```

Nếu Streamlit chưa cài, xem dependency setup trong `requirements.txt`; không gọi dashboard “verified” nếu chưa chạy trên máy.

## 🧪 Automated Test

Unit tests bảo vệ helper `_team_summary`, `_player_summary` gián tiếp; UI browser smoke test chưa chạy trong môi trường này (**LIMITATION**).

## 🛠 Nếu kết quả sai thì debug ở đâu?

UI helper → SQL query → DB snapshot → freshness/config. Không sửa chart data trong frontend.

## 🎤 Bạn phải tự giải thích được

Vì sao app read-only, cách xử lý empty/stale state và separation giữa data refresh với visualization.

## ✅ Checkpoint

Bạn demo được một câu hỏi từ filter đến bảng, chart, prediction và source link.

### 📍 Good stopping point

Dashboard đáng tin khi có context + freshness, không chỉ nhiều widget.

