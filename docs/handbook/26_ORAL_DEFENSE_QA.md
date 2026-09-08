# 26 — Oral defense Q&A (100 câu)

Mỗi câu nên trả lời theo mẫu: định nghĩa → ví dụ trong project → limitation → file/evidence.

1. Project giải quyết vấn đề gì? — Phân tích S16 LCK và dự đoán có điều kiện.
2. Vì sao chọn LoL? — Có game/player/draft/timeline phong phú.
3. Nguồn chính? — Gol.gg.
4. Nguồn schedule? — Nguồn bổ sung theo docs.
5. Vì sao chỉ S16? — Up-to-date và scope đã chốt.
6. LCK Challengers có lấy không? — Không.
7. Primary player là gì? — Starter/current scope theo policy.
8. Raw data là gì? — HTML/cache chưa chuẩn hoá.
9. Curated data là gì? — Record clean trong DB.
10. Grain của games? — Một row/game.
11. Grain player stats? — Một row/player-game.
12. Grain team stats? — Một row/team-game.
13. Vì sao grain quan trọng? — Tránh join nhân bản.
14. Cache để làm gì? — Reproducibility/rate-limit.
15. Parser khác scraper? — Scraper tải, parser hiểu cấu trúc.
16. Dataclass lợi gì? — Contract rõ và type-like.
17. HTML schema drift? — Fixture/test và source audit phát hiện.
18. Upsert là gì? — Ghi idempotent theo key.
19. Academy loại ra sao? — Scope repair/business rule.
20. Foreign key để làm gì? — Integrity giữa dimension/fact.
21. Missing khác zero? — Không quan sát khác giá trị 0.
22. Cleaning normalize role? — Canonical join/filter.
23. Quality gate? — Chặn publish khi contract fail.
24. Freshness? — Tuổi dữ liệu so với policy.
25. Win rate formula? — wins/games.
26. Vì sao luôn báo denominator? — Đánh giá sample.
27. KDA là gì? — Kill/Death/Assist ratio theo định nghĩa report.
28. DPM? — Damage per minute.
29. CSM? — Creep score per minute.
30. CSD@15? — CS difference at 15 minutes.
31. GD@15? — Gold difference at 15 minutes.
32. Champion pool? — Picks, wins, rate, usage.
33. H2H limitation? — Small/context-dependent sample.
34. Side split? — Outcome theo blue/red side.
35. Objective timing? — Phân bố thời điểm objective.
36. EDA là gì? — Khám phá chất lượng/pattern.
37. DA khác DS? — Mô tả/quyết định vs dự báo/mô hình.
38. CRISP-DM? — Business, data, prep, model, evaluate, deploy.
39. NumPy dùng gì? — Vector/numeric operations.
40. Pandas dùng gì? — Tabular/groupby/merge.
41. Mean vs median? — Trung bình vs robust center.
42. IQR? — Q3-Q1/outlier fence.
43. Vì sao không xoá outlier ngay? — Có thể là event thật.
44. Visualization goal? — Trả lời câu hỏi.
45. Bar khi nào? — So sánh categories.
46. Line khi nào? — Trend theo thời gian.
47. Heatmap khi nào? — Matrix pattern.
48. Radar limitation? — Scale/area bias.
49. Boxplot? — Distribution/spread.
50. Why annotate charts? — Unit/sample/source.
51. Wilson interval? — Interval cho tỷ lệ nhị phân.
52. p-value? — Evidence under H0, not truth probability.
53. Effect size? — Magnitude practical.
54. Cohen’s d? — Standardized mean difference.
55. Multiple testing? — False positives increase.
56. Prediction vs causal? — Forecast association vs intervention effect.
57. Feature contract? — Known-at-prediction fields.
58. Logistic regression? — Linear log-odds classifier.
59. Sigmoid? — Map score to 0–1.
60. Coefficient sign? — Direction conditional on others.
61. Accuracy limitation? — Ignores calibration/class balance.
62. Log-loss? — Penalizes confident errors.
63. Brier? — Probability squared error.
64. Baseline? — Majority/naive comparator.
65. Walk-forward? — Train past, predict next.
66. Leakage? — Future info enters features.
67. Random split risk? — Time leakage/optimism.
68. H2H leakage example? — Including future meeting.
69. Small sample strategy? — Caveat, shrinkage/baseline, no overclaim.
70. Prediction 0.57 means? — Conditional estimate, not guarantee.
71. Calibration? — Probability reliability.
72. Why recent form? — Current state, but noisy.
73. Why season aggregate? — Stable baseline, may lag.
74. Why both? — Compare stability and recency.
75. Streamlit role? — Interactive presentation.
76. Why read-only UI? — Separate refresh from consumption.
77. Empty state? — Honest missing selection handling.
78. Stale state? — Warn, retain last-known-good.
79. Unit test? — Isolated contract.
80. Integration test? — Component interaction.
81. Regression test? — Prevent known break.
82. 31 tests evidence? — Full suite passed.
83. Warning vs failure? — Diagnostic vs broken assertion.
84. Why comments? — Explain intent/logic to learner.
85. Why docstrings? — API contract/reference.
86. Config centralization? — Consistent scope/paths.
87. CLI benefit? — Repeatable VS Code runs.
88. Report benefit? — Shareable audit trail.
89. Notebook benefit? — Guided exploration.
90. Source audit benefit? — Provenance/freshness.
91. What if Gol.gg changes? — Parser fixture/source audit.
92. What if network down? — Cache/last-known-good.
93. What if DB empty? — Init/sync/check counts.
94. What if chart wrong? — Trace DataFrame before styling.
95. What if player names collide? — Stable ids + canonical names.
96. Why no casual causal claim? — Observational data/confounding.
97. Biggest project limitation? — Source schema/availability and historical sample.
98. How improve model? — More data, calibration, feature/time validation.
99. How ensure daily update? — Runbook, freshness policy, QA gate.
100. What would you change next? — Scheduler, stronger source contracts, richer uncertainty.

Evidence map: `docs/05_CODEBASE_FILE_GUIDE.md`, `docs/DATA_SCHEMA.md`, `docs/RUNBOOK.md`, `reports/release-readiness-2026-09-08.md`, `src/analysis/`, `src/modeling/`, `tests/`.

