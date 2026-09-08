# Handbook coverage audit

## Scope audited

Repository source/docs/tests were inspected before writing this handbook. Inventory: 34 Python files under source/app/scripts/tests, approximately 5,729 lines and 195 definitions. Production definitions have docstrings; missing docstrings are limited to test class/method helpers.

## Coverage matrix

| Area | Chapter | Status |
|---|---|---|
| Entry/learning order | 00–05 | covered |
| Python foundations | 02 | covered |
| DA/DS reasoning | 03, 10–15 | covered |
| Scraping/parsing | 06 | covered |
| DB/schema | 07 | covered |
| Cleaning/quality | 08 | covered |
| NumPy/Pandas | 09 | covered |
| EDA/metrics | 10 | covered |
| Statistics | 11 | covered |
| Visualization | 12 | covered |
| Prediction/logistic | 13–15 | covered |
| Streamlit | 16 | covered |
| Tests/reproducibility | 17 | covered |
| Operations/freshness | 18 | covered |
| Reports | 19 | covered |
| File reference | 20 | covered |
| Function reference | 21 | covered |
| Lineage | 22 | covered |
| Capability testing | 23 | covered |
| Debugging | 24 | covered |
| Demo/defense | 25–26 | covered; 100 questions |
| Exercises/glossary | 27–28 | covered |
| Limitations/cheatsheet | 29–30 | covered |
| Mobile-first mode | all chapters | covered |

## Runtime evidence

- `health`: status `ok`, S16, 10 teams — **RUNTIME-VERIFIED**.
- `show-config`: project/source/season — **RUNTIME-VERIFIED**.
- freshness: last update 2026-09-07T17:04:38Z, fresh under 24h at audit — **RUNTIME-VERIFIED**.
- full tests: `Ran 31 tests ... OK` — **TEST-VERIFIED**.
- snapshot: 667 games, 271 series, 13,340 draft actions, 152 players — **RUNTIME-VERIFIED**.

## Honest gaps

- No claim of a new live internet refresh in this handbook.
- No browser/mobile screenshot smoke test executed in this audit.
- Runtime SQLite/raw files are intentionally not committed.
- Future schedule availability depends on source and current date.
- Visual quality still needs human inspection when generated artifacts change.

## Review protocol

1. Open `00_START_HERE.md` on phone.
2. Follow chapter order.
3. Run commands from `docs/RUNBOOK.md` in VS Code.
4. Compare outputs with labels and existing reports.
5. Run full tests before commit.
6. Re-run this audit when source/schema changes.

