# 03 — DA/DS Foundations

**Prerequisites:** 01–02. **Phone mode:** đầy đủ. **Source:** `docs/03_DA_DS_PLAYBOOK.md`, `src/analysis`, `src/modeling`.

## 🧠 Mental Model

Project dùng CRISP-DM rút gọn:

```text
Business question → data understanding → preparation → analysis/model → evaluation → communication
```

DA hỏi “điều gì đã xảy ra, khác nhau ở đâu, pattern nào đáng chú ý?”. DS hỏi thêm “nếu chỉ biết lịch sử đến thời điểm T, baseline dự đoán ra sao và đo được tốt đến đâu?”.

## 📱 Phone Mode — một câu hỏi tốt

Bad: “Vẽ nhiều chart cho T1.”

Good: “Trong S16, T1 và HLE khác nhau thế nào về win rate, GPM/GDM, objectives và cùng role; pattern nào có sample đủ lớn để hỗ trợ kịch bản matchup?”

Câu hỏi tốt quyết định grain, metric, chart và limitation.

## 📥 Metric contract

| Metric | Câu hỏi | Cảnh báo |
|---|---|---|
| Win rate | Đội thắng bao nhiêu phần trận? | Cần `wins/games`, CI |
| GPM | Economy mỗi phút | Không đồng nghĩa nguyên nhân thắng |
| GDM | Gold differential mỗi phút | Hai team rows cùng game đối dấu |
| DPM | Damage mỗi phút của player | So sánh trong role |
| CSM | CS mỗi phút | Role/strategy ảnh hưởng |
| GD@15/CSD@15 | Early lane state | Không phải kết quả cuối |
| Champion pool | Tướng nào được pick và hiệu quả? | n nhỏ dễ tạo 100% giả |

## ⚙️ DA → DS flow

```text
Clean rows
→ descriptive aggregates
→ uncertainty/statistics
→ feature engineering trước cutoff
→ transparent baseline
→ walk-forward evaluation
```

## 🧪 Simulated Lab — sample size

Team A: 1/1 win = 100%. Team B: 60/100 = 60%.

### ❓ Đội nào evidence ổn định hơn?

### ✅ Đáp án

Team B. Tỷ lệ thấp hơn nhưng denominator lớn hơn; uncertainty thường nhỏ hơn. Không kết luận Team A tốt hơn chỉ vì 100%.

## 🔍 Đọc output như thế nào?

Mỗi claim nên có bốn phần: estimate, denominator, uncertainty, context.

> T1 thắng 63,2% trên 152 primary team-game rows; đây là mô tả S16 snapshot, không phải xác suất trận kế tiếp.

## ❌ What If?

- Correlation cao không chứng minh causation.
- p-value nhỏ không chứng minh effect lớn hay hữu ích nghiệp vụ.
- Accuracy cao không đảm bảo probability calibrated.
- Một chart đẹp không sửa được grain sai.

## 💻 Try It Yourself

Đọc `docs/03_DA_DS_PLAYBOOK.md` rồi mở `reports/statistics-phase-7.md`, `reports/backtest-phase-9.md`; viết một insight có denominator và một limitation.

## 🎤 Defense

1. Vì sao question-first quan trọng hơn chart-first?
2. DA và DS nối nhau ở feature engineering thế nào?
3. Vì sao project không dùng deep learning?
4. Khi nào một metric không nên compare cross-role?
5. Vì sao hypothetical phải tách official?

## ✅ Checkpoint

- [ ] Tôi viết được business question có scope và cutoff.
- [ ] Tôi không diễn giải correlation là nguyên nhân.
- [ ] Tôi hiểu prediction cần evaluation theo thời gian.
