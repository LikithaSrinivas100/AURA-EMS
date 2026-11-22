# AURA-EMS ML Evaluation (simulated data)

Target: `Total_Campus_Demand_kW` · Interval: 15 min · Max horizon: 168 h

## Results
| Model | RMSE | MAE | MAPE | R2 |
|---|---:|---:|---:|---:|
| Baseline | 79.437 | 36.543 | 34.00% | 0.3842 |
| SeasonalNaive7Day | 50.571 | 22.278 | 17.95% | 0.7504 |
| XGBoost | 13.718 | 9.158 | 9.59% | 0.9816 |
| LightGBM | 16.678 | 9.864 | 9.88% | 0.9729 |

Winner (trees): **XGBoost** by lowest test RMSE.

## Peak-alert (threshold from TRAIN only)
- Rule: max(350, train_p90) → **350.00 kW** (train P90=292.38)
- Precision=0.3636 Recall=0.1905 F1=0.2500 FAR=0.0010

## Horizon error
See `outputs/horizon_error.csv` and `reports/horizon_error.png`.
