# Likitha's AURA-EMS Role and Project Guide

## Your role

You own the forecasting brain of AURA-EMS: the work that turns historical campus energy readings into a tested, leak-safe prediction and a small set of artifacts the backend and dashboard can consume. Your role is to understand and validate the data, build time-aware features, compare a simple benchmark with stronger models, evaluate on future data, select one winner, and explain the evidence honestly.

You do not own the Streamlit dashboard or the FastAPI/SQLite backend. Keep the handoff stable: the backend consumes the inference CSV and metrics, while the dashboard presents those results. It should not load your model pickle directly.

## The project in plain language

Alliance University campus demand changes with time of day, weekday/weekend patterns, exams and vacations, and temperature. A reactive process notices energy use after it happens; forecasting gives the campus an estimate of upcoming total demand so people can plan proactively.

The current prediction target is `Total_Campus_Demand_kW`. The current scope is campus-total demand, not separate building or zone forecasts.

## How the ML work fits together

1. **Validate the source.** Confirm timestamps parse, sort into time order, contain no duplicates, stay at 15-minute intervals, and have usable nonnegative target values. The pipeline prints a quality summary and stops when the assumptions needed for row-based time features are broken.
2. **Build past-only signals.** Four rows represent one hour, eight rows two hours, and 96 rows one day. The 4-hour rolling mean and standard deviation use the previous 16 values after `shift(1)`, never the current row's target.
3. **Split by time.** The first 80% of usable observations train the models; the last 20% test them. Random splitting would let the model learn from later periods while being evaluated on earlier ones, which is not the real forecasting situation.
4. **Establish a baseline.** The 24-hour persistence benchmark predicts that demand will match the same time yesterday. XGBoost and LightGBM must be compared against this simple reference, not just against each other.
5. **Choose and hand off.** The current rule is lowest test RMSE. Save one best model, all model metrics, and test-period predictions with a timestamp index. Keep the feature names and order stable for the backend handoff.

## What the evaluation numbers mean

- **RMSE (kW):** a typical error scale that penalizes large misses more strongly. For example, an RMSE of 20 kW means errors are around that scale, with large errors weighted more heavily; it is not a guarantee that every prediction is within 20 kW.
- **MAE (kW):** the average absolute distance between predicted and actual demand. It is directly in kW and easier to interpret as an average miss.
- **MAPE (%):** average absolute error relative to actual demand. It is not defined when actual demand is zero; this project's metric excludes those rows and reports how many were excluded.
- **Peak risk:** intervals with high predicted demand are candidate periods for operational attention. A forecast alone is not an alarm threshold; agree thresholds with campus operations and account for model error.

## Your integration handoff

Give the backend owner `models/aura_ems_best.pkl`, `outputs/dashboard_inference_feed.csv`, and `outputs/metrics.json`, plus the exact feature order recorded in metrics. Give the dashboard owner the actual-versus-predicted interpretation, the RMSE/MAPE explanation above, and the caveat that peak risk means predicted high load, not a guaranteed event.

## Mentor questions to be ready for

- **Why not random splitting?** Forecasting predicts the future from the past, so the test set must occur after the training set.
- **Why boosted trees rather than only ARIMA?** The supplied feature design includes calendar, weather, and operational indicator columns plus recent demand history. Boosted trees can combine these inputs; a future model study could compare against ARIMA or other time-series methods under the same chronological evaluation.
- **How is leakage prevented?** Lag features shift demand into the past, rolling statistics shift by one before aggregation, and the test period follows the train period without shuffling.
- **Why is the baseline required?** It establishes whether the learned models improve on a simple, explainable 24-hour persistence rule.
- **Is it zone-level?** No. The current target is total campus demand only.

## Work recorded in this workspace

Implemented in this workspace: shared data-quality validation, stable feature engineering, a chronological 80/20 split, a 24-hour baseline, XGBoost and LightGBM training scripts, RMSE/MAE/MAPE evaluation, winner selection, a dashboard-feed exporter, plot/report generation, dependency setup, and this role/project guide.

Still requiring the source CSV: validation of the real campus data, actual model fitting, measured model comparison, generated `.pkl` model files, populated metrics and prediction feed, plots, and a data-backed final report. No model performance result is claimed before that run. Git branching and PR creation also require this folder to be connected to the team repository.

## Commands to finish the data-backed run

From the project root, install `requirements-ml.txt`, place the master CSV in `data/`, then run:

```powershell
python -m ml.feature_engineering
python -m ml.train
python -m ml.evaluate
```

Review the printed data-quality summary, `outputs/metrics.json`, generated `reports/ml_evaluation.md`, and test-period plot before sharing results or making claims in a PR.