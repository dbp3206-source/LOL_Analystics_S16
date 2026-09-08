# 18 — Operations: cập nhật hằng ngày và dữ liệu stale

## 🧠 Mental Model

Data product tốt có vòng đời: update → validate → publish → monitor → explain failure. Freshness là một feature hiển thị, không phải lời hứa tuyệt đối.

## 📱 Phone Mode

**RUNTIME-VERIFIED** health snapshot: status `ok`, season `S16`, teams `10`; freshness `fresh`, last successful update `2026-09-07T17:04:38+00:00`, age khoảng 16.9h dưới ngưỡng 24h tại lần kiểm tra.

## 📥 Input

Source availability, update policy, cache, previous DB snapshot, current date/time.

## ⚙️ Step-by-Step Execution

1. Run health/config.
2. Run scoped/all-team update.
3. Cache raw pages.
4. Upsert idempotently.
5. Quality + source audit.
6. Generate reports/figures.
7. Re-run freshness and tests.

## 📤 Output

DB snapshot, update log, quality report, source audit, artifacts, freshness state.

## 🔍 Đọc output

Fresh ≠ complete; complete ≠ correct; correct ≠ predictive. Đọc cả source audit và coverage.

## 🧪 Simulated Lab

Nếu `age > max_age_hours`, UI chuyển amber/stale, prediction caveat tăng; không xoá dữ liệu cuối cùng.

## ❌ What If?

- Gol.gg rate limit: giữ last-known-good + log lỗi.
- Một team fail: publish partial với scope clearly marked, hoặc fail closed tùy policy.
- Source schema drift: dừng publish chart phụ thuộc field đó.

## 💻 Try It Yourself

Đọc `docs/RUNBOOK.md`; dùng `health`, `show-config`, `freshness` commands documented ở repo.

## 🧪 Automated Test

`tests/test_config.py`, `test_quality.py`, `test_schedule.py` thuộc 31/31 pass.

## 🛠 Nếu kết quả sai thì debug ở đâu?

Timestamp/timezone → update log → raw cache → DB counts → quality → artifacts.

## 🎤 Bạn phải tự giải thích được

Last-known-good, idempotence, partial update, freshness SLA và rollback snapshot.

## ✅ Checkpoint

Bạn có runbook một ngày cập nhật và biết khi nào phải nói “dữ liệu stale”.

### 📍 Good stopping point

Không demo prediction mà không đọc freshness trước.

