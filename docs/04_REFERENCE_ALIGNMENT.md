# 04 — Đối chiếu project với các nguồn tham khảo

Tài liệu này trả lời hai câu hỏi: project đã lấy phần nào từ nguồn tham khảo, và phần nào chủ động không lấy để giữ quy mô vừa sức sinh viên năm 3.

## 1. Nguồn đã đọc

1. [MIS140 EDA Colab](https://colab.research.google.com/drive/1YQIgDaDWOZdBZ9ELmYRBiDjDWF0D3JWD#scrollTo=ZSGU7OXHMlm6)
2. [Python cho DA/DS — Intermediate](https://learningvn.com/roadmap/lo-trinh-hoc-python-cho-data-analyst-scientist-trinh-do-intermediate-v1773733576--1773733576)
3. [Data Science cho người mới](https://learningvn.com/roadmap/lo-trinh-hoc-data-science-cho-nguoi-moi-bat-dau-1768040428)
4. [Python nâng cao cho DA/DS](https://learningvn.com/roadmap/lo-trinh-hoc-python-nang-cao-cho-data-analyst-scientist-v1773808001--1773808002)

Đối chiếu được thực hiện theo từng mục lớn/nhỏ hiển thị công khai của các nguồn, không chỉ dựa vào tên khóa học.

## 2. Ánh xạ với notebook Colab

| Mục trong Colab | Cách áp dụng cho LoL S16 | Bằng chứng/project output |
|---|---|---|
| Learning objectives | Nêu câu hỏi đội/player/matchup trước khi code | `docs/01_PROJECT_OVERVIEW.md` |
| Business questions | Chuyển thành câu hỏi phong độ, economy, objective, role matchup | `docs/PRODUCT_SPEC.md` |
| Data dictionary | Định nghĩa grain, field và relation | `docs/DATA_SCHEMA.md` |
| Import libraries | NumPy, Pandas, Matplotlib, Seaborn; SciPy/Statsmodels khi cần | `requirements.txt` |
| Load dataset | Đọc SQLite thay vì một CSV rời | `load_analysis_frames()` |
| Inspect data | Shape, dtype, unique, missing, duplicate | `inspect_dataframe()` |
| Clean data | Datetime, text/role, missing policy, quality gates | `src/quality/`, Pandas EDA |
| Missing heatmap | Figure chẩn đoán coverage, không dùng để che giấu missing | scientific visualization phase |
| Descriptive statistics | count/mean/std/quartile/skewness/kurtosis | `numeric_summary()` |
| Numerical univariate | Histogram/KDE, boxplot, violin theo metric/role | scientific visualization phase |
| Outlier IQR | Gắn cờ candidate; không tự động xóa trận đặc biệt | `iqr_outlier_summary()` |
| Categorical summary | `value_counts`, relative frequency, champion/side/role | Pandas EDA và champion pool |
| Bar preferred / pie careful | Ưu tiên bar/lollipop; không dùng pie nhiều lát | visualization contract |
| Numerical vs numerical | Correlation heatmap, scatter và trend | scientific visualization phase |
| Numerical vs categorical | Box/violin cùng role/team | scientific visualization phase |
| Categorical vs categorical | Crosstab count/rate, heatmap; chi-square chỉ khi assumption hợp lệ | side outcome và statistics phase |
| Multivariate | Scatter có hue/facet, normalized comparison | scientific visualization phase |

### Điều chỉnh có chủ đích so với Colab

Notebook mẫu có minh họa `dropna()` toàn bộ và ba lựa chọn xử lý outlier. Project không copy máy móc hai thao tác này:

- Missing esports có ý nghĩa nguồn; chỉ drop khi field bắt buộc cho đúng câu hỏi.
- Outlier có thể là một game thật sự xuất sắc/dài; mặc định chỉ review.
- Không dùng pairplot toàn bộ hàng chục feature vì nặng và khó đọc; chỉ chọn feature phục vụ câu hỏi.
- Chi-square chỉ được chạy khi expected count hợp lệ; nếu không, báo “không đủ điều kiện”.

Đây là bám sát **quy trình tư duy**, không sao chép quyết định cleaning từ một domain nhà đất sang esports.

## 3. Ánh xạ với roadmap Intermediate 8 tuần

| Tuần | Nội dung nguồn | Phần chọn cho project | Trạng thái |
|---:|---|---|---|
| 1 | Pandas cơ bản, missing, chuẩn hóa | Load/inspect/missing/clean | Đã có |
| 2 | GroupBy, growth theo thời gian, join dataset | role/tournament summary, rolling form, SQLite joins | Đã có |
| 3 | Matplotlib/Seaborn, trend và dashboard nhiều chart | 12 global + 2 matchup figures, Streamlit | Code đã có; chờ cài package để render/QA |
| 4 | Mean/median/std/skewness, A/B test | descriptive stats; rate comparison phù hợp dữ liệu quan sát | Một phần; không gọi observational comparison là A/B test |
| 5 | Outlier, scaling, datetime/text feature | IQR review, time cutoff, feature scaling trong model | Đã có phần phù hợp |
| 6 | Linear/Logistic Regression | Logistic Regression cho win/loss | Đã có bản giáo dục |
| 7 | Random Forest, GridSearchCV | Chỉ optional benchmark sau baseline | Chưa chọn làm bắt buộc |
| 8 | Capstone end-to-end, Jupyter report | full pipeline + notebook/report | Đang hoàn thiện notebook render |

## 4. Ánh xạ với roadmap Data Science 12 tuần

### Phần nền tảng được dùng

- Python: biến, kiểu dữ liệu, điều kiện, vòng lặp, hàm, module.
- NumPy/Pandas: array, DataFrame, CSV/SQL, filter, sort, groupby, aggregation.
- Visualization: line, bar, scatter, heatmap, subplot, label/title.
- Statistics: descriptive distribution, probability intuition, correlation, kiểm định cơ bản có assumption.
- Cleaning: missing, encoding khi model cần, feature engineering, outlier, preprocessing.
- EDA: distribution, group, correlation, anomaly, insight.
- ML: Logistic Regression, train/evaluate, classification metrics.
- SQL: SELECT, WHERE, JOIN, GROUP BY; subquery dùng ở current roster/cutoff.
- Integrated project: collect → clean → EDA → model → report → presentation.
- Best practices: tests, documentation, code optimization ở mức vừa phải.

### Phần không đưa vào core

- Linear Regression không phù hợp target win/loss nhị phân.
- K-Means/PCA/hierarchical clustering không trực tiếp giải quyết pain point chính.
- Flask deployment không cần vì demo dùng Streamlit Python.
- Git không thể được chứng minh trong workspace hiện tại vì thư mục chưa phải repository; đây là kỹ năng học bổ sung, không được giả vờ là deliverable đã có.

## 5. Ánh xạ với roadmap Python nâng cao

| Nội dung nâng cao | Quyết định | Lý do |
|---|---|---|
| MultiIndex | Không bắt buộc | GroupBy bảng phẳng dễ hiểu hơn cho sinh viên năm 3 |
| Multi-level GroupBy | Dùng vừa phải | Có role/tournament/team grouping |
| NumPy broadcasting/vectorization | Dùng | `kill_death_ratio` vectorized và numeric calculations |
| Dask/chunking dataset lớn | Không dùng | 667 games không cần distributed computing |
| Memory dtype optimization | Chỉ giải thích | Dataset hiện nhỏ, tối ưu sớm làm code khó học |
| Matplotlib subplot/annotation | Dùng | Cần cho visualization chuyên nghiệp |
| Plotly Dash | Không dùng | Streamlit đã đủ và giữ tech stack Python gọn |
| A/B testing, ANOVA | Chỉ optional/assumption-aware | Dữ liệu trận đấu không phải randomized experiment |
| Time-series visualization | Dùng | Rolling form theo thời gian |
| Jupyter report | Dùng | Phù hợp cách học Colab/VS Code |
| ML Pipeline/GridSearchCV | Optional | Chỉ sau khi baseline và temporal split ổn |
| DBSCAN/PCA/PolynomialFeatures | Không dùng core | Không phục vụ query chính, vượt scale |
| Flask API | Không dùng | Không cần hai lớp demo |
| Git/DVC | Git khuyến nghị, DVC không cần | Dataset/project chưa đủ lớn |
| Docker/Prefect/Airflow | Không dùng | Vượt yêu cầu bài tập lớn Python và tăng gánh vận hành |
| Unit test | Dùng | Parser/data/model cần regression evidence |
| Documentation/presentation | Dùng | Là deliverable bắt buộc |

## 6. Scope học thuật cuối cùng

### Core — bắt buộc phải chạy và giải thích được

1. Python core và module organization.
2. Web scraping có trách nhiệm và raw provenance.
3. SQLite + SQL joins/aggregation.
4. Cleaning và data-quality gates.
5. Pandas/NumPy EDA.
6. Univariate, bivariate, multivariate analysis.
7. Matplotlib/Seaborn visualization theo pain point.
8. Thống kê mô tả, interval và kiểm định đơn giản có assumption.
9. Logistic Regression/baseline và walk-forward evaluation.
10. Streamlit demo, notebook, report, tests.

### Optional của nguồn — không đưa vào scope hiện tại

- Scikit-learn Logistic Regression có thể dùng sau này để đối chiếu bản gradient descent giáo dục.
- Decision Tree/Random Forest và hyperparameter search không cần cho bài nộp hiện tại.
- Statsmodels logistic inference không cần; Statsmodels trong core chỉ dùng z-test hai tỷ lệ.

Việc ghi nhận các mục trên thể hiện đã đối chiếu roadmap, không phải cam kết phải nhồi mọi kỹ thuật vào sản phẩm. Baseline + Logistic Regression walk-forward hiện tại đủ để trả lời câu hỏi dự đoán ở mức năm 3.

### Out of scope

- Deep learning.
- Dask/Spark.
- PCA/DBSCAN/clustering không có câu hỏi rõ.
- Docker/Kubernetes.
- Airflow/Prefect.
- Cloud deployment/MLOps phức tạp.

Ranh giới này giữ project có chiều sâu DA/DS nhưng vẫn đủ để sinh viên năm 3 hiểu, tự chạy và bảo vệ trước giảng viên.
