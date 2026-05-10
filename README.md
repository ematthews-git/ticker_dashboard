# Ticker Mentions Dashboard

A Streamlit dashboard that tracks how often stock tickers are mentioned across Reddit. Includes sentiment scoring, price overlays and correlation charts.

## Features

- **Top daily tickers** — quick-select pills showing the most-mentioned tickers in the last 12 hours
- **Mention + price chart** — stacked bar chart of mentions per subreddit, overlaid with sentiment and close price
- **Mention trends** — hour-over-hour deltas, rolling average momentum, and cumulative mention count
- **Activity heatmap** — mentions broken down by day-of-week and hour-of-day (UTC)
- **Correlation charts** — scatter plots comparing sentiment/mention volume against price change
- **Filters** — subreddit multiselect, timeframe (12 h → 30 d), and optional daily bucketing
- **Shareable URLs** — ticker and subreddit selection are reflected in query params

**Subreddits tracked:** r/wallstreetbets, r/pennystocks, r/SmallStreetBets, r/Daytrading, r/ShortSqueeze, r/10xpennystocks

## Stack

- [Streamlit](https://streamlit.io/) — UI
- [Supabase](https://supabase.com/) — database (mention counts, sentiment scores, price data)
- [Plotly](https://plotly.com/python/) — charts
- [pandas](https://pandas.pydata.org/) / [statsmodels](https://www.statsmodels.org/) — data processing

## Local setup

This app uses a private database. Contact me for more information.

## Data disclaimer

This is a side project. Data accuracy is not guaranteed. Notable caveats:

- Data before May 2025 did not capture lowercase ticker mentions
- A significant methodology change to sentiment scoring was rolled out in late April 2025
- WSB post coverage may have gaps due to post volume; smaller subreddits have more complete coverage

Reddit buzz is **not** a reliable predictor of stock price. Check the correlation charts.
