"""TC_F0: target definition fields on /metrics/summary schema."""
from app.schemas import MetricsSummaryResponse


def test_tc_f0_metrics_summary_has_target_definition_fields():
    m = MetricsSummaryResponse(
        active_model="XGBoost",
        rmse=1.0,
        mape=1.0,
        mae=1.0,
        train_rows=1,
        test_rows=1,
    )
    assert m.target == "Total_Campus_Demand_kW"
    assert m.interval_minutes == 15
    assert m.max_horizon_hours == 168
    assert m.data_source == "simulated"
