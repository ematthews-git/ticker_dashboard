import streamlit as st
import pandas as pd
from db import client

df = pd.DataFrame(client.fetch_mention_data("AIXI"))

st.dataframe(df)

