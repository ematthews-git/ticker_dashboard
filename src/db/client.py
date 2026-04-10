from supabase import create_client
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime, timedelta, timezone

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

def fetch_mention_data(ticker: str, hours: int = 12):
    end_time = (datetime.now(timezone.utc) - timedelta(hours)).isoformat()

    response = supabase.table("mentions").select("*").eq("ticker", ticker) \
        .gte("timestamp", end_time).order("timestamp", desc=True).execute()
    
    return pd.DataFrame(response)
