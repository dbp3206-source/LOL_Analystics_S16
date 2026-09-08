# 29 — Limitations và design trade-offs

## Known limitations

- Gol.gg/source HTML có thể đổi, rate-limit hoặc thiếu field.
- Snapshot/fixtures không đại diện cho một lần refresh internet trong tương lai.
- Observational match data không chứng minh causal skill.
- S16 sample vẫn nhỏ cho một số player/champion/matchup.
- Prediction không guarantee kết quả và cần đọc freshness.
- Browser/mobile visual smoke test chưa được thực thi trong lượt audit này.
- Runtime SQLite/raw data bị ignore, không commit artifact lớn.
- Một số test helper trong `tests/` không có docstring; handbook giải thích behavior thay thế.

## Trade-offs

| Decision | Benefit | Cost |
|---|---|---|
| SQLite | portable, demo dễ | concurrency hạn chế |
| cached HTTP | reproducible/rate-limit | cache stale |
| heuristic + logistic | dễ giải thích | accuracy chưa tối ưu |
| S16-only | up-to-date | sample nhỏ |
| SVG fallback | chạy ít dependency | chart ít phong phú |
| Streamlit | nhanh demo | UI production hạn chế |

## Optional extensions

Scheduler/CI refresh, richer source contracts, calibration, hierarchical player effects, champion patch features, visual regression, deployed DB. Các mục này không phải baseline bắt buộc của bài tập.

## Checkpoint

Bạn có thể nói limitation trước khi người chấm hỏi, kèm mitigation và evidence.

