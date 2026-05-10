import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

SUBREDDITS = [
    "r/pennystocks",
    "r/wallstreetbets",
    "r/SmallStreetBets",
    "r/Daytrading",
    "r/ShortSqueeze",
    "r/10xpennystocks",
]

timeframe_map = {
    "12 Hours": "12h",
    "24 Hours": "24h",
    "3 Days": "72h",
    "7 Days": "168h",
    "14 Days": "336h",
    "30 Days": "720h",
}
