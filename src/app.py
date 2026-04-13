import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from plotly.subplots import make_subplots
from plotly import graph_objects as go
from utils import configure_page, sentiment_to_colour
from config import SUBREDDITS, timeframe_map
from cache import (
    get_mention_data_1h,
    get_price_data_1h,
    get_top_tickers_12h,
    get_top_tickers_1h,
)


st.title("Ticker Mentions Dashboard")

configure_page()

## -- variables needed across multiple cells --
daily_bucket = False


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

# SUBREDDIT SELECTION
if "subreddits" not in st.session_state:
    st.session_state.subreddits = st.query_params.get("subreddits", "All").split(",")


# update query params when subreddits are changed
def update_subreddits():
    if st.session_state.subreddits:
        st.query_params["subreddits"] = st.session_state.subreddits
    else:
        st.query_params.pop("subreddits", None)


top_left_cell = cols[0].container(
    border=True, height="stretch", vertical_alignment="bottom"
)

with top_left_cell:
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
with top_left_cell:
    ticker = st.text_input(
        "Ticker",
        value=st.query_params.get("ticker", "").upper(),
        placeholder="Enter a ticker symbol (e.g. AAPL)",
    )


# timeframe selection
with top_left_cell:
    timeframe = st.pills(
        "Timeframe",
        options=list(timeframe_map.keys()),
        default="3 Days",
    )

    # bucket option
    daily_bucket = False
    if timeframe_map[timeframe] in ["168h", "336h", "720h"]:
        daily_bucket = st.toggle(
            "Daily Buckets",
            help="Group data into daily buckets instead of hourly.",
            value=True,
        )

# -- DATA DISPLAY --
right_cell = cols[1].container(border=True, height="stretch")


def retrieve_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retrieve data using client function.

    Uses the ticker, subreddits, and timeframe selected by the user to fetch data from the database.

    Returns:
        tuple[mention_data, price_data]: A tuple containing the mention data and price data dataframes.
    """
    if ticker:
        with st.spinner("Fetching data..."):
            data = get_mention_data_1h(
                ticker.upper(),
                subreddits=tuple(subreddits) if subreddits else None,
                hours=int(timeframe_map[timeframe][:-1]),
            )

            price_data = get_price_data_1h(
                ticker.upper(), hours=int(timeframe_map[timeframe][:-1])
            )

            if not data.empty:
                return data, price_data
            else:
                st.warning("No data found for the specified ticker and timeframe.")
                return pd.DataFrame(), pd.DataFrame()
    else:
        st.info("Please enter a ticker symbol to display data.")
        return pd.DataFrame(), pd.DataFrame()


# Get data
try:
    df, price_df = retrieve_data()

except Exception as e:
    st.error(f"An error occurred while fetching data: {e}")

# -- Display data --
with right_cell:
    if df.empty:
        st.warning(
            "No data to display. Please enter a ticker symbol and select a timeframe."
        )
        st.stop()

    if not price_df.empty:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])

        if daily_bucket:
            price_df = price_df.sort_values("timestamp")

            price_df["timestamp"] = pd.to_datetime(price_df["timestamp"]).dt.floor("D")
            price_df = (
                price_df.groupby("timestamp").agg(close=("close", "last")).reset_index()
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

    kwargs = {"row": bar_row, "col": bar_col} if bar_row else {}

    # logic continues with or without price data
    if daily_bucket:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.floor("D")
        df = (
            df.groupby(["timestamp", "subreddit"])
            .agg(
                mention_count=("mention_count", "sum"),
                unique_users=("unique_users", "max"),
                avg_sentiment=("avg_sentiment", "mean"),
            )
            .reset_index()
        )

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
    unique_users = df["unique_users"].max()
    avg_sentiment = df["avg_sentiment"].mean()

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"**Total Mentions**  \n{total_mentions:,}")
    col2.markdown(f"**Unique Users**  \n{unique_users:,}")
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
    table_df = df[["timestamp", "subreddit", "mention_count", "avg_sentiment"]].copy()
    table_df["timestamp"] = pd.to_datetime(table_df["timestamp"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # tabs
    tab_chart, tab_table = st.tabs(["Chart View", "Table View"])

    with tab_chart:
        st.plotly_chart(fig, width="stretch")
    with tab_table:
        st.dataframe(table_df, width="stretch")


# -----------------------------------------------
# NEXT ROW OF DISPLAY
# -----------------------------------------------

cols = st.columns([1, 1, 1])

left_cell = cols[0].container(border=True, height="stretch")
mid_cell = cols[1].container(border=True, height="content")
right_cell = cols[2].container(border=True, height="stretch")

# Create predictive and reactive correlation charts
# PREDICTIVE
if not ticker:
    st.info("Please enter a ticker symbol to display correlation data.")
else:
    sentiment_df = (
        df.groupby("timestamp")
        .agg(avg_sentiment=("avg_sentiment", "mean"))
        .reset_index()
        .sort_values("timestamp")
    )

    price_df_sorted = price_df.sort_values("timestamp")
    price_df_sorted["price_change"] = price_df_sorted["close"].pct_change().shift(-1)

    corr_df = pd.merge(
        sentiment_df,
        price_df_sorted[["timestamp", "price_change"]],
        on="timestamp",
        how="inner",
    ).dropna()

    fig_corr = px.scatter(
        corr_df,
        x="avg_sentiment",
        y="price_change",
        trendline="ols",
        labels={
            "avg_sentiment": "Sentiment",
            "price_change": "Next Period Price Change",
        },
        hover_data=["timestamp"],
    )
    fig_corr.update_layout(margin=dict(t=20, b=20, l=20, r=20))

    # REACTIVE
    corr_df_reactive = pd.merge(
        sentiment_df,
        price_df_sorted[["timestamp", "price_change"]],
        on="timestamp",
        how="inner",
    ).dropna()

    # Shift sentiment forward instead of price
    corr_df_reactive["next_sentiment"] = corr_df_reactive["avg_sentiment"].shift(-1)
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
        """
        ### Correlation Between Sentiment and Next Period Price Change
        """
        if daily_bucket:
            st.warning("Correlation may be less meaningful with daily buckets enabled.")

        st.plotly_chart(fig_corr, width="stretch")

    with mid_cell:
        """
        ### Correlation Between Sentiment and Previous Period Price Change (Reactivity)
        """

        if daily_bucket:
            st.warning("Correlation may be less meaningful with daily buckets enabled.")

        st.plotly_chart(fig_reactive, width="stretch")

    with right_cell:
        """
        ### Lag analysis + mention volume
        """

        # Should only go head where timestamp <= 14 days
        if timeframe_map[timeframe] not in ["336h", "720h"]:
            st.warning(
                "Lag analysis requires at least 14 days of data. Please select a longer timeframe to view this analysis."
            )
        else:
            LAGS = [1, 2, 4, 6, 12, 24]

            # aggregates per timestamp the weighted sentiment and total mention count
            sentiment_df = (
                df.groupby("timestamp")
                .apply(
                    lambda x: pd.Series(
                        {
                            "weighted_sentiment": np.average(
                                x["avg_sentiment"], weights=x["mention_count"]
                            ),
                            "mention_count": x["mention_count"].sum(),
                        }
                    )
                )
                .reset_index()
                .sort_values("timestamp")
            )

            price_df_sorted = price_df.sort_values("timestamp")
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

            fig_lag = px.bar(
                lag_df,
                x="lag",
                y="r",
                labels={"lag": "Lag (hours)", "r": "Correlation Coefficient"},
                title="Correlation Between Sentiment and Future Price Change at Different Lags",
            )
            fig_lag.add_hline(y=0, line_dash="dash", line_color="grey")
            fig_lag.update_layout(margin=dict(t=20, b=20, l=20, r=20))

            st.plotly_chart(fig_lag, width="stretch")


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
