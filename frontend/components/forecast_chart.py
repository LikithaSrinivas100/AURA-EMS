"""Section C — Actual vs Predicted demand chart, sourced from /forecasts."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_forecast_chart(items: list, show_model_lines: bool = False) -> None:
    """Render the actual-vs-predicted line chart.

    items: list of dicts shaped like the /forecasts "items" array
           (ts, actual_demand_kw, best_pred_kw, xgb_pred_kw, lgb_pred_kw)
    show_model_lines: also plot the individual XGBoost / LightGBM lines
    """
    if not items:
        st.info("No forecast data available for the selected range.")
        return

    df = pd.DataFrame(items)
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["actual_demand_kw"],
        name="Actual Demand", mode="lines",
        line=dict(color="#264653", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["best_pred_kw"],
        name="Best Predicted Demand", mode="lines",
        line=dict(color="#e76f51", width=2, dash="dash"),
    ))

    if show_model_lines:
        if "xgb_pred_kw" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["ts"], y=df["xgb_pred_kw"],
                name="XGBoost", mode="lines",
                line=dict(color="#2a9d8f", width=1),
            ))
        if "lgb_pred_kw" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["ts"], y=df["lgb_pred_kw"],
                name="LightGBM", mode="lines",
                line=dict(color="#e9c46a", width=1),
            ))

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Demand (kW)",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
