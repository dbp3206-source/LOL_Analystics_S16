# 19 — Reporting: biến output thành câu chuyện nghiên cứu

## 🧠 Mental Model

Report phải dẫn người đọc từ question → data → method → evidence → limitation → decision. Không paste toàn bộ notebook mà thiếu kết luận.

## 📱 Phone Mode

Đọc theo thứ tự: executive answer, scope/as-of, KPI table, comparison chart, recent form, player/role deep dive, prediction, caveats, appendix.

## 📥 Input

EDA outputs, statistics, visual artifacts, prediction/backtest, source/quality reports.

## ⚙️ Step-by-Step Execution

1. State user question.
2. Declare S16/LCK/primary scope.
3. Show sample/denominators.
4. Present 3–5 findings with visuals.
5. Explain matchup scenarios.
6. Give conditional prediction.
7. Separate fact, inference, recommendation.

## 📤 Output

`reports/final_report.md`, `reports/statistics/statistics_report.md`, `reports/eda/`, figures và README gallery.

## 🔍 Đọc output

Mọi headline phải truy ngược tới table/figure/source. Nếu không, đó là narrative không audit được.

## 🧪 Simulated Lab

Claim “HLE mạnh early”: cần GD15/CSD15/objective timing, denominator, opponent scope và chart; không chỉ cảm giác.

## ❌ What If?

- Findings mâu thuẫn: nói rõ và đề xuất dữ liệu/experiment tiếp.
- Chart đẹp nhưng không action: cắt.
- Prediction uncertainty rộng: trình bày scenarios thay vì false precision.

## 💻 Try It Yourself

Mở `reports/release-readiness-2026-09-08.md`, `README.md`, `docs/03_DA_DS_PLAYBOOK.md`.

## 🧪 Automated Test

`tests/test_reporting.py`/related report checks thuộc suite; full 31 pass.

## 🛠 Nếu kết quả sai thì debug ở đâu?

Claim → figure/table → metric → data lineage → source audit.

## 🎤 Bạn phải tự giải thích được

Khác biệt insight, finding, recommendation, prediction và causal claim.

## ✅ Checkpoint

Bạn viết một đoạn kết luận mà người đọc biết scope, bằng chứng, uncertainty và next action.

### 📍 Good stopping point

Report hoàn chỉnh khi người khác reproduce được từ runbook.

