# 09 — NumPy và Pandas: công cụ tư duy dữ liệu

## 🧠 Mental Model

NumPy xử lý vector/mảng số; Pandas gắn vector với index, column và groupby. Mục tiêu là thao tác theo cột, reproducible, tránh vòng lặp sai grain.

## 📱 Phone Mode

```python
import pandas as pd
df = pd.DataFrame({"team": ["T1", "T1", "HLE"], "win": [1, 0, 1]})
df.groupby("team", as_index=False)["win"].mean()
```

Output: T1 `0.5`, HLE `1.0`. Đây là **SOURCE-DERIVED SIMULATION** để hiểu cú pháp; metrics production nằm ở `src/analysis/metrics.py`.

## 📥 Input

SQL rows/dataframes: team-game, player-game, champion-game, timeline.

## ⚙️ Step-by-Step Execution

1. `read_sql` lấy đúng columns.
2. Kiểm tra `shape`, `dtypes`, `head`, missing.
3. Dùng `assign`, `loc`, `groupby`, `agg`, `merge` có key.
4. Giữ raw frame bất biến; tạo curated/summary frame.
5. Sort theo date trước rolling.
6. Export CSV/Markdown/figure.

## 📤 Output

DataFrame summary có denominator, ví dụ `games`, `wins`, `win_rate`; không chỉ một số tỷ lệ.

## 🔍 Đọc output

`shape=(n, p)` cho biết sample size và feature count. `info()` cho dtype/missing. Luôn xem 3 dòng đầu, 3 dòng cuối và một group nhỏ.

## 🧪 Simulated Lab

```python
import numpy as np
np.mean([1, 0, 1])  # 0.666...
```

Nếu `np.mean([])` trả warning/NaN, đó là dấu hiệu thiếu sample, không phải 0%.

## ❌ What If?

- `SettingWithCopyWarning`: dùng `.loc`/`.copy()`.
- Merge nhân đôi: kiểm tra uniqueness của key ở hai bên.
- Sort sai trước rolling: kết quả phong độ bị leakage thời gian.

## 💻 Try It Yourself

```powershell
.\.venv-vscode\Scripts\python.exe -m src.analysis.pandas_eda
```

Nếu module không có entrypoint trực tiếp, dùng CLI/report command trong `docs/RUNBOOK.md`; đây là **LIMITATION** của handbook, không tự suy diễn command mới.

## 🧪 Automated Test

`tests/test_eda.py` bảo vệ output EDA. 31/31 tests pass (**TEST-VERIFIED**).

## 🛠 Nếu kết quả sai thì debug ở đâu?

In `shape`, `columns`, `dtypes`, sample rows; sau đó kiểm tra SQL grain và join keys.

## 🎤 Bạn phải tự giải thích được

Vì sao `groupby.mean()` cần kèm `count`; vì sao rolling phải theo thời gian; vì sao NumPy array không tự biết team/player.

## ✅ Checkpoint

Bạn viết được một summary frame có `wins`, `games`, `win_rate`, `mean`, `median`, `std` và giải thích từng column.

### 📍 Good stopping point

Khi bạn đọc DataFrame như một bảng dữ liệu có grain, không chỉ như spreadsheet.

