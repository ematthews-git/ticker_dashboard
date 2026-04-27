import streamlit as st
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
from plotly import graph_objects as go


def render_mention_trends(df_raw: pd.DataFrame) -> None:
    """Render the mention trends chart based on the provided data.

    Args:
        df_raw (pd.DataFrame): Raw mention data with columns 'timestamp', 'avg_sentiment', and 'mention_count'.
    """

    if df_raw.empty:
        st.info("No mention data available to display mention trends.")
        return

    if "ticker" not in st.session_state or not st.session_state.ticker:
        st.info("Please enter a ticker symbol to display mention trends.")
        return

    ticker = st.session_state.ticker
    st.subheader(f"Mention Trends for {ticker}")

    if "daily_bucket" not in st.session_state or not st.session_state.daily_bucket:
        daily_bucket = False
    else:
        daily_bucket = st.session_state.daily_bucket

    df = (
        df_raw.groupby("timestamp")
        .agg(mention_count=("mention_count", "sum"))
        .reset_index()
        .sort_values("timestamp")
    )

    if daily_bucket:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.floor("D")
        df = (
            df.groupby(["timestamp"])
            .agg(
                mention_count=("mention_count", "sum"),
            )
            .reset_index()
        )

    if len(df) < 5:
        st.warning(
            "Insufficent data to visualise mention trends. Try a longer timeframe."
        )
        return

    # hour over hour data
    df["delta"] = df["mention_count"].diff()

    # rolling average window, depends on data length
    window = min(6, max(2, len(df) // 5))
    df["rolling_avg"] = df["delta"].rolling(window=window, center=True).mean()

    # percentage change
    df["pct_change"] = df["mention_count"].pct_change()

    # no delta on first row
    df = df.dropna(subset=["delta"])

    df["colour"] = df["delta"].apply(lambda d: "#2ca02c" if d >= 0 else "#d62728")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df["timestamp"],
            y=df["delta"],
            name="mentions",
            marker_color=df["colour"],
            opacity=0.7,
            hovertemplate=("<b>%{x}</b><br>Mentions: %{y:+d}<br><extra></extra>"),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["rolling_avg"],
            name=f"Rolling Avg ({window}-period)",
            line=dict(color="#ff7f0e", width=2.5),
            hovertemplate=("<b>%{x}</b><br>Rolling Avg: %{y:.1f}<br><extra></extra>"),
        ),
        secondary_y=False,
    )

    df["cumulative"] = df["mention_count"].cumsum()
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["cumulative"],
            name="Cumulative Mentions",
            line=dict(color="#1f77b4", width=1.5, dash="dot"),
            opacity=0.5,
            hovertemplate=("<b>%{x}</b><br>Total so far: %{y:,}<br><extra></extra>"),
        ),
        secondary_y=True,
    )
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(
            orientation="h",
            y=1.02,
            x=0.0,
            xanchor="left",
            yanchor="bottom",
        ),
        barmode="relative",
    )

    fig.update_yaxes(title_text="Δ Mentions", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative", secondary_y=True)

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="grey", line_width=0.8)

    # Summary metrics
    cols = st.columns(3)

    peak_accel = df.loc[df["delta"].idxmax()]
    peak_decel = df.loc[df["delta"].idxmin()]
    current_momentum = (
        df["rolling_avg"].iloc[-1] if not df["rolling_avg"].isna().all() else 0
    )

    cols[0].metric(
        label="Current Momentum",
        value=f"{current_momentum:+.1f}",
        help="Latest rolling average of mention deltas. Positive = accelerating.",
    )
    cols[1].metric(
        label="Peak Acceleration",
        value=f"+{peak_accel['delta']:.0f}",
        help=f"Largest hour-over-hour increase at {peak_accel['timestamp']}",
    )
    cols[2].metric(
        label="Peak Deceleration",
        value=f"{peak_decel['delta']:.0f}",
        help=f"Largest hour-over-hour decrease at {peak_decel['timestamp']}",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_mention_heatmap(df_raw: pd.DataFrame) -> None:
    """Render a heatmap of mention counts by hour-of-day and day-of-week.

    Args:
        df_raw (pd.DataFrame): Raw mention data with columns 'timestamp' and 'mention_count'.
    """

    if "ticker" not in st.session_state or not st.session_state.ticker:
        st.info("Please enter a ticker symbol to display the mention heatmap.")
        return

    if df_raw.empty:
        st.warning("No data available for mention heatmap.")
        return

    DAY_ORDER = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    heatmap_df = df_raw[["timestamp", "mention_count"]].copy()
    heatmap_df["timestamp"] = pd.to_datetime(heatmap_df["timestamp"])

    heatmap_df["hour"] = heatmap_df["timestamp"].dt.hour
    heatmap_df["day_name"] = heatmap_df["timestamp"].dt.day_name()

    # Aggregate: total mentions per (day, hour) cell
    grid = (
        heatmap_df.groupby(["day_name", "hour"])
        .agg(mention_count=("mention_count", "sum"))
        .reset_index()
    )

    # Pivot into matrix form
    pivot = grid.pivot(index="day_name", columns="hour", values="mention_count")

    # Reindex to ensure all hours and days are present
    pivot = pivot.reindex(index=DAY_ORDER, columns=range(24), fill_value=0)

    # Format hour labels (e.g. "00:00", "13:00")
    hour_labels = [f"{h:02d}:00" for h in range(24)]

    # Build heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=hour_labels,
            y=DAY_ORDER,
            colorscale=[
                [0.0, "#f7f7f7"],
                [0.25, "#fdd49e"],
                [0.5, "#fdbb84"],
                [0.75, "#e34a33"],
                [1.0, "#b30000"],
            ],
            hovertemplate=("<b>%{y} %{x}</b><br>Mentions: %{z:,}<br><extra></extra>"),
            colorbar=dict(title="Mentions"),
        )
    )

    fig.update_layout(
        xaxis_title="Hour (UTC)",
        yaxis_title="",
        margin=dict(t=20, b=40, l=80, r=20),
        yaxis=dict(autorange="reversed"),  # Monday at top
    )

    # Peak activity summary
    if not grid.empty:
        peak = grid.loc[grid["mention_count"].idxmax()]
        quiet = grid.loc[grid["mention_count"].idxmin()]

        cols = st.columns(2)
        cols[0].metric(
            label="Peak Activity",
            value=f"{peak['day_name']} {int(peak['hour']):02d}:00 UTC",
            delta=f"{int(peak['mention_count']):,} mentions",
        )
        cols[1].metric(
            label="Quietest Window",
            value=f"{quiet['day_name']} {int(quiet['hour']):02d}:00 UTC",
            delta=f"{int(quiet['mention_count']):,} mentions",
            delta_color="inverse",
        )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "💡 This heatmap works best with 7+ days of data. "
        "Select a longer timeframe for more complete coverage."
    )
