"""Section C — Actual vs Predicted (Calculated Caliber chart colors)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ACTUAL = "#15181E"
BEST = "#0F766E"
XGB = "#64748B"
LGB = "#A8A29E"
GRID = "#F0EFEA"
MUTED = "#374151"


def render_forecast_chart(items: list, show_model_lines: bool = False) -> None:
    if not items:
        st.info("No forecast data available for the selected range.")
        return

    df = pd.DataFrame(items)
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["actual_demand_kw"], name="Actual Demand",
        mode="lines", line=dict(color=ACTUAL, width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["ts"], y=df["best_pred_kw"], name="Best Predicted Demand",
        mode="lines", line=dict(color=BEST, width=2, dash="dash"),
    ))
    if show_model_lines:
        if "xgb_pred_kw" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["ts"], y=df["xgb_pred_kw"], name="XGBoost",
                mode="lines", line=dict(color=XGB, width=1.25),
            ))
        if "lgb_pred_kw" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["ts"], y=df["lgb_pred_kw"], name="LightGBM",
                mode="lines", line=dict(color=LGB, width=1.25),
            ))

    fig.update_layout(
        margin=dict(l=40, r=16, t=16, b=40),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", color=MUTED, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12, color=MUTED)),
        xaxis=dict(showgrid=False, zeroline=False, color=MUTED),
        yaxis=dict(
            title="kW",
            showgrid=True,
            gridcolor=GRID,
            griddash="dash",
            zeroline=False,
            color=MUTED,
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch")
