import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from config import timeframe_map
from cache import (
    get_top_tickers_1h,
)
from utils import aggregate_sentiment_to_timestamp


def render_correlation_charts(df_raw: pd.DataFrame, price_df_raw: pd.DataFrame) -> None:
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
    timeframe = st.session_state.timeframe

    cols = st.columns([1, 1, 1])

    left_cell = cols[0].container(border=True, height="stretch")
    mid_cell = cols[1].container(border=True, height="content")
    right_cell = cols[2].container(border=True, height="stretch")

    # Create predictive and reactive correlation charts
    # PREDICTIVE
    if not ticker:
        st.info("Please enter a ticker symbol to display correlation data.")
    else:
        # aggregates per timestamp the weighted sentiment and total mention count
        sentiment_df = aggregate_sentiment_to_timestamp(df_raw, weighted=True)

        price_df_sorted = price_df_raw.sort_values("timestamp")
        price_df_sorted["price_change"] = (
            price_df_sorted["close"].pct_change().shift(-1)
        )

        corr_df = pd.merge(
            sentiment_df,
            price_df_sorted[["timestamp", "price_change"]],
            on="timestamp",
            how="inner",
        ).dropna()

        fig_corr = px.scatter(
            corr_df,
            x="weighted_sentiment",
            y="price_change",
            trendline="ols",
            labels={
                "weighted_sentiment": "Sentiment",
                "price_change": "Next Period Price Change",
            },
            hover_data=["timestamp"],
        )
        fig_corr.update_layout(margin=dict(t=30, b=20, l=20, r=20))

        # REACTIVE
        corr_df_reactive = pd.merge(
            sentiment_df,
            price_df_sorted[["timestamp", "price_change"]],
            on="timestamp",
            how="inner",
        ).dropna()

        # Shift sentiment forward instead of price
        corr_df_reactive["next_sentiment"] = corr_df_reactive[
            "weighted_sentiment"
        ].shift(-1)
        corr_df_reactive = corr_df_reactive.dropna()

        fig_reactive = px.scatter(
            corr_df_reactive,
            x="next_sentiment",
            y="price_change",
            trendline="ols",
            labels={
                "price_change": "Price Change",
                "next_sentiment": "Next Period Sentiment",
            },
            hover_data=["timestamp"],
        )

        with left_cell:
            st.subheader(
                "Correlation Between Sentiment and Next Period Price Change (Predictive)"
            )
            st.plotly_chart(fig_corr, width="stretch")

        with mid_cell:
            st.subheader(
                "Correlation Between Sentiment and Previous Period Price Change (Reactivity)"
            )
            st.plotly_chart(
                fig_reactive,
                width="stretch",
            )

        with right_cell:
            # Should only go head where timestamp <= 14 days
            if timeframe_map[timeframe] not in ["336h", "720h"]:
                st.warning(
                    "Lag analysis requires at least 14 days of data. Please select a longer timeframe to view this analysis."
                )
            else:
                st.subheader(
                    "Correlation Between Sentiment and Future Price Change at Different Lags"
                )
                LAGS = [1, 2, 4, 6, 12, 24]

                # aggregates per timestamp the weighted sentiment and total mention count
                sentiment_df = aggregate_sentiment_to_timestamp(df_raw, weighted=True)

                price_df_sorted = price_df_raw.sort_values("timestamp")
                price_df_sorted["price_change"] = (
                    price_df_sorted["close"].pct_change().shift(-1)
                )

                # r-value
                merged = pd.merge(
                    sentiment_df,
                    price_df_sorted[["timestamp", "price_change"]],
                    on="timestamp",
                    how="inner",
                ).dropna()

                lag_results = []
                for lag in LAGS:
                    lagged = merged.copy()
                    lagged["price_change"] = lagged["price_change"].shift(-lag)
                    lagged = lagged.dropna()
                    if len(lagged) > 2:
                        r = lagged["weighted_sentiment"].corr(lagged["price_change"])
                        lag_results.append({"lag": lag, "r": r})

                lag_df = pd.DataFrame(lag_results)

                if not lag_df.empty:
                    fig_lag = px.bar(
                        lag_df,
                        x="lag",
                        y="r",
                        labels={"lag": "Lag (hours)", "r": "Correlation Coefficient"},
                    )
                    fig_lag.add_hline(y=0, line_dash="dash", line_color="grey")
                    fig_lag.update_layout(margin=dict(t=20, b=20, l=20, r=20))

                    st.plotly_chart(fig_lag, width="stretch")
                else:
                    st.info(
                        "Not enough data points to perform lag analysis. Please select a longer timeframe or a more popular ticker."
                    )


def render_top_tickers() -> None:
    cols = st.columns([1, 2])

    bottom_left_cell = cols[0].container(border=True, height="stretch")

    with bottom_left_cell:
        hours = st.text_input(
            "Lookback Hours",
            value="12",
            placeholder="Enter number of hours to look back (e.g. 12)",
        )

        # display df underneath
        if hours.isdigit():
            top_tickers_df = get_top_tickers_1h(hours=int(hours))
            st.dataframe(top_tickers_df, width="stretch")
        else:
            st.warning("Please enter a valid number of hours to look back.")
