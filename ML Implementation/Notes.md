# AURA-EMS — ML Module Review Notes (Likitha)

> Use this as a talking script during the project guide review. Speak from the headings, use the numbers as-is from `outputs/metrics.json`.

---

## 1. The Problem

Alliance University's campus energy demand is dynamic — academic blocks peak in daytime, hostels peak early morning/late night, and usage shifts around exams, holidays, and weather. The old approach looks only at **past billing data** (reactive). My module builds a **predictive ML pipeline** so the university can see demand *before* it happens (proactive) and avoid BESCOM peak-tariff penalties.

**Target variable:** `Total_Campus_Demand_kW`

---

## 2. My Pipeline, Step by Step

| Step | What I did | Why |
|---|---|---|
| **1. Data validation** | Checked the dataset: 15-minute interval smart-meter data, ~35,000 rows, one full year (2025-09-02 → 2026-09-01), no duplicate timestamps, sorted chronologically | Bad timestamps or gaps would silently break lag features later |
| **2. Feature engineering** | Built lag features (`Load_Lag_1hr`, `Load_Lag_2hr`, `Load_Lag_24hr`) and rolling stats (`Load_Rolling_Mean_4hr`, `Load_Rolling_Std_4hr`) using `.shift()` before `.rolling()` | Prevents the model from ever seeing "future" data when predicting — this is the #1 rule in time-series ML |
| **3. Chronological split** | 80/20 split **by time**, not randomly — 27,956 train rows / 6,989 test rows | Random shuffling would let the model "peek" at future patterns — that's data leakage and gives fake accuracy |
| **4. Baseline model** | Built a simple persistence baseline first (assume demand looks like it did ~24hrs ago) | Gives a fair reference point — proves the real model adds value, not just complexity |
| **5. Model training** | Trained **XGBoost** and **LightGBM** regressors on top of engineered features | Both handle non-linear, tabular time-series-with-context data well |
| **6. Evaluation** | Compared RMSE, MAE, MAPE across Baseline / XGBoost / LightGBM | Multiple metrics give a fuller picture than one number alone |
| **7. Model selection** | Picked lowest **test RMSE** as the winner | RMSE penalizes large errors more — important since missing a peak-demand spike is costlier than several small misses |
| **8. Export for team** | Saved `aura_ems_best.pkl`, `metrics.json`, `dashboard_inference_feed.csv` | Backend (Anushka) loads these into DB; frontend (Risha) never touches my raw files directly |

---

## 3. The Results 

| Model | RMSE (kW) | MAE (kW) | MAPE (%) |
|---|---|---|---|
| Baseline (persistence) | 79.44 | 36.54 | 34.00 |
| **XGBoost (winner)** | **13.52** | **9.09** | **9.59** |
| LightGBM | 16.68 | 9.86 | 9.88 |


> "XGBoost cuts RMSE by about 83% compared to the naive baseline — from ~79 kW error down to ~13.5 kW — and holds MAPE under 10%, which is a strong result for short-term demand forecasting."

**Why XGBoost over LightGBM:** lower RMSE *and* lower MAPE on the same test set — not an arbitrary pick.

---

## 4. Anticipated Questions & My Answers

**Q: Why not randomly shuffle train/test?**
> Random shuffling would mix future rows into training, letting the model implicitly learn from data it shouldn't have access to yet. I always train on the past and test on the future.

**Q: How did you prevent data leakage in your features?**
> Every rolling feature uses `.shift(1)` before `.rolling(...)`, so the value at any row never includes that row's own target. Lag features (`shift(4)`, `shift(8)`, `shift(96)`) only look backward.

**Q: Why is a baseline required?**
> Without it, a low RMSE number means nothing on its own. The baseline proves the ML model is actually learning something useful — an 83% improvement is only meaningful next to a reference point.

**Q: What do RMSE and MAPE mean in plain terms?**
> RMSE is the average prediction error in kW, weighted more heavily toward large misses. MAPE is the average error as a percentage of actual demand — easier to communicate to non-technical stakeholders (e.g. "about 9.6% off on average").

**Q: Does this forecast individual zones or just total campus demand?**
> Currently just total campus demand — that's the current scope. Zone-level forecasting would be a natural next step, not yet implemented.

**Q: What happens if the model's error is high in production?**
> The metrics are exposed transparently through the API/dashboard rather than hidden — if error rises, the team can see it via the KPI cards and retrain/investigate rather than silently trusting a stale model.

---

## 5. Limitations

- Forecasts **total campus demand**, not per-zone/per-building yet.
- Assumes **weather data is available at forecast time** — reasonable for short-term forecasts, but worth stating explicitly.
- Trained on **one year of synthetic/campus data** — more historical data (multiple years) would make seasonal patterns more robust.

---

## 6. How My Part Connects to the Team

```
My ML outputs (pkl / csv / json)
        ↓
Anushka's backend (seeds SQLite, serves via FastAPI)
        ↓
Risha's Streamlit dashboard (KPIs, actual-vs-predicted chart, peak-risk panel)
```

I don't build the dashboard or the API — I hand off clean, contract-matched files so the rest of the pipeline can trust them without needing to understand my modeling choices.

---

## 7. What to Show Live During Review

1. Open `outputs/metrics.json` — point to the RMSE/MAPE table above.
2. Open `reports/actual_vs_predicted.png` — show how closely predicted demand tracks actual demand.
3. Open `reports/feature_importance.png` — show which features (likely lag/rolling demand features) drive predictions most.
4. Open `outputs/dashboard_inference_feed.csv` — show the exact rows that feed into the dashboard.
5. (Optional) Open `reports/ml_evaluation.md` — the full written report backing all of the above.

---

## 8. One-Line Summary (memorize this)

> "I prove the forecasting model is valid, leak-safe, and roughly 83% more accurate than a simple baseline — and I export it in a form the backend and dashboard can trust without touching my raw files."