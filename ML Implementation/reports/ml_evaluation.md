# AURA-EMS ML Evaluation

## Dataset
- Rows after feature-related dropna: 34,945
- Usable date range: 2025-09-02 00:00:00 to 2026-09-01 00:00:00
- Evaluation date range: 2026-06-20 05:00:00 to 2026-09-01 00:00:00
- Frequency: 15 minutes (validated before feature generation)
- Target: `Total_Campus_Demand_kW`

## Split
- Method: chronological 80/20 (past for training, future for testing)
- Train size: 27,956
- Test size: 6,989

## Features
- `Hour`
- `DayOfWeek`
- `Month`
- `Temperature_C`
- `Is_Weekend`
- `Is_Vacation`
- `Is_Exam_Cycle`
- `Load_Lag_1hr`
- `Load_Lag_2hr`
- `Load_Lag_24hr`
- `Load_Rolling_Mean_4hr`
- `Load_Rolling_Std_4hr`

Lag features use past values only. Four-hour rolling statistics use `shift(1)` before a 16-row rolling window; no current or future target enters the features. No random shuffle is used.

## Results
| Model | RMSE (kW) | MAE (kW) | MAPE |
|---|---:|---:|---:|
| Baseline | 79.437 | 36.543 | 34.00% |
| XGBoost | 13.522 | 9.089 | 9.59% |
| LightGBM | 16.678 | 9.864 | 9.88% |

MAPE is computed over nonzero actual-demand rows; zero actual values are excluded because percentage error is undefined there. RMSE penalizes larger misses more heavily; MAE is the average absolute miss in kW.

## Winner
- Model: XGBoost
- Rule: lowest RMSE on the held-out future test set.
- Production artifact: `models/aura_ems_best.pkl`

## Limitations
- This is a campus-total forecast, not zone-level forecasting.
- Temperature is assumed available at forecast time; future weather forecast error is not modeled.
- The benchmark and test period cover only the supplied dataset and may not represent future operating conditions.
