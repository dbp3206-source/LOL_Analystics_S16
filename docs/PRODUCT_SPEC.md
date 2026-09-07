# Final Product Specification

## Product name

LoL Pro Analytics S16 — LCK Teams

## User goal

Chọn một hoặc hai thực thể thuộc nhóm đội tuyển/tuyển thủ LCK và nhận báo cáo cập nhật phù hợp với loại truy vấn. Dự báo chỉ được sinh khi có fixture tương lai hợp lệ.

## Analysis modes

### Mode A — One team

- Team profile và vị trí percentile trong LCK.
- Phong độ 5/10 game và 3/5 series.
- Domestic/international split.
- Starting five, role contribution và champion pools.
- Đối thủ/trận tiếp theo nếu tìm thấy lịch.
- Prediction cho fixture kế tiếp khi đủ dữ liệu.

### Mode B — Two teams

- Team comparison.
- Recent results và S16 head-to-head.
- Năm role matchups.
- Draft/champion context.
- Prediction và BO3/BO5 scenarios nếu có fixture hoặc người dùng chọn hypothetical matchup.

### Mode C — One player

- General, early-game, economy, combat và vision profile.
- Champion pool, số game, win rate và KDA từng champion.
- Recent form và tournament/patch split.
- So sánh với phân phối của các starting players cùng role trong LCK.
- Đối thủ cùng lane ở fixture kế tiếp nếu xác định được.

### Mode D — Two players

- Có thể cùng đội hoặc khác đội.
- Nếu cùng role: peer comparison bằng raw metrics, distribution và role percentile.
- Nếu khác role: chỉ so sánh role-adjusted percentile và contribution profile.
- Nếu khác đội và từng đối đầu: thêm game-level history khi cả hai cùng xuất hiện.
- Nếu là đối thủ cùng lane ở fixture sắp tới: thêm lane-matchup scenarios.

## Scope rules

1. Team universe là 10 đội LCK cấp một.
2. Không thu thập đội Challengers/Academy vào dataset chính.
3. Team-level form dùng mọi trận chính thức S16 mà đội tham dự, gồm nội địa và quốc tế.
4. Player comparison dùng starting five hiện tại theo lineup gần nhất; substitute không xuất hiện trong bảng so sánh chính.
5. Historical games có substitute vẫn được tính ở team level nhưng phải gắn roster context.
6. Head-to-head gồm mọi lần hai đội gặp nhau trong S16, kể cả giải quốc tế.
7. Gol.gg là nguồn statistics duy nhất; nguồn phụ chỉ cung cấp future schedule.
8. Phân tích chính không dùng S15 hoặc mùa cũ hơn.

## Standard query

Với T1 và Hanwha Life Esports, hệ thống phải:

- xác định đúng đội cấp một;
- xác nhận S16 và data cutoff;
- tìm fixture sắp tới nếu lịch có;
- so sánh team metrics và percentile trong nhóm LCK;
- hiển thị 5/10 game và 3/5 series gần nhất;
- liệt kê toàn bộ H2H S16;
- so sánh TOP, JUNGLE, MID, BOT và SUPPORT;
- phân tích champion pool với số game;
- trình bày lợi thế early game, economy, combat, objective, vision và side;
- dự báo game/series probability;
- nêu các kịch bản có điều kiện và limitation.

## Input UI

- Analysis mode: one team, two teams, one player, two players.
- Entity A bắt buộc; Entity B chỉ xuất hiện ở chế độ hai thực thể.
- Scope: all official S16, domestic, international hoặc tournament cụ thể.
- Recent window: 5, 10 hoặc 20 games.
- Unit: game/series.
- BO1/BO3/BO5 chỉ dành cho team matchup/prediction.
- Toggle role matchup và prediction.
- Update-data button.

Không triển khai chatbot ngôn ngữ tự nhiên tổng quát trong bản chính.

## Analysis output sections

1. Data status.
2. Entity profile(s).
3. Recent form.
4. Comparison/head-to-head khi có hai thực thể.
5. Team role matchups hoặc player peer benchmark khi phù hợp.
6. Champion pool/draft context.
7. Statistical evidence.
8. Visual story.
9. Next fixture, prediction và scenarios khi đủ điều kiện.
10. Data/model limitations.

## Prediction contract

- Prediction timestamp nhỏ hơn fixture timestamp.
- Feature chỉ được tính từ record có timestamp nhỏ hơn prediction timestamp.
- Không dùng aggregate S16 đã chứa target game.
- Probability luôn kèm model version, training cutoff và validation metrics.
- Nếu data không đủ hoặc không có fixture, không tạo xác suất giả.
- Single-player analysis không tự tạo xác suất “tuyển thủ thắng”; prediction target vẫn là team/game/series outcome.

## Daily update contract

- App kiểm tra `last_successful_update`.
- Nếu dữ liệu chưa được cập nhật trong ngày, chạy incremental update.
- Raw response được cache và hash.
- SQLite upsert phải idempotent.
- Mọi output hiển thị collected_at và data cutoff.
- Có thể chạy thủ công bằng CLI khi nguồn web thay đổi.
