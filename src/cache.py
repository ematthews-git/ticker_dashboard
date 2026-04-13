"""Cache wrappers utilising client.py.

Placed here for readability and cleanliness.
"""

import db.client as client
import streamlit as st
import pandas as pd


# Cache output for 1 hour due to database updating hourly.
@st.cache_data(ttl=3600)
def get_mention_data_1h(
    ticker: str, subreddits: list = None, hours: int = 12
) -> pd.DataFrame:
    """Cache wrapper for fetch_mention_data.

    Args:
        ticker (str): The ticker to be searched for.
        subreddits (list, optional): List of subreddits to filter by. Defaults to None (no filtering).
        hours (int, optional): How many hours to lookback. Supabase inposes limit of 1000 items. Defaults to 12 hours.

    Returns:
        pd.DataFrame: The data in the form of a cached dataframe.
    """
    return client.fetch_mention_data(ticker, subreddits=subreddits, hours=hours)


# Cache output for 1 hour due to database updating hourly.
@st.cache_data(ttl=3600)
def get_price_data_1h(ticker: str, hours: int = 12) -> pd.DataFrame:
    """Cache wrapper for fetch_price_data.

    Args:
        ticker (str): The ticker to be searched for.
        hours (int, optional): How many hours to lookback. Defaults to 12 hours.

    Returns:
        pd.DataFrame: Dataframe containing price data with columns 'timestamp' and 'price'.
    """
    return client.fetch_price_data(ticker, hours=hours)


# Cache output for 12 hours to act as top daily tickers
@st.cache_data(ttl=43200)
def get_top_tickers_12h(hours: int = 12) -> pd.DataFrame:
    """Fetch top tickers in the last 12 hours.

    Args:
        hours (int, optional): How many hours to lookback. Defaults to 12 hours.
    returns:
        pd.DataFrame: Dataframe containing top tickers with columns 'ticker' and 'mention_count'.
    """
    return client.fetch_top_tickers(hours=hours)


@st.cache_data(ttl=3600)
def get_top_tickers_1h(hours: int = 12) -> pd.DataFrame:
    """Fetch top tickers for given timeframe and caches for 1 hour.

    Args:
        hours (int, optional): How many hours to lookback. Defaults to 12 hours.
    returns:
        pd.DataFrame: Dataframe containing top tickers with columns 'ticker' and 'mention_count'.
    """
    return client.fetch_top_tickers(hours=hours)
