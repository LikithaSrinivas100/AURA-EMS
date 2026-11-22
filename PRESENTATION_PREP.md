# AURA-EMS — Presentation prep pack (from the actual repo)
**Verify every number against the cited file.** If a claim has no citation, do not say it.

Team: **Likitha** = ML (`ML_Implementation/`). **Anushka** = FastAPI (`backend/`). **Risha** = Streamlit (`frontend/`).
Any of you can answer another’s module using the one-liners below.

---

# A. Memorize tonight (most important)

## 10 sentences (no hesitation)

1. AURA-EMS forecasts **15-minute campus demand** by fusing meter load, academic calendar, and weather, then exposes peaks and a what-if carbon/cost shave through a dashboard that **only talks to the API**.
2. We **do not shuffle time**. Train = first **80%** of usable rows (**27,956**), test = last **20%** (**6,989**), **2025-09-02 → 2026-09-01** after lag dropna (`outputs/metrics.json`).
3. Lags are **row shifts on a validated 15-min index**: 4=1h, 8=2h, 96=24h; rolling 4h uses **shift(1) then window 16** so the current target never enters (`ml/feature_engineering.py`).
4. Baseline is **24-hour persistence**: predict `Load_Lag_24hr` (`ml/baseline.py`). XGBoost **RMSE 13.72 kW** vs baseline **79.44 kW** (`metrics.json`).
5. Winner rule is **lowest test RMSE**, not MAPE; XGBoost beat LightGBM **13.72 vs 16.68** (`evaluate.py` `winner = min(..., rmse)`).
6. MAPE **9.59%** is mean |error/actual|×100 on **nonzero** actuals; **0 zeros excluded** (`evaluate.py` `calculate_metrics`).
7. Dashboard RMSE/MAPE/MAE are the **published test-set**, not the date filter (`/metrics/summary` ← `ModelRegistry`).
8. **Demand forecast ahead** is recursive 15-min steps from an **as_of** timestamp, max **168 h**, using last **96** load points as lags (`forecaster.py` `forecast_ahead`).
9. **HIGH** = demand ≥ **max(350 kW, P90)** of the relevant series; the peaks **table** is Start→End history with a **HIGH/MEDIUM/LOW mix**; the green “no HIGH peaks” line is **only the ahead horizon** (`forecasts.py`, `app.py`).
10. CO₂/₹ are a **what-if peak-shave**, not BESCOM bills: cap HIGH intervals at P75, × **0.25 h** × **0.71 kg/kWh** and **₹8.50/kWh** (`schemas.py`, `forecasts.py` `get_carbon_impact`).

## Elevator pitch (~45s)

Alliance University is billed like a small city: academic blocks peak in the day, hostels at night, and exams/vacations/weather move the load. AURA-EMS is a **context-aware 15-minute demand forecast**. We fuse smart-meter kW, calendar flags, and temperature, train leak-safe tree models on a **chronological 80/20 split**, and pick **XGBoost** (test RMSE **13.72 kW**, MAPE **9.59%**) over a 24-hour persistence baseline (**79.44 kW**). FastAPI serves the artifacts; Streamlit never touches the pickle or SQLite. Facilities see history vs prediction, a **7-day-max recursive ahead forecast** with Open-Meteo weather, peak-risk windows, and an **illustrative** CO₂ and tariff-shave KPI. It is a **decision-support tool, not official BESCOM billing**.

## Cheat sheet

| Item | Value | Source |
|---|---|---|
| Frequency | 15 min | `ml/utils.py` `EXPECTED_INTERVAL` |
| Master span | 2025-09-01 → 2026-09-01 (raw); usable 2025-09-02 → 2026-09-01 | earlier CSV check; `metrics.json` |
| Usable rows | 34,945 | `ml_evaluation.md` |
| Train / test | 27,956 / 6,989 | `metrics.json` |
| Test window | 2026-06-20 05:00 → 2026-09-01 | `ml_evaluation.md` |
| Features | 12 listed in `FEATURE_COLUMNS` | `feature_engineering.py` |
| XGB/LGB params | n_est=300, depth=6, lr=0.05, subsample=0.8, colsample=0.8, seed=42 | `train.py` |
| Baseline RMSE/MAE/MAPE | 79.437 / 36.543 / 34.00% | `metrics.json` |
| XGBoost | 13.718 / 9.158 / 9.59% | same |
| LightGBM | 16.678 / 9.864 / 9.88% | same |
| Academic zone | RMSE 9.65, MAPE 22.00% | `zone_metrics.json` |
| Hostel zone | RMSE 7.43, MAPE 13.27% | same |
| RMSE | √(mean (y−ŷ)²) | `evaluate.py` + sklearn |
| MAE | mean \|y−ŷ\| | same |
| MAPE | mean \|(y−ŷ)/y\|×100, y≠0 | same |
| Ahead max | 168 hours, 4 steps/hour | `forecasts.py` Query le=168 |
| Seed lags | 96 intervals = 24 h | `forecaster.py` |
| EF | 0.71 kg CO₂/kWh | `schemas.py` `INDIA_GRID_EF` |
| Tariff | ₹8.50/kWh | `EDU_TARIFF` |
| Trees | CO₂ / 21 | `forecasts.py` `_TREE_KG_CO2_PER_YEAR` |
| HIGH floor | 350 kW | `HIGH_RISK_KW` |
| Open-Meteo campus | 12.7286, 77.7027 (Anekal) | `forecaster.py` |
| Open-Meteo live KPI | 12.9716, 77.5946 (city) | `weather.py` |
| Render | `render.yaml` two free web services | |

**RMSE** = √(1/n Σ (yᵢ−ŷᵢ)²) — big misses hurt more.  
**MAE** = 1/n Σ \|yᵢ−ŷᵢ\| — typical kW error.  
**MAPE** = 100/n Σ \|yᵢ−ŷᵢ\|/yᵢ — %; blows up near 0.

---

# B. Architecture (end-to-end)

```
Master CSV + academic_calendar.csv
    → feature_engineering (leak-safe lags) → X_train/X_test
    → train.py (baseline, XGB, LGB) → pkl
    → evaluate.py → aura_ems_best.pkl + metrics.json + dashboard_inference_feed.csv
    → train_zones.py → aura_ems_academic.pkl, aura_ems_hostel.pkl
    → seed_db.py → SQLite (forecasts, model_registry, energy_logs)
    → FastAPI JSON
    → Streamlit (requests only)
```

**Why frontend → API only:** README integration rule; `api_client.py` is the only HTTP client; no pickle/CSV in Streamlit. Swappable ML without rewriting UI.

**Why SQLite:** capstone, one file `backend/aura_ems.db` (`db.py`), no Postgres ops. `check_same_thread=False` for FastAPI. **Not** multi-writer production.

**Why FastAPI:** typed JSON, CORS, Pydantic, `/docs`. **Why Streamlit:** fastest Python dashboard; Plotly charts. Tradeoff: Streamlit reruns the script on widget change.

**Likitha does not serve HTTP. Anushka does not train. Risha does not query SQL.**

---

# C. Data and features

**Loader** `ml/utils.py` `load_master_dataset`: parse index, reject duplicate/unparseable ts, sort, numeric target, **fail on negative kW**, **fail if median interval ≠ 15 min**.

**Target:** `Total_Campus_Demand_kW`. Also in master (used by zones/seed): `Academic_Demand_kW`, `Hostel_Demand_kW`, `Temperature_C`, `Hour`, `DayOfWeek`, `Month`, `Is_Weekend`, `Is_Vacation`, `Is_Exam_Cycle`. Calendar **columns are already in the CSV**; `academic_calendar.csv` is used at **inference** (`_calendar_flags`).

**Cleaning:** no imputation in code — invalid rows **raise**. Lag/rolling NaNs **dropped** (`dropna` in `engineer_features`) → first ~24h gone → start **2025-09-02**.

**Engineered (only lags/rolling in code):**

| Feature | How | Leak-safe? |
|---|---|---|
| Load_Lag_1hr | `demand.shift(4)` | yes, t−1h |
| Load_Lag_2hr | `shift(8)` | t−2h |
| Load_Lag_24hr | `shift(96)` | t−24h |
| Load_Rolling_Mean_4hr | `shift(1).rolling(16).mean()` | yes, excludes y_t |
| Load_Rolling_Std_4hr | `shift(1).rolling(16).std()` | same |
| Hour, DayOfWeek, Month, Temp, Weekend, Vacation, Exam | from CSV | assumed known at t |

**Split:** `create_chronological_split` `iloc[:80%]` / `iloc[80%:]`. **No k-fold.** Random folds leak future into train.

**Calendar file:** exam weeks Nov/May, vacation Dec + **June**. Placeholder-ish (rounded weeks) — say “simplified academic calendar for flags, not the registrar’s official PDF.”

---

# D. Models

**Baseline** `Persistence24HourBaseline.predict` = return `Load_Lag_24hr`. Fair seasonal-naive benchmark.

**XGB + LGB** same params (`train.py`): 300 trees, depth 6, lr 0.05, subsample 0.8, colsample 0.8, `reg:squarederror`, seed 42. LGB extra `subsample_freq=1`. **No GridSearch in repo** — not found.

**Why XGB:** empirically lowest **test RMSE** (`evaluate.py` line 78). Trees handle mixed numeric/binary features, irregular campus peaks, less data-hungry than LSTM.

**Zones** `train_zones.py`: swap target to academic/hostel, **same features and XGB params**, same 80/20. Academic MAPE **22%** because nights near-zero inflate MAPE even if RMSE 9.65 kW is small. Hostel MAPE 13.27%. `ml_evaluation.md` still says “campus-total only” — **stale vs code**.

**Artifacts:** `models/aura_ems_best.pkl` (copy of winner), `aura_ems_xgboost_exp.pkl`, `lightgbm_exp.pkl`, `baseline_exp.pkl`, zone pkls.

---

# E. Forecast-ahead (`forecaster.py` `forecast_ahead`)

1. Slice history `loc[:as_of]`; need ≥96 rows.
2. Future index = last_ts+15min, `hours*4` steps.
3. Weather: Open-Meteo hourly temp, 15-min interpolate; timeout 3s; else **previous-day temp fallback**.
4. Calendar: vacation/exam if date in `academic_calendar.csv`.
5. For each zone, start from last 96 kW; each step build 12 features, `model.predict`, append (clip ≥0).
6. Risk vs **history** P90/P75 with HIGH floor 350 kW.

**Drawback:** recursive error accumulates (ŷ feeds next lag). Weather API can fail. `@lru_cache(64)` caches (hours, as_of).

**Live KPI** `weather.py` `today_peak`: 24h from **now**, lags from last history **same clock hour**, city lat/lon. **Different coords than campus forecast.**

---

# F. Peaks

**Ahead items:** HIGH if `total_kw >= max(350, hist P90)` else MEDIUM if ≥ P75 else LOW (`forecaster.py`).

**Table** `get_peaks`: filter Start→End, P90/P75 by rank-offset, HIGH cut = `max(350, p90)`, then **mix** ~half HIGH, ~1/3 MEDIUM, rest LOW (`forecasts.py`). Sorted by kW desc.

**Green banner** `app.py`: no HIGH in **ahead_df** only. Table can still show HIGH history. Say this out loud in demo.

---

# G. Carbon / ₹

`get_carbon_impact`: prefer Start→End `best_pred_kw`; else ahead totals.

```
p90, p75 = percentiles of that series
shaved_i = min(v, p75) if v≥p90 else v
energy_avoided_kWh = (Σv − Σshaved) × 0.25
CO₂_kg = energy_avoided × 0.71
₹ = energy_avoided × 8.50
trees = CO₂ / 21
```

**Assumptions (say honestly):** 0.71 ≈ India grid EF (hard-coded, not CEA live). 8.50 = education-tariff **proxy**, not your BESCOM TOD slab. 21 kg/tree/year is a popular heuristic. This is **if we shaved HIGH down to P75**, not measured meters.

Live carbon card uses the **same shave on the 24h live preds** (`weather.py`).

---

# H. Backend

**DB** `models.py`: `forecasts`, `model_registry`, `energy_logs`, `model_performance_metrics`, `meter_readings` (schema exists; seed focus is first four).

**Seed** `scripts/seed_db.py`: requires real ML CSV+metrics; **mock disabled**. Winner → active registry v1.0.

**Endpoints**

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{status, service}` |
| GET | `/metrics/summary` | active model + rmse/mape/mae |
| GET | `/forecasts?start&end` | actual vs xgb/lgb/best |
| GET | `/forecasts/range` | min/max ts |
| GET | `/forecasts/peaks?limit&start&end` | top mixed-risk rows |
| GET | `/forecasts/ahead?hours&as_of&start&end` | recursive forecast + exam/vacation counts |
| GET | `/forecasts/carbon?start&end&hours&as_of` | shave KPIs |
| GET | `/forecasts/today-peak` and `/api/v1/forecasts/today-peak` | live banner |
| POST | `/predict` | one-shot `predict_one` |

CORS `allow_origins=["*"]` GET/POST (`main.py`). Cache: forecast `lru_cache` only, not HTTP cache.

---

# I. Frontend

**Talks only to API** `services/api_client.py`. Timeout 180s. `API_BASE_URL` env (Render set in `render.yaml`).

**Filters:** dates clamped to `/forecasts/range`; peaks 1–50; ahead checkbox; 24h/7d/Match (Match capped 168h).

| KPI | Source | Filter? |
|---|---|---|
| Live temp / 24h peak / time / live CO₂ | `/forecasts/today-peak` | no |
| Model, RMSE, MAPE, MAE | `/metrics/summary` | no (test-set) |
| Actual vs pred chart | `/forecasts` | **yes** Start–End |
| Ahead chart | `/forecasts/ahead` | End/Start as_of + horizon |
| Green Skills four cards | `/forecasts/carbon` | **yes** Start–End |
| Peaks table | `/forecasts/peaks` | **yes** + limit |

Errors: `aura-warn` for HTTP/timeout/connection (`api_client.py`). Empty range → info messages.

Charts: Plotly in `forecast_chart.py`, `ahead_chart.py`.

---

# J. Weak points + honest answers

| Spot | Truth | Why | Improve |
|---|---|---|---|
| Model KPIs look static | They **are** test-set | Contract: one published score | Label “hold-out”; we labeled it |
| Green “no peaks” vs HIGH table | **Two windows** | Ahead vs history | Captions now say so |
| Table used to be all HIGH | Top-N of P90 band | Sort by kW | Now mix HIGH/MED/LOW |
| Date filter on peaks | **Does** apply (`start`/`end`) | Old rumor | Demo it |
| Hard-coded dates | Fallback only if range API fails `2025-09-02`/`2026-09-01` | `app.py` | Prefer API range |
| Calendar | Simplified CSV weeks | No registrar API | Replace with official dates |
| 0.71, 8.50, 21, 350 | Constants | Transparent assumptions | Cite CEA/BESCOM |
| Two lat/lon | Campus vs city KPI | Live banner used city | Unify to Anekal |
| Temp 19°C | CSV fallback if Open-Meteo fails | Timeout/UA | User-Agent + `current=` |
| Recursive drift | Inherent | Trees aren’t seq2seq | Shorter horizon / direct multi-horizon |
| Render sleep | Free tier | Cost | Ping / paid instance |
| Unpinned: uvicorn/pandas ranges | `requirements-*.txt` | Speed | Pin all |
| Evaluation.md vs zones | Report stale | Zones added later | Update report |
| README_DATA “CSV missing” | Stale | CSV is in repo | Ignore that paragraph |
| Not official billing | Footer caption | Ethics | Keep saying it |
| Carbon not measured | Counterfactual | Green-skills demo | Call it estimate |
| No hyperparameter search | Fixed 300/6/0.05 | Time | CV on train only |
| Test = Jun–Sep 2026 | Chronological 20% | Correct method | More years of meters |

---

# K. Question bank (≥100)

**Who:** L=Likitha, A=Anushka, R=Risha, **All** = anyone. **B**=basic **T**=technical **X**=trick.

### Problem / motivation
1. B All — What problem? Reactive BESCOM bills vs proactive 15-min forecast + peak warning.  
2. B L — Heterogeneous fusion? Meter + calendar + weather in one feature row.  
3. B All — Who is the user? Facilities / estate, not the billing office.  
4. T All — Why 15 min? Matches TOD/peak windows and lag math (4 rows = 1 h).  
5. B R — Decision-support not billing? Footer in `app.py`.  
6. X All — Isn’t this just last year’s June? No: test is **future** of train; ahead uses model + live weather.  
7. B L — Academic vs hostel? Different diurnal shape → zone models.  
8. T All — Why not only weather? Weather without lags misses occupancy.  
9. B All — Success metric? Beat persistence RMSE; usable peak flags.  
10. X All — Will this cut the university bill tomorrow? Not guaranteed; it’s a shave **scenario**.

### Data
11. B L — Frequency? 15 min, enforced (`utils.py`).  
12. B L — Range? Usable 2025-09-02 to 2026-09-01.  
13. T L — Why start 2 Sep not 1 Sep? First 96 lags NaN dropped.  
14. T L — Rows? 34,945 usable; 27,956/6,989.  
15. T L — Negative kW? Pipeline **refuses** to train.  
16. T L — Gaps? Irregular intervals raise.  
17. B L — Target column? `Total_Campus_Demand_kW`.  
18. X L — Did you interpolate holes? **Not in code** — fail instead.  
19. B L — Where is CSV? `ML_Implementation/data/alliance_campus_energy_master.csv`.  
20. T L — Duplicate timestamps? Rejected.

### Features
21. B L — List 12 features. See cheat sheet.  
22. T L — Why shift 4 not 1 for 1 hour? 15-min index.  
23. T L — Rolling leak? `shift(1)` first.  
24. B L — Weekend? `Is_Weekend` from CSV.  
25. T L — Exam/vacation at train vs serve? Train: CSV columns. Serve: `academic_calendar.csv`.  
26. X L — Future lag leak? No, only past shifts.  
27. T L — Feature contract? Order frozen in `metrics.json`.  
28. B L — Temp units? °C column `Temperature_C`.  
29. T L — Why include Hour if you have lags? Calendar occupancy pattern.  
30. X L — One-hot Hour? Trees split numeric Hour; not found one-hot.  
31. T L — Missing feature at predict? `predict_one` raises.  
32. B L — Who built features? Likitha, `feature_engineering.py`.

### Models
33. B L — Three models? Persistence, XGB, LGB.  
34. T L — Persistence formula? ŷ_t = y_{t−24h}.  
35. T L — XGB params? 300, 6, 0.05, 0.8, 0.8, seed 42.  
36. T L — Tuning? **Not found** — fixed params.  
37. B L — Why XGB won? Lowest test RMSE.  
38. X L — Overfit? Test still 13.72 vs 79 baseline; depth 6 + subsample. Not a CV curve in repo.  
39. X L — Why not LSTM/Prophet? Short capstone, irregular calendar flags, tree fusion is standard; LSTM needs more data/tuning; Prophet weaker on 15-min + exogenous mix. **We compared a strong naive baseline.**  
40. T L — Objective? `reg:squarederror` (RMSE-aligned).  
41. B L — Production pkl? `aura_ems_best.pkl`.  
42. T L — Zone training? `train_zones.py` same XGB.  
43. X L — Why academic MAPE 22% if RMSE 9.6? MAPE punishes low night kW.  
44. T L — random_state 42? Reproducibility.  
45. B A — Backend loads pkl? `joblib.load` in `forecaster._assets`.  
46. X L — Is XGB a black box? Feature importance plot exists; not SHAP in repo.

### Metrics
47. B L — RMSE formula? √ mean square error.  
48. B L — MAE formula? Mean abs error.  
49. B L — MAPE formula? Mean abs percent, y≠0.  
50. T L — Why RMSE to pick winner? Penalizes peak misses (facilities care about peaks).  
51. T L — MAPE 9.59 good? ~3.5× better than 34% baseline; still ~10% typical error.  
52. X L — Why not R² only? R² can look high with daily seasonality; kW error is operational.  
53. T L — Zero actuals? Count in json = 0.  
54. X L — Why not k-fold? Time series leakage.  
55. T L — Test period? 2026-06-20 → 2026-09-01 (summer/monsoon campus).  
56. B L — Who computed metrics? `evaluate.py` / sklearn.

### Peaks
57. B A — HIGH? ≥ max(350, P90).  
58. T A — P90 of what? Ahead: history used as_of. Table: filtered window rank.  
59. T R — Why all HIGH before? Top-N ⊂ top 10%.  
60. T R — Now? Mix of bands.  
61. B R — Green message? No HIGH in **ahead** horizon.  
62. X R — Bug that table ignores dates? **False** — `start`/`end` passed.  
63. T A — Rank offset P90? `offset(total*0.10)` not exact quantile.  
64. B R — Peaks limit? 1–50.

### CO₂ / money
65. B A — EF? 0.71 kg/kWh hard-coded.  
66. B A — Tariff? ₹8.50/kWh hard-coded.  
67. T A — Energy avoided formula? See section G.  
68. T A — Interval 0.25 h? 15 min.  
69. X All — Real money saved? **Scenario**, not invoice.  
70. B A — Trees? CO₂/21.  
71. T R — Live CO₂ vs Green Skills? Live=next 24h preds; GS=selected history range.  
72. X All — Is 0.71 CEA 2024? **Not cited in code** — say “commonly used India grid factor; we would replace with CEA table.”

### Backend
73. B A — Framework? FastAPI + SQLAlchemy + SQLite.  
74. T A — Why SQLite? Simple deploy; absolute path `aura_ems.db`.  
75. B A — `/health`? `{status: ok, service: aura-ems-backend}`.  
76. T A — Seed without ML? **Exits 1**, mock off.  
77. T A — CORS? `*` GET/POST.  
78. T A — `/predict`? Body `{features: {12 names}}`.  
79. B A — Registry? `model_registry.is_active`.  
80. T A — Caching? `lru_cache` on `forecast_ahead`.  
81. X A — SQL injection? SQLAlchemy bound params.  
82. T A — Who wrote routers? Anushka’s folder; Likitha can name `forecasts.py`.

### Frontend
83. B R — Stack? Streamlit + Plotly + requests.  
84. T R — Why not read pickle? Contract + security/size.  
85. B R — Which KPIs ignore filters? Live four + model four.  
86. B R — Which follow filters? History chart, carbon, peaks.  
87. T R — Ahead Match? Horizon min(window, 168h) from Start.  
88. T R — Timeout? 180s + 24h retry.  
89. X R — Hard-coded chart? No, API items.  
90. B R — Sidebar lock? CSS + JS keep filters open (`theme.py`).

### Render
91. B All — Two services in `render.yaml`.  
92. T A — Backend build seeds DB.  
93. T R — Frontend `API_BASE_URL=https://aura-ems-backend.onrender.com`.  
94. X All — 502 on first click? Free cold start / peaks timeout — Refresh.  
95. B All — Health path `/health`.  
96. T All — Plan free — sleeps.

### Testing / ethics / future
97. B L — Automated tests? **Not found** as a pytest suite in repo.  
98. T All — Validate demo: `/health`, `/metrics/summary`, change dates.  
99. X All — Privacy? Aggregated campus kW, no student IDs in code.  
100. B All — Future? Official calendar, BESCOM TOD, pin deps, unify lat/lon, direct multi-horizon, more meter years.  
101. X L — Generalize to another campus? Same pipeline, **new CSV + retrain**; numbers won’t transfer.  
102. X L — Lookup table of past days? Baseline **is** that; we **beat** it by 66 kW RMSE.  
103. T A — POST predict vs ahead? One vector vs recursive loop.  
104. T R — Show XGB/LGB lines? Checkbox `show_model_lines`.  
105. X All — Why Streamlit not React? Team Python, time; design HTML in `new_design/` was reference only.  
106. B All — Who is lead? Likitha, ML + integration.  
107. X R — Did Risha train XGB? No — she charts API JSON.  
108. X A — Did Anushka invent RMSE 13.72? No — seeded from Likitha’s `metrics.json`.  
109. T L — LightGBM closer MAPE but worse RMSE? More large peak errors.  
110. B All — Demo backup? Screenshots + `ml_evaluation.md` table if Render sleeps.

---

# L. 12-minute run of show

| Min | Who | Slide / action |
|---|---|---|
| 0:00–0:45 | Likitha | Problem + pitch |
| 0:45–2:30 | Likitha | Architecture diagram (3 modules, API contract) |
| 2:30–5:30 | Likitha | Data, leak-safe features, split, baseline vs XGB numbers |
| 5:30–7:00 | Anushka | SQLite seed, 4 key endpoints, ahead recursion in one sentence |
| 7:00–8:30 | Risha | Dashboard tour: what follows filters vs not |
| 8:30–10:30 | Risha + Likitha | **Live demo** (script below) |
| 10:30–12:00 | Likitha | Limits + “not BESCOM” + future | 
| 12–15 | All | Questions |

**Slides (10):** (1) Title (2) Problem (3) Architecture (4) Features/leakage (5) Results table (6) Ahead + weather (7) Peaks + carbon formulas (8) Demo screenshots (9) Limits (10) Thank you + roles.

**Demo script:** Health → KPIs (say test-set vs live) → set Start 20 Jun 2026 End 1 Sep → history chart → Match/24h ahead → say green banner ≠ table → peaks mix → carbon changes if you shrink dates. **If down:** open `reports/actual_vs_predicted.png` + metrics table + this cheat sheet.

**Morning checklist:** Render both **Manual Deploy**; hit `/health`; open dashboard once to wake; screenshots on USB; `PRESENTATION_PREP.md` printed; agree who answers LSTM/overfit/billing.

---

# M. Cross-answers (“who built this?”)

- **Likitha on backend:** “Anushka’s FastAPI seeds my `dashboard_inference_feed.csv` into `forecasts` and serves JSON; I don’t query SQLite from Streamlit.”  
- **Likitha on frontend:** “Risha only calls `api_client._get`; filters become query params.”  
- **Anushka on ML:** “Winner is XGBoost by test RMSE 13.72 in metrics.json.”  
- **Risha on ML:** “I display registry metrics; I don’t recompute RMSE.”
