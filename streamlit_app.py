import streamlit as st
import requests


st.title("⚽ Football-data.org Match Test")


data = requests.get(

    "https://api.football-data.org/v4/matches",

    headers={
        "X-Auth-Token": st.secrets["API_KEY"]
    }

)


st.write(
    "Status:",
    data.status_code
)


st.json(
    data.json()
)
