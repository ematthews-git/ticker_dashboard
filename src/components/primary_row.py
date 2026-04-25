import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.express as px
from plotly.subplots import make_subplots
from plotly import graph_objects as go
from utils import sentiment_to_colour, aggregate_sentiment_to_timestamp
from config import SUBREDDITS, timeframe_map
from cache import (
    get_mention_data_1h,
    get_price_data_1h,
    get_top_tickers_12h,
)


def render_primary_row(
    daily_bucket: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Render the primary row of the dashboard, which includes subreddit selection, ticker input, timeframe selection, and data display.

    Args:
        daily_bucket (bool, optional): Whether to group data into daily buckets. Defaults to False.
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: The raw mention data and price data dataframes used for the correlation charts.
    """

    # displays across top of page
    def render_ticker_bar(top_tickers: pd.DataFrame) -> None:
        """Render a bar across the top of the page featuring the top tickers daily.

        Args:
            top_tickers (pd.DataFrame): Dataframe containing top tickers with columns 'ticker' and 'mention_count'.
        """
        st.markdown("#### Top Daily Tickers")

        cols = st.columns(len(top_tickers))
        for col, row in zip(cols, top_tickers.itertuples()):
            col.markdown(f"**{row.ticker}**  \n{row.total_mentions:,} mentions")

    top_tickers_df = get_top_tickers_12h()
    if not top_tickers_df.empty:
        render_ticker_bar(top_tickers_df)

    st.divider()

    cols = st.columns([1, 3])
    top_left_cell = cols[0].container(border=True)
    bottom_left_cell = cols[0].container(border=True, vertical_alignment="bottom")

    # SUBREDDIT SELECTION
    if "subreddits" not in st.session_state:
        st.session_state.subreddits = st.query_params.get("subreddits", "All").split(
            ","
        )

    # update query params when subreddits are changed
    def update_subreddits():
        if st.session_state.subreddits:
            st.query_params["subreddits"] = st.session_state.subreddits
        else:
            st.query_params.pop("subreddits", None)

    with bottom_left_cell:
        # Selecter box for subreddits
        subreddits = st.multiselect(
            "Subreddits",
            options=sorted(set(SUBREDDITS) | set(st.session_state.subreddits)),
            default=st.session_state.subreddits,
            placeholder="ALL",
            help="Select subreddits to filter by. If none are selected, data from all subreddits will be shown.",
            accept_new_options=False,
            on_change=update_subreddits,
        )

    # Ticker selection
    with bottom_left_cell:
        ticker = st.text_input(
            "Ticker",
            value=st.query_params.get("ticker", "").upper(),
            placeholder="Enter a ticker symbol (e.g. AAPL)",
        )

    # timeframe selection
    with bottom_left_cell:
        timeframe = st.pills(
            "Timeframe",
            options=list(timeframe_map.keys()),
            default="3 Days",
        )

        if not timeframe:
            st.warning("Please select a timeframe.")
            st.stop()

        # bucket option
        daily_bucket = False
        if timeframe_map[timeframe] in ["168h", "336h", "720h"]:
            daily_bucket = st.toggle(
                "Daily Buckets",
                help="Group data into daily buckets instead of hourly.",
                value=True,
            )

    # Add selections to session state
    st.session_state.ticker = ticker
    st.session_state.timeframe = timeframe
    st.session_state.subreddits = subreddits

    # -- DATA DISPLAY --
    right_cell = cols[1].container(border=True, height="stretch")

    def retrieve_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Retrieve data using client function.

        Uses the ticker, subreddits, and timeframe selected by the user to fetch data from the database.

        Returns:
            tuple[delta_data, mention_data, price_data]: A tuple containing the delta data(before the timeframe) mention data and price data dataframes.
        """
        if ticker:
            with st.spinner("Fetching data..."):
                hours = int((timeframe_map[timeframe][:-1]))

                data = get_mention_data_1h(
                    ticker.upper(),
                    subreddits=tuple(subreddits) if subreddits else None,
                    hours=hours * 2,
                )

                middle_time = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)

                delta_data = data[data["timestamp"] < middle_time.isoformat()]
                data = data[data["timestamp"] >= middle_time.isoformat()]

                price_data = get_price_data_1h(
                    ticker.upper(), hours=int(timeframe_map[timeframe][:-1])
                )

                if not data.empty:
                    return delta_data, data, price_data
                else:
                    st.warning("No data found for the specified ticker and timeframe.")
                    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        else:
            st.info("Please enter a ticker symbol to display data.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Get data
    delta_df, df, price_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    try:
        delta_df, df, price_df = retrieve_data()
    except Exception as e:
        st.error(f"An error occurred while fetching data: {e}")

    with right_cell:
        if df.empty:
            st.warning(
                "No data to display. Please enter a ticker symbol and select a timeframe."
            )
            st.stop()  # stops here - check not needed anywhere lower

        # save raw copies of dataframes - used for return
        df_raw = df.copy()
        price_df_raw = price_df.copy()

        sentiment_df = aggregate_sentiment_to_timestamp(df_raw, weighted=True)
        sentiment_df = sentiment_df.rename(
            columns={"weighted_sentiment": "avg_sentiment"}
        )

        if not price_df.empty:
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                row_heights=[0.7, 0.3],
                specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
            )

            if daily_bucket:
                price_df = price_df.sort_values("timestamp")

                price_df["timestamp"] = pd.to_datetime(price_df["timestamp"]).dt.floor(
                    "D"
                )
                price_df = (
                    price_df.groupby("timestamp")
                    .agg(close=("close", "last"))
                    .reset_index()
                )

            # price trace
            fig.add_trace(
                go.Scatter(x=price_df["timestamp"], y=price_df["close"], name="Close"),
                row=1,
                col=1,
            )
            bar_row, bar_col = 2, 1
        else:
            fig = go.Figure()
            st.caption("Price data not available for this ticker and timeframe.")
            bar_row, bar_col = None, None
            sentiment_df = None

        kwargs = {"row": bar_row, "col": bar_col} if bar_row else {}

        # logic continues with or without price data
        if daily_bucket:
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.floor("D")
            df = (
                df.groupby(["timestamp", "subreddit"])
                .agg(
                    mention_count=("mention_count", "sum"),
                    unique_users=("unique_users", "sum"),
                    avg_sentiment=("avg_sentiment", "mean"),
                )
                .reset_index()
            )

            # now adjust sentiment df
            sentiment_df["timestamp"] = pd.to_datetime(
                sentiment_df["timestamp"]
            ).dt.floor("D")
            sentiment_df = (
                df.groupby("timestamp")
                .agg(avg_sentiment=("avg_sentiment", "mean"))
                .reset_index()
            )

        # sentiment line
        if sentiment_df is not None and not sentiment_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=sentiment_df["timestamp"],
                    y=sentiment_df["avg_sentiment"],
                    name="Sentiment",
                    yaxis="y2",
                ),
            )
            fig.update_yaxes(range=[-1, 1], secondary_y=True, row=1, col=1)

        df["colour"] = df["avg_sentiment"].apply(sentiment_to_colour)

        # Choose bar colours based on subreddit if multiple subreddits are present, otherwise use sentiment colours
        if len(df["subreddit"].unique()) > 1:
            colour_map = {
                sub: px.colors.qualitative.Plotly[i]
                for i, sub in enumerate(df["subreddit"].unique())
            }
            for sub, group in df.groupby("subreddit"):
                fig.add_trace(
                    go.Bar(
                        x=group["timestamp"],
                        y=group["mention_count"],
                        name=sub,
                        marker_color=colour_map[sub],
                    ),
                    **kwargs,
                )
        else:
            fig.add_trace(
                go.Bar(
                    x=df["timestamp"],
                    y=df["mention_count"],
                    name="Mentions(colour by sentiment)",
                ),
                **kwargs,
            )
            fig.update_traces(marker_color=df["colour"])

        total_mentions = df["mention_count"].sum()
        unique_users = df["unique_users"].mean()
        avg_sentiment = df["avg_sentiment"].mean()

        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Total Mentions**  \n{total_mentions:,}")
        col2.markdown(f"**Average Users per Time Bucket**  \n{unique_users:.0f}")
        col3.markdown(f"**Avg Sentiment**  \n{avg_sentiment:.2f}")

        if len(df["subreddit"].unique()) > 1:
            st.caption("💡 Select a single subreddit to colour bars by sentiment")

        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))

        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Mentions: %{y}<br>Sentiment: %{customdata[0]:.2f}"
        )

        fig.update_layout(
            legend=dict(
                orientation="h",
                y=1.02,  # just above the plot area
                x=0.0,  # left aligned
                xanchor="left",
                yanchor="bottom",
            ),
            barmode="stack",
        )

        # table view
        table_df = df[
            ["timestamp", "subreddit", "mention_count", "avg_sentiment"]
        ].copy()
        table_df["timestamp"] = pd.to_datetime(table_df["timestamp"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # tabs
        tab_chart, tab_table = st.tabs(["Chart View", "Table View"])

        with tab_chart:
            st.plotly_chart(fig, width="stretch")
        with tab_table:
            st.dataframe(table_df, width="stretch")

    with top_left_cell:
        # pie not needed if only one subreddit present
        if len(df["subreddit"].unique()) > 1:
            pie_df = (
                df.groupby("subreddit")
                .agg(mention_count=("mention_count", "sum"))
                .reset_index()
            )

            pie_fig = px.pie(
                pie_df,
                names="subreddit",
                values="mention_count",
                color="subreddit",
                color_discrete_map=colour_map,  # only available with >1 subreddits
            )
            pie_fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), showlegend=False, height=200
            )

            st.plotly_chart(pie_fig, width="stretch")

        current_mentions = df_raw["mention_count"].sum()
        previous_mentions = delta_df["mention_count"].sum()
        delta_mentions = current_mentions - previous_mentions

        st.metric(
            label="Total Mentions",
            value=f"{current_mentions:,}",
            delta=f"{delta_mentions:,}",
        )

    # Finishing code
    return df_raw, price_df_raw
