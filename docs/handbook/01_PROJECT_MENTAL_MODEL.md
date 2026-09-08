# 01 — Project Mental Model

**Prerequisites:** Không. **Phone mode:** đầy đủ. **Laptop:** optional. **Source:** `README.md`, `configs/project.json`, `src/cli.py`.

## 🧠 Mental Model

Project trả lời một câu hỏi nghiệp vụ bằng một đường truy vết:

```text
Question
 → scope S16 / entity / cutoff
 → Gol.gg HTML hoặc fixture schedule
 → parsed Python records
 → SQLite facts
 → cleaning + 12 quality gates
 → DataFrame / metrics / statistics
 → figures / prediction / Streamlit / report
```

Nó không phải một biểu đồ đơn lẻ và cũng không phải một model dự đoán tự động. Chất lượng của output phụ thuộc cả lineage, grain, sample size và thời điểm dữ liệu.

## 📱 Phone Mode — Hãy tưởng tượng chương trình chạy

Giả sử bạn hỏi: “So sánh T1 và HLE trong S16”.

1. UI/CLI xác định `team_a_id=2809`, `team_b_id=2805`.
2. Config khóa `season=S16`, `season_start_date=2026-01-01`.
3. Query lấy những rows trong SQLite trước cutoff.
4. Metrics tạo win rate, GPM, GDM, DPM, objectives, champion pool, H2H.
5. Statistics thêm uncertainty; visualization chọn chart theo câu hỏi.
6. Nếu fixture tương lai không tồn tại, predictor gắn `hypothetical`.

### ❓ Predict trước khi đọc output

Nếu một đội có 3 wins/4 games, raw win rate là bao nhiêu?

### ✅ Đáp án

`3 / 4 = 0.75 = 75%`. Đây là mô tả sample, chưa phải xác suất tương lai chắc chắn.

## 📥 Input

| Input | Ví dụ | Ý nghĩa |
|---|---|---|
| User query | `T1 vs HLE` | Câu hỏi nghiệp vụ |
| Config | `S16`, 10 primary teams | Ràng buộc phạm vi |
| Raw HTML | Gol.gg game page | Bằng chứng nguồn |
| SQLite | `team_game_stats` | Analytical grain |
| Parameters | rolling window `5` | Quyết định phân tích |

## 📤 Output

Đầu ra không chỉ là `probability`: tables, CSV, JSON manifest, PNG/SVG figures, Streamlit screen, final Markdown report và test evidence.

## 🔗 Nó nối với phần nào tiếp theo?

- Python packaging giải thích tại sao chạy `python -m src.cli` ở [02](02_PYTHON_PROJECT_FOUNDATIONS.md).
- Source map nằm ở [04](04_REPOSITORY_ARCHITECTURE.md).
- Lineage cụ thể của win rate, DPM, champion pool, rolling form và prediction nằm ở [22](22_DATA_LINEAGE_AND_TRACEABILITY.md).

## 🧪 Simulated Lab — một game đi qua hệ thống

Toy input:

```text
HTML: team=T1, kills=15, win=1
```

Trace:

```text
BeautifulSoup → "T1", "15", "1"
int("15") → 15
bool/int result → win=1
GameTeamStat(team_id=2809, kills=15, win=1)
SQLite team_game_stats row
DataFrame row
groupby(team)[win].mean()
```

## ❌ What If?

| Tình huống | Hệ quả |
|---|---|
| Dùng S15 | Model/metrics sai scope; config/test phải chặn |
| Gộp player Support với Bot raw DPM | So sánh lệch baseline role |
| Dùng target game trong historical feature | Data leakage |
| Gọi matchup không có fixture là trận tiếp theo | Overclaim nghiệp vụ |

## 🎤 Bạn phải tự giải thích được

1. Vì sao raw HTML cần lưu?
2. Grain của một team-game row là gì?
3. Vì sao missing không tự biến thành zero?
4. Vì sao prediction cần cutoff?
5. Vì sao output phải có sample size?

## ✅ Checkpoint

- [ ] Tôi mô tả được pipeline bằng một dòng.
- [ ] Tôi phân biệt mô tả dữ liệu và dự đoán.
- [ ] Tôi biết mọi insight phải truy ngược về raw/source.

### 📍 Good stopping point

Khi quay lại, đọc **02 — Python project foundations** để hiểu các khối ngôn ngữ tạo pipeline.
