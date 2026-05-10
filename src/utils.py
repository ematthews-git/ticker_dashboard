"""
Utils for the entire ticker_dashboard application.
"""

import streamlit as st
import numpy as np
import pandas as pd


def configure_page() -> None:
    """Configure page settings for the entire app."""
    st.set_page_config(
        page_title="Ticker Mentions Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.expander("Data Disclaimer"):
        st.markdown("""
            **IMPORTANT:** \
            This is a small side project. Data may be inaccurate in places.
            Also note, significant methodology changes have been made recently:
            Data before May did not include mentions that were written in lowercase.
            Getting strong post coverage has been an ongoing goal.
            Data before May may have a non-negligible count of missing posts(Especially WSB due to it's high volume;
                    other subreddits have much better coverage.).
            Additionally, a large improvement to sentiment scoring was rolled out late April.
            **PLEASE - look at the correlation charts. Reddit buzz is not a reliable predictor of stock price.**
        """)

    app_style = """
    <style>
    /*#MainMenu {visibility: visible;}*/
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(app_style, unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        .custom-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            text-align: center;
            padding: 10px;
            color: grey;
            font-size: 0.85rem;
            background: transparent;
            z-index: 9999;
        }
        .custom-footer a {
            color: #888;
            text-decoration: none;
        }
        .custom-footer a:hover {
            color: #ccc;
        }
        </style>
        <div class="custom-footer">
            Copyright &copy; 2026 Ethan M. &nbsp;|&nbsp;
            <a href="https://github.com/ematthews-git" target="_blank">GitHub</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sentiment_to_colour(sentiment: float) -> str:
    """Convert a sentiment score to a hex colour.

    Args:
        sentiment (float): Sentiment score to be converted. Must range from -1 to 1.

    Returns:
        str: The hex colour corresponding to the sentiment score.
    """
    negative_color = np.array([214, 39, 40])  # #d62728 red
    neutral_color = np.array([136, 136, 136])  # #888888 grey
    positive_color = np.array([44, 160, 44])  # #2ca02c green

    # Clamp to range
    sentiment = np.clip(sentiment, -1, 1)

    # Normalise to 0–1
    t = (sentiment - (-1)) / (1 - (-1))

    if t < 0.5:
        frac = t / 0.5  # 0 to 1 within the negative half
        rgb = (1 - frac) * negative_color + frac * neutral_color
    else:
        frac = (t - 0.5) / 0.5  # 0 to 1 within the positive half
        rgb = (1 - frac) * neutral_color + frac * positive_color

    r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
    return f"#{r:02x}{g:02x}{b:02x}"


def aggregate_sentiment_to_timestamp(
    df: pd.DataFrame, weighted: bool = True
) -> pd.DataFrame:
    """Aggregate sentiment scores to the timestamp level by calculating a weighted average sentiment for each timestamp.

    Args:
        df (pd.DataFrame): DataFrame containing 'timestamp', 'mention_count', and 'avg_sentiment' columns.
        weighted (bool): Whether to calculate a weighted average sentiment.

    Returns:
        pd.DataFrame: DataFrame with 'timestamp' and 'weighted_sentiment' columns.
    """
    if weighted:
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
    else:
        sentiment_df = (
            df.groupby("timestamp")
            .apply(lambda x: x["avg_sentiment"].mean())
            .reset_index()
            .sort_values("timestamp")
        )

    return sentiment_df
