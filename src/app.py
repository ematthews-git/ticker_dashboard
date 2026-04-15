"""App.py is the main entry point for the Streamlit application.

Different elements of the dashboard are organised into seperate components for readability and maintanability.
This module simply calls the different components in the correct order and passes necessary data between them.
"""

import streamlit as st
from utils import configure_page
from components.primary_row import render_primary_row
from components.correlation_charts import render_correlation_charts
from components.correlation_charts_mentions import render_corr_charts_mentions


st.title("Ticker Mentions Dashboard")

configure_page()

## -- variables needed across multiple cells --
daily_bucket = False

df_raw, price_df_raw = render_primary_row(daily_bucket=daily_bucket)

tab_correlation, tab_mentions = st.tabs(
    ["Correlation Between Sentiment+Mentions and Price Change", "not yet implemented"]
)

with tab_correlation:
    render_correlation_charts(df_raw, price_df_raw)
    render_corr_charts_mentions(df_raw, price_df_raw)
