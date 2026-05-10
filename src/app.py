"""App.py is the main entry point for the Streamlit application.

Different elements of the dashboard are organised into seperate components for readability and maintanability.
This module simply calls the different components in the correct order and passes necessary data between them.
"""

import streamlit as st
from utils import configure_page
from components.primary_row import render_primary_row
from components.correlation_charts import render_correlation_charts
from components.correlation_charts_mentions import render_corr_charts_mentions
from components.mention_charts import render_mention_trends, render_mention_heatmap

configure_page()
st.title("Ticker Mentions Dashboard")

## -- variables needed across multiple cells --
daily_bucket = False

df_raw, price_df_raw = render_primary_row(daily_bucket=daily_bucket)


tab_mentions, tab_correlation = st.tabs(
    ["Mention Trends", "Correlation Between Sentiment+Mentions and Price Change"]
)

with tab_mentions:
    render_mention_trends(df_raw)
    render_mention_heatmap(df_raw)

with tab_correlation:
    if len(price_df_raw) > 6:
        render_correlation_charts(df_raw, price_df_raw)
        render_corr_charts_mentions(df_raw, price_df_raw)
    else:
        st.warning("Requires at least one day of price data.")
