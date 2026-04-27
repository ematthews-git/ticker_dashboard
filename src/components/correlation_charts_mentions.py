import streamlit as st
import pandas as pd
import plotly.express as px


def render_corr_charts_mentions(
    df_raw: pd.DataFrame, price_df_raw: pd.DataFrame
) -> None:
    """Render the predictive, reactive, and lagged correlation charts based on the provided data.

    Args:
        df_raw (pd.DataFrame): Raw mention data with columns 'timestamp', 'avg_sentiment', and 'mention_count'.
        price_df_raw (pd.DataFrame): Raw price data with columns 'timestamp' and 'price'.
    """

    # get ticker and timeframe from session state
    if "ticker" not in st.session_state:
        st.session_state.ticker = st.query_params.get("ticker", "").upper()

    if "timeframe" not in st.session_state:
        st.session_state.timeframe = st.query_params.get("timeframe", "3 Days")

    ticker = st.session_state.ticker
    # timeframe = st.session_state.timeframe

    cols = st.columns([1, 1, 1])

    left_cell = cols[0].container(border=True, height="stretch")
    mid_cell = cols[1].container(border=True, height="content")
    # right_cell = cols[2].container(border=True, height="stretch")

    # Create predictive and reactive correlation charts
    # PREDICTIVE
    if not ticker:
        st.info("Please enter a ticker symbol to display correlation data.")
    else:
        # aggregates per timestamp total mention count
        mentions_df = (
            df_raw.groupby("timestamp")
            .apply(lambda x: pd.Series({"mention_count": x["mention_count"].sum()}))
            .reset_index()
            .sort_values("timestamp")
        )

        price_df_sorted = price_df_raw.sort_values("timestamp")
        price_df_sorted["price_change"] = (
            price_df_sorted["close"].pct_change().shift(-1)
        )

        # Merge sentiment and price data on timestamp
        merged_predictive = pd.merge(
            mentions_df[["timestamp", "mention_count"]],
            price_df_sorted[["timestamp", "price_change"]],
            on="timestamp",
            how="inner",
        ).dropna()

        fig_corr = px.scatter(
            merged_predictive,
            x="mention_count",
            y="price_change",
            trendline="ols",
            labels={
                "mention_count": "Mention Count",
                "price_change": "Next Period Price Change",
            },
            hover_data=["timestamp"],
        )
        fig_corr.update_layout(margin=dict(t=20, b=20, l=20, r=20))

        with left_cell:
            st.subheader(
                "Correlation Between Mention Count and Next Period Price Change (Predictive)"
            )
            st.plotly_chart(
                fig_corr,
                width="stretch",
            )

        # REACTIVE
        merged_reactive = pd.merge(
            mentions_df[["timestamp", "mention_count"]],
            price_df_sorted[["timestamp", "price_change"]],
            on="timestamp",
            how="inner",
        ).dropna()

        # shift mention count forward instead of price
        merged_reactive["next_mention_count"] = (
            merged_reactive["mention_count"].shift(-1).dropna()
        )

        fig_reactive = px.scatter(
            merged_reactive,
            x="next_mention_count",
            y="price_change",
            trendline="ols",
            labels={
                "next_mention_count": "Next Period Mention Count",
                "price_change": "Price Change",
            },
            hover_data=["timestamp"],
        )
        fig_reactive.update_layout(margin=dict(t=20, b=20, l=20, r=20))

        with mid_cell:
            st.subheader(
                "Correlation Between Mention Count and Next Period Price Change (Reactivity)"
            )
            st.plotly_chart(
                fig_reactive,
                width="stretch",
            )
