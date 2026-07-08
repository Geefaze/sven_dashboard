import streamlit as st
import requests

st.title("Football-data.org Test")

r = requests.get(
    "https://api.football-data.org/v4/competitions",
    headers={
        "X-Auth-Token": st.secrets["API_KEY"]
    }
)

st.write("Status:", r.status_code)
st.json(r.json())
