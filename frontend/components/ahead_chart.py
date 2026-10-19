"""Demand Forecast Ahead — Plotly chart matching Calculated Caliber colors."""
import plotly.graph_objects as go
import streamlit as st

TOTAL, ACADEMIC, HOSTEL = "#0F766E", "#64748B", "#A8A29E"
MUTED, GRID = "#374151", "#F0EFEA"


def render_ahead_chart(ahead_df) -> None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ahead_df["ts"], y=ahead_df["total_kw"], name="Total campus",
        mode="lines", line=dict(color=TOTAL, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=ahead_df["ts"], y=ahead_df["academic_kw"], name="Academic blocks",
        mode="lines", line=dict(color=ACADEMIC, width=1.75),
    ))
    fig.add_trace(go.Scatter(
        x=ahead_df["ts"], y=ahead_df["hostel_kw"], name="Hostels",
        mode="lines", line=dict(color=HOSTEL, width=1.75),
    ))
    # BESCOM peak tariff window shade (18:00–22:00 each day in range)
    for day in ahead_df["ts"].dt.normalize().unique():
        x0 = day + __import__("pandas").Timedelta(hours=18)
        x1 = day + __import__("pandas").Timedelta(hours=22)
        fig.add_vrect(x0=x0, x1=x1, fillcolor="#F2F3FC", opacity=0.85, line_width=0)

    high = ahead_df[ahead_df["risk_level"] == "HIGH"]
    if not high.empty:
        peak_row = high.loc[high["total_kw"].idxmax()]
        fig.add_trace(go.Scatter(
            x=[peak_row["ts"]], y=[peak_row["total_kw"]], mode="markers+text",
            marker=dict(color="#B91C1C", size=9, line=dict(color="#FFF", width=1.5)),
            text=[f"{peak_row['total_kw']:.0f} kW"], textposition="top center",
            textfont=dict(color="#B91C1C", size=11), name="Peak", showlegend=False,
        ))

    fig.update_layout(
        margin=dict(l=40, r=16, t=24, b=40),
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", color=MUTED, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(showgrid=False, color=MUTED),
        yaxis=dict(title="kW", gridcolor=GRID, griddash="dash", color=MUTED),
        hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch")
