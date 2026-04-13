import streamlit as st
import pandas as pd
import plotly.express as px
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


def render_ticker_bar(top_tickers: pd.DataFrame) -> None:
    """Render a bar across the top of the page featuring the top tickers daily.

    Args:
        top_tickers (pd.DataFrame): Dataframe containing top tickers with columns 'ticker' and 'mention_count'.
    """
    st.markdown("#### Top Daily Tickers")

    cols = st.columns(len(top_tickers))
    for col, row in zip(cols, top_tickers.itertuples()):
        col.markdown(f"**{row.ticker}**  \n{row.mention_count:,} mentions")


render_ticker_bar(get_top_tickers_12h())

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
    border=True, height="stretch", vertical_alignment="center"
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

# DATA DISPLAY
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
                subreddits=subreddits,
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
    # supress error when trying to apply colour mapping to empty dataframe
    if not df.empty:
        df["colour"] = df["avg_sentiment"].apply(sentiment_to_colour)
except Exception as e:
    st.error(f"An error occurred while fetching data: {e}")

# -- Display data --
with right_cell:
    if not df.empty:
        if not price_df.empty:
            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3]
            )

            fig.add_trace(
                go.Scatter(x=price_df["timestamp"], y=price_df["close"], name="Close"),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Bar(
                    x=df["timestamp"],
                    y=df["mention_count"],
                    name="Mentions(colour by sentiment)",
                ),
                row=2,
                col=1,
            )

            # Chose bar colours based on subreddit if multiple subreddits are present, otherwise use sentiment colours
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
                        row=2,
                        col=1,
                    )
            else:
                fig.update_traces(marker_color=df["colour"])

        total_mentions = df["mention_count"].sum()
        unique_users = df["unique_users"].max()
        avg_sentiment = df["avg_sentiment"].mean()

        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Total Mentions**  \n{total_mentions:,}")
        col2.markdown(f"**Unique Users**  \n{unique_users:,}")
        col3.markdown(f"**Avg Sentiment**  \n{avg_sentiment:.2f}")

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

# NEXT SECTION - see list of top tickers

st.header("Most popular tickers")

cols = st.columns([1, 2])

left_cell = cols[0].container(border=True, height="stretch")

with left_cell:
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
