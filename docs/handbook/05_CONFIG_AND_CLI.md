# 05 — Config and CLI

**Prerequisites:** 02, 04. **Phone mode:** đầy đủ. **Source:** `configs/project.json`, `src/config.py`, `src/cli.py`.

## 🧠 Mental Model

Config là contract trung tâm; CLI là dispatch layer. Command không tự đoán nguồn hay season.

## 📥 Config input

Các invariant quan trọng:

```json
{
  "season": "S16",
  "season_start_date": "2026-01-01",
  "tracked_lck_teams": "10 unique canonical teams",
  "update_policy": "24h freshness, timeout, retries, rate limit"
}
```

## ⚙️ Step-by-Step — `load_config`

1. Mở JSON bằng `Path.open(..., encoding="utf-8")`.
2. Kiểm tra required keys.
3. Reject nếu `season != S16`.
4. Reject nếu start date trước `2026-01-01`.
5. Reject nếu không đúng 10 đội hoặc duplicate canonical name.
6. Tạo frozen `ProjectConfig` + `UpdatePolicy`.

## 📤 Verified output

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli show-config
```

Representative output:

```json
{
  "project_name": "lol-pro-analytics-s16",
  "season": "S16",
  "season_start_date": "2026-01-01",
  "tracked_team_count": 10,
  "statistics_source": "https://gol.gg/esports/home/"
}
```

## 🧪 Simulated Lab — invalid season

```text
raw["season"] = "S15"
↓
if raw["season"] != "S16"
↓
raise ValueError("The project is locked to Season S16.")
```

Đây là `SOURCE-BACKED` và được bảo vệ bởi `test_config_is_locked_to_s16_and_ten_teams`.

## 📱 Run Without Running

`python -m src.cli quality-check` → import parser → load config → resolve DB → execute quality checks → write JSON/Markdown → return status. Success nghĩa `status=passed`; không có nghĩa mọi field nguồn đều non-null.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli --help
.\.venv-vscode\Scripts\python.exe -m src.cli health
.\.venv-vscode\Scripts\python.exe -m src.cli freshness
```

## 🧪 Automated Test

`test_cli_help_without_error`, `test_cli_health`, `test_config_is_locked_to_s16_and_ten_teams`.

## 🎤 Defense

1. Config validation chạy ở đâu?
2. Vì sao config frozen? Tránh sửa policy sau khi load.
3. `freshness` đo gì? Age của latest successful update so với max age.
4. CLI có phải business logic không? Không; nó điều phối.
5. Nếu command chạy sai working directory? Dùng VS Code workspace root và `python -m`.

## ✅ Checkpoint

- [ ] Tôi biết `ProjectConfig.root` tạo path nào.
- [ ] Tôi biết invalid S15 bị reject trước analysis.
- [ ] Tôi biết exact command health/show-config/freshness.
