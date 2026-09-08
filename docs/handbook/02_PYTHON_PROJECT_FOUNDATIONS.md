# 02 — Python Project Foundations

**Prerequisites:** Python cơ bản. **Phone mode:** đầy đủ bằng toy examples. **Source:** `src/config.py`, `src/cli.py`, `src/storage/database.py`.

## 🧠 Mental Model

Một project nhiều module là một đồ thị trách nhiệm, không phải một file khổng lồ. `src.cli` điều phối; collection lấy dữ liệu; storage ghi DB; analysis tạo insight; modeling dự đoán.

## 🧩 Concepts thực sự dùng

| Concept | Ví dụ project | Vì sao cần |
|---|---|---|
| Package | `src/analysis/__init__.py` | Python nhận diện module tree |
| `python -m` | `python -m src.cli health` | Chạy module với import path đúng |
| Dataclass | `ProjectConfig`, `GamePlayerStat` | Object có field rõ ràng |
| Frozen dataclass | `UpdatePolicy` | Policy không bị sửa ngẫu nhiên |
| Type hint | `Path | str`, `dict[str, Any]` | Đọc contract, hỗ trợ IDE |
| `Path` | `config.root / "data"` | Path portable hơn chuỗi nối tay |
| Context manager | `with closing(connect_database(...))` | Đóng connection ngay cả khi lỗi |
| Exception | `raise ValueError(...)` | Fail fast khi invariant sai |
| JSON | `project.json`, reports | Config/report machine-readable |
| Logging | `configure_logging` | Tách vận hành khỏi `print` |
| argparse | `build_parser` | CLI có help và validation |

## 📱 Phone Mode — `Path` mental execution

```python
root = Path("project")
database = root / "data" / "lol_analytics.db"
```

Trace:

```text
root                  = project
root / "data"         = project/data
... / "lol_analytics.db" = project/data/lol_analytics.db
```

`Path` không mở file; nó chỉ biểu diễn địa chỉ. File được tạo khi code gọi `open`, `write_text`, SQLite connection hoặc `mkdir`.

## 📥 Input → ⚙️ Execution → 📤 Output

```powershell
python -m src.cli health
```

`python -m` tìm package → import `src.cli` → parser đọc subcommand `health` → `run_health` load config → validate invariants → print JSON.

Representative runtime output:

```json
{"status": "ok", "season": "S16", "teams": 10}
```

## 🧪 Simulated Lab — context manager

```python
with closing(connect_database(path)) as connection:
    rows = connection.execute("SELECT 1").fetchall()
```

Mental execution: mở connection → chạy query → block kết thúc → `closing` gọi `.close()`. Nếu query raise exception, resource vẫn được đóng.

## ❌ What If?

```python
python src/cli.py health
```

Có thể import behavior khác so với `python -m src.cli`, đặc biệt khi project root không ở `sys.path`. Dùng command trong README/VS Code tasks để giữ import ổn định.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m src.cli --help
.\.venv-vscode\Scripts\python.exe -m src.cli show-config
```

## 🧪 Automated Test

`test_cli_help_without_error` bảo vệ parser/help; `test_cli_health` bảo vệ config và runtime health.

## 🎤 Defense

- `dataclass` khác dictionary ở đâu? Dataclass làm contract field/type rõ hơn.
- Vì sao `Path` tốt hơn string? Có operator path, portable separator và API filesystem.
- Vì sao `raise` thay vì silently continue? Invariant sai làm output sau đó không đáng tin.
- Vì sao logging không thay `print` hoàn toàn? CLI vẫn cần JSON output; logging dành cho operational context.

## ✅ Checkpoint

- [ ] Tôi giải thích được `python -m`.
- [ ] Tôi trace được một `Path` expression.
- [ ] Tôi biết context manager bảo vệ resource nào.

### 📍 Good stopping point

Đọc [03 — DA/DS foundations](03_DA_DS_FOUNDATIONS.md) trước khi đi vào scraper.
