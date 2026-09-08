# 27 — Beginner exercises và quiz

## Phone-first exercises

1. Predict `AVG(win)` for a 2-row team table before reveal: rows `1,0` → `0.5`.
2. Spot grain error: joining 10 player rows to 1 team row should not create 10 team games.
3. Mark leakage: a feature using game result is forbidden.
4. Choose chart: trend → line; category comparison → bar; matrix → heatmap.
5. Explain `NaN` vs `0` in one sentence.

## Hands-on exercises

6. Add a parser fixture with one missing score and write expected output.
7. Add a quality check for duplicate `game_id`.
8. Create a Pandas summary with wins/games/rate.
9. Add sample-size annotation to a chart.
10. Compare majority baseline with logistic backtest.
11. Trace one report number to SQL and source field.
12. Write a regression test for role normalization.
13. Simulate stale freshness and design UI message.
14. Explain one champion 100% win rate with n=1.
15. Present a 3-minute T1/HLE analysis with two caveats.

## Predict → reveal pattern

For every exercise: pause, write expected output, run/test, compare, explain mismatch, record a regression test if the mismatch reveals a bug.

## Checkpoint

A beginner finishes when they can complete 1–5 without IDE, then 6–10 in VS Code using existing tests as templates.

