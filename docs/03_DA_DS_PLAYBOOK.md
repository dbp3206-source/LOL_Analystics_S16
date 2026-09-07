# 03 — DA/DS Playbook từ lý thuyết đến thực hành

Tài liệu này là template có thể tái sử dụng khi làm một project phân tích dữ liệu khác. Ví dụ xuyên suốt là LoL chuyên nghiệp, nhưng quy trình áp dụng được cho bán hàng, marketing, thể thao hoặc vận hành.

## 1. Tư duy cốt lõi: bắt đầu từ quyết định, không bắt đầu từ biểu đồ

Một analysis tốt trả lời được bốn câu hỏi:

1. **Đối tượng ra quyết định là ai?** Người xem trận, analyst hay huấn luyện viên giả lập.
2. **Họ cần quyết định gì?** Đội nào có lợi thế, matchup nào đáng chú ý, dữ liệu đã đủ tin cậy chưa.
3. **Bằng chứng nào cần thiết?** Recent form, economy, objective, combat, role matchup, H2H.
4. **Điều gì có thể làm kết luận sai?** Sample nhỏ, khác giải, khác role, patch/meta, dữ liệu thiếu hoặc leakage.

Chỉ sau đó mới chọn bảng, metric, chart và model.

## 2. Framework phân tích dùng trong project

### 2.1 Descriptive → Diagnostic → Predictive

| Mức | Câu hỏi | Ví dụ trong project |
|---|---|---|
| Descriptive | Chuyện gì đã xảy ra? | Win rate, KDA, DPM, form 5 trận |
| Diagnostic | Vì sao/pattern nào đi kèm? | Economy, objective, side, role matchup |
| Predictive | Điều gì có thể xảy ra? | Probability cho fixture kế tiếp |

Project không khẳng định causal vì dữ liệu quan sát từ trận đấu không phải thí nghiệm ngẫu nhiên.

### 2.2 CRISP-DM rút gọn

1. Business understanding — chốt câu hỏi và định nghĩa thành công.
2. Data understanding — kiểm tra nguồn, grain, thời gian, coverage.
3. Data preparation — scrape, parse, clean, join, feature.
4. Modeling — baseline trước, model đơn giản sau.
5. Evaluation — backtest theo thời gian và kiểm tra xác suất.
6. Deployment — CLI/Streamlit/report và daily update.

Mỗi phase trong project ánh xạ vào một bước trên. Đây là cách giải thích đồ án bài bản khi phỏng vấn.

## 3. Xác định grain trước khi lấy dữ liệu

**Grain** là “một dòng đại diện cho cái gì”. Nếu không chốt grain, join rất dễ làm nhân bản dòng.

| Bảng | Grain |
|---|---|
| `games` | một game |
| `game_team_stats` | một team trong một game |
| `game_player_stats` | một player trong một game |
| `drafts` | một pick/ban theo thứ tự trong một game |
| `timeline_events` | một objective milestone trong một game |
| `roster_periods` | một giai đoạn player thuộc team/role |
| `schedules` | một fixture dự kiến |

Ví dụ lỗi thật đã được phòng ngừa: nếu parser đọc cả container cha `Bans | Picks` lẫn hai container con, draft actions bị nhân đôi. Test fixture và quality gates hiện kiểm tra uniqueness cùng đúng 10 pick/10 ban mỗi game.

## 4. Chọn dữ liệu nào lấy và dữ liệu nào không lấy

### Lấy khi

- metric trả lời trực tiếp câu hỏi;
- nguồn hiển thị ổn định và có thể parse;
- grain/time/team/player có thể xác định;
- có cách validate range hoặc đối chiếu;
- có thể lưu source ID/raw evidence.

### Không lấy hoặc để nullable khi

- nguồn không cung cấp ổn định;
- không biết timestamp/cutoff;
- metric nghe hấp dẫn nhưng không phục vụ pain point;
- chi phí crawl lớn hơn giá trị phân tích;
- phải “đoán” giá trị từ giao diện.

Không tự điền số thiếu bằng tưởng tượng. Nếu imputation cần thiết cho model, phải học tham số imputation từ training window, ghi rõ phương pháp và không làm thay đổi raw data.

## 5. Web scraping đúng nghiệp vụ

### 5.1 Công cụ

- `requests`: gửi HTTP request.
- `BeautifulSoup`: duyệt cấu trúc HTML.
- `dataclass`: định nghĩa object trung gian rõ field.
- `hashlib`/manifest: xác định content thay đổi.
- `sqlite3`: lưu dữ liệu có cấu trúc.

### 5.2 Quy trình

```text
URL → kiểm tra cache → request có timeout/retry/rate limit
→ lưu raw HTML → parse field → validate season/identity
→ upsert transaction → ghi manifest
```

### 5.3 Vì sao phải lưu raw HTML?

- Có thể sửa parser rồi rebuild mà không tải lại web.
- Chứng minh số liệu xuất phát từ trang nào.
- So sánh khi cấu trúc HTML thay đổi.
- Tách lỗi mạng khỏi lỗi parsing.

### 5.4 Parser tốt có đặc điểm gì?

- Selector càng gần nhãn có ý nghĩa càng tốt.
- Parse number/date ở một helper chung.
- Không phụ thuộc vào màu sắc hoặc vị trí tuyệt đối nếu có label/ID.
- Trả `None` khi source thật sự thiếu; không trả 0 giả.
- Có fixture HTML nhỏ để test case bình thường và case dễ lỗi.

## 6. Cleaning và data quality

### 6.1 Các nhóm lỗi phổ biến

- whitespace/case khác nhau;
- tên role đồng nghĩa như `ADC`, `BOTTOM`, `BOT`;
- duplicate do crawl lại;
- missing metric;
- value ngoài miền hợp lý;
- join sai grain;
- game ngoài season;
- Academy/Challengers lọt vào primary scope.

### 6.2 Missing không đồng nghĩa bằng 0

- `0 kills`: biết tuyển thủ không có kill.
- `NULL kills`: chưa biết hoặc parse không được.

Gộp hai trạng thái này làm sai mean, distribution và model.

### 6.3 Outlier

IQR rule:

```text
IQR = Q3 - Q1
lower = Q1 - 1.5 × IQR
upper = Q3 + 1.5 × IQR
```

Project dùng IQR để **gắn cờ rà soát**, không tự xóa. Một trận 70 phút tạo CS/DPM bất thường nhưng vẫn có thể là dữ liệu thật. Với player metrics, nên kiểm tra theo role trước vì Support và Bot có distribution khác nhau.

### 6.4 Quality gates quan trọng

- đúng S16;
- mỗi game có một winner;
- mỗi game có hai team rows;
- mỗi game có đúng lineup hợp lệ;
- primary team có current starting five;
- numeric range hợp lý;
- timeline/draft không trùng;
- mỗi game có đúng 10 pick và 10 ban;
- không đưa Academy/Challengers vào primary analysis.

## 7. EDA bằng Pandas và NumPy

### 7.1 Bộ câu hỏi chuẩn

1. Dataset có bao nhiêu dòng/cột?
2. Grain là gì?
3. Khoảng thời gian nào?
4. Dtype đã đúng chưa?
5. Missing/duplicate ở đâu?
6. Central tendency và spread ra sao?
7. Distribution lệch không?
8. Nhóm nào khác nhau đáng kể về mặt mô tả?
9. Feature nào đi cùng nhau?
10. Kết quả nào chỉ là artifact của sample nhỏ?

### 7.2 Cú pháp nền cần hiểu

```python
frame.shape                       # số dòng và cột
frame.dtypes                      # kiểu dữ liệu
frame.isna().sum()                # số missing theo cột
frame.duplicated().sum()          # số dòng trùng
frame[columns].describe().T       # thống kê mô tả
frame.groupby("role")["dpm"].mean()
pd.crosstab(frame["side"], frame["won"], normalize="index")
frame[numeric_columns].corr()
```

NumPy phù hợp cho vectorized calculation, percentile, clipping có kiểm soát và numeric transform. Pandas phù hợp cho bảng, join, filter, groupby, crosstab và export.

## 8. Metrics LoL và cách diễn giải

### 8.1 Team metrics

- Win rate = wins / games.
- Kill/death ratio: sức mạnh combat tổng quát, nhạy với game length.
- GPM là gold per minute; GDM là gold differential per minute. Cùng đơn vị theo phút giúp so game dài/ngắn công bằng hơn.
- First blood/tower rate: early initiative.
- Objective timing: tốc độ lấy dragon/herald/Nashor đầu.
- Side split: mô tả khác biệt blue/red, không mặc định là quan hệ nhân quả.
- Recent form 5/10: cân bằng giữa độ mới và sample.

### 8.2 Player metrics

- KDA = (kills + assists) / max(1, deaths).
- DPM: damage mỗi phút, nên so cùng role/champion context.
- CSM: CS mỗi phút.
- Gold share/damage share: vai trò phân bổ tài nguyên và chuyển hóa tài nguyên.
- GD@15/CSD@15/XPD@15: trạng thái lane ở phút 15.
- Vision score/wards: đặc biệt quan trọng với Support/Jungle.
- Champion pool breadth: số champion đã dùng, cần xem cùng số game.

### 8.3 Champion win rate

Không xếp champion chỉ theo win rate. Bảng tốt cần đồng thời:

- games;
- wins;
- win rate;
- pick rate;
- KDA hoặc performance;
- small-sample warning.

## 9. Thống kê nền tảng

### 9.1 Mean, median, standard deviation

- Mean nhạy với extreme values.
- Median bền hơn khi distribution lệch.
- Standard deviation cho biết độ phân tán quanh mean.
- Quartile/IQR mô tả 50% dữ liệu trung tâm.

### 9.2 Skewness và kurtosis

- Skewness dương: đuôi phải dài.
- Skewness âm: đuôi trái dài.
- Kurtosis cao: nhiều giá trị cực đoan hơn so với normal distribution.

Hai metric này giúp chọn cách trình bày và kiểm tra assumption, không phải tiêu chí tự động để loại dữ liệu.

### 9.3 Confidence interval cho win rate

Một tỷ lệ 70% sau 10 game không đáng tin ngang 70% sau 100 game. Project dùng Wilson interval vì ổn hơn normal approximation khi n nhỏ hoặc tỷ lệ gần 0/1.

### 9.4 Correlation

- Gần +1: hai biến có xu hướng tăng cùng nhau.
- Gần -1: một biến tăng khi biến kia giảm.
- Gần 0: không có quan hệ tuyến tính rõ.

Correlation không chứng minh nguyên nhân. Win làm GPM cao hay GPM cao giúp win có thể cùng tồn tại; muốn kết luận causal cần thiết kế nghiên cứu khác.

### 9.5 Kiểm định suy luận vừa sức

- **Chi-square side × outcome:** dùng cho hai biến phân loại; đọc bảng observed/expected và chỉ diễn giải khi expected count đủ lớn.
- **Two-proportion z-test:** so tỷ lệ thắng tổng thể của hai đội. H0 là hai tỷ lệ bằng nhau; p-value không phải xác suất đội A thắng trận tới.
- **Welch t-test:** so mean GDM của hai đội mà không ép phương sai bằng nhau. Cần đọc distribution, outlier và sample trước.
- **Cohen's d:** cho biết độ lớn chênh lệch mean theo đơn vị standard deviation; nên báo cùng p-value.

Đây là phân tích observational. Lịch đối thủ, patch/meta và thời gian chưa được kiểm soát đầy đủ, nên không viết “A gây ra B”. ANOVA, causal inference và Bayesian modeling nằm ngoài core của bài tập lớn này.

## 10. Chọn visualization theo câu hỏi

| Câu hỏi | Visual phù hợp | Không nên dùng |
|---|---|---|
| So sánh 10 đội theo một metric | Sorted bar/lollipop | Pie 10 lát |
| So sánh hai đội nhiều metric | Dumbbell/heatmap/radar có chuẩn hóa | 10 bar chart rời |
| Phong độ qua thời gian | Line + rolling mean | Bar không theo trật tự |
| Distribution DPM/CSM | Box/violin + điểm dữ liệu | Chỉ mean bar |
| GPM liên hệ win rate | Scatter + annotation | Radar |
| Correlation nhiều feature | Heatmap | Bảng số thô duy nhất |
| Side và kết quả | 100% stacked bar/mosaic | Pie tách rời |
| Champion pool | Dot/bubble hoặc ranked table | Word cloud |

Mỗi figure cần: title là kết luận/câu hỏi, label và đơn vị, sample/cutoff, chú thích metric, màu nhất quán và source note.

## 11. Feature engineering và modeling vừa sức

### 11.1 Feature an toàn

- recent win rate trước fixture;
- mean gold/kills/deaths trước fixture;
- H2H trước fixture;
- side nếu fixture cung cấp;
- rolling window cố định.

Không dùng kết quả hoặc stats của chính game cần dự đoán.

### 11.2 Baseline trước model

Baseline cho biết model phức tạp có thật sự thêm giá trị không. Project dùng empirical/Bayesian-smoothed strength dễ giải thích, sau đó so với Logistic Regression.

### 11.3 Logistic Regression

Mô hình ước lượng:

```text
p(win) = sigmoid(intercept + w1×feature1 + ... + wk×featurek)
```

Ưu điểm: dễ học, nhanh, output là probability, coefficient có thể diễn giải tương đối. Giới hạn: quan hệ tuyến tính trong log-odds và nhạy với feature scale/correlation.

### 11.4 Walk-forward validation

```text
Game 1..N quá khứ → fit → dự đoán game N+1
thêm kết quả game N+1 vào history → lặp lại
```

Không random split vì esports là time-dependent. Random split có thể cho model học dữ liệu xảy ra sau trận test.

### 11.5 Metrics model

- Accuracy: dự đoán đội thắng đúng bao nhiêu phần trăm.
- Brier score: trung bình bình phương sai số probability; thấp hơn tốt hơn.
- Log loss: phạt nặng dự đoán rất tự tin nhưng sai; thấp hơn tốt hơn.

Probability hữu ích phải vừa phân loại đúng vừa được calibration hợp lý. Không chỉ nhìn accuracy.

## 12. Cách viết insight có trách nhiệm

Template:

```text
Finding: Trong [sample/time window], A cao hơn B ở [metric] bao nhiêu.
Evidence: n, mean/median/rate, uncertainty và chart/table.
Interpretation: Pattern này gợi ý điều gì trong ngữ cảnh trận đấu.
Limitation: role, opponent strength, patch, missing hoặc sample nhỏ.
Action/Scenario: Điều kiện nào khiến lợi thế có thể phát huy.
```

Tránh các câu như “chắc chắn thắng”, “player tốt hơn tuyệt đối” hoặc “X gây ra Y” khi dữ liệu không chứng minh được.

## 13. Template triển khai project tương tự

```text
01_problem_definition.md
02_source_contract.md
03_data_dictionary.md
raw/ → staging/ → processed/
collection/ → storage/ → quality/ → analysis/ → modeling/
notebooks/01_understand.ipynb
notebooks/02_clean_eda.ipynb
notebooks/03_visualize.ipynb
notebooks/04_model.ipynb
reports/ + figures/ + app/
tests/fixtures + unit/integration tests
```

Checklist tái sử dụng:

1. Viết câu hỏi và decision trước.
2. Chốt scope, grain, time cutoff và source authority.
3. Lưu raw và source ID.
4. Tách collection, cleaning và analysis.
5. Định nghĩa data contract và quality gates.
6. EDA trước modeling.
7. Chọn visual theo câu hỏi.
8. Baseline trước model nâng cao.
9. Split theo thời gian nếu dự đoán tương lai.
10. Báo sample, uncertainty, cutoff và limitation.
11. Test case dễ sai.
12. Làm một demo từ input đến output có thể lặp lại.

## 14. Câu hỏi phỏng vấn có thể trả lời từ project

- Vì sao chọn SQLite thay vì chỉ CSV?
- Upsert và idempotency giải quyết vấn đề gì?
- Làm sao tránh duplicate khi scrape định kỳ?
- Vì sao missing không được thay bằng 0?
- Vì sao player phải so cùng role?
- Vì sao không xóa mọi outlier theo IQR?
- Wilson interval có lợi gì khi sample nhỏ?
- Data leakage trong project này có thể xảy ra ở đâu?
- Vì sao walk-forward tốt hơn random split?
- Accuracy, Brier score và log loss khác nhau thế nào?
- Một chart tốt khác một chart “show skill” ở điểm nào?
- Nếu Gol.gg đổi HTML, bạn phát hiện và sửa như thế nào?

Nếu có thể trả lời bằng ví dụ và chỉ đúng file/code/report tương ứng, bạn đã hiểu project thay vì chỉ chạy được project.
