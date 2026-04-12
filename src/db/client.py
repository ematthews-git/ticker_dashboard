from supabase import create_client
from dotenv import load_dotenv
import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)


# Cache output for 1 hour due to database updating hourly.
@st.cache_data(ttl=3600)
def fetch_mention_data(
    ticker: str, subreddits: list = None, hours: int = 12
) -> pd.DataFrame:
    """Fetch all columns from mentions table for specified ticker and timeframe.

    Args:
        ticker (str): The ticker to be searched for.
        subreddits (list, optional): List of subreddits to filter by. Defaults to None (no filtering).
        hours (int, optional): How many hours to lookback. Supabase inposes limit of 1000 items. Defaults to 12 hours.

    Returns:
        Pandas Dataframe: The data in the form of a dataframe.
    """
    end_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    response = (
        supabase.table("mentions")
        .select("*")
        .eq("ticker", ticker)
        .gte("timestamp", end_time)
        .order("timestamp", desc=True)
        .execute()
    )

    data = pd.DataFrame(response.data)

    if subreddits:
        if "All" in subreddits:
            return data
        subreddits = [s[2:] if s.startswith("r/") else s for s in subreddits]
        data = data[data["subreddit"].isin(subreddits)]

    return data


@st.cache_data(ttl=3600)
def fetch_price_data(ticker: str, hours: int = 12) -> pd.DataFrame:
    """Fetch price data for the specified ticker and timeframe.

    Args:
        ticker (str): The ticker to be searched for.
        hours (int, optional): How many hours to lookback. Defaults to 12 hours.

    Returns:
        pd.DataFrame: Dataframe containing price data with columns 'timestamp' and 'price'.
    """
    end_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    response = (
        supabase.table("stock_prices")
        .select("*")
        .eq("ticker", ticker)
        .gte("timestamp", end_time)
        .order("timestamp", desc=True)
        .execute()
    )

    price_data = pd.DataFrame(response.data)

    return price_data
