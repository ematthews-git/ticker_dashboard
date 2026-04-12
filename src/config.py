import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

SUBREDDITS = [
    "r/pennystocks",
    "r/WallStreetBets",
    "r/SmallStreetBets",
    "r/Daytrading",
    "r/ShortSqueeze",
    "r/10xpennystocks",
]

timeframe_map = {
    "1 Hour": "1h",
    "6 Hours": "6h",
    "12 Hours": "12h",
    "24 Hours": "24h",
    "3 Days": "72h",
    "7 Days": "168h",
}
