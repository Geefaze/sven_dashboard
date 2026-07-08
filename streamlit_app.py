import streamlit as st
import requests
from datetime import datetime


st.set_page_config(
    page_title="API Football Test",
    page_icon="⚽"
)


st.title("⚽ Sven AI Betting Cockpit - API Test")


API_URL = "https://v3.football.api-sports.io"


def test_api():

    headers = {
        "x-apisports-key": st.secrets["API_KEY"]
    }


    params = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }


    response = requests.get(
        f"{API_URL}/fixtures",
        headers=headers,
        params=params
    )


    return response.status_code, response.json()



try:

    status, data = test_api()


    st.success(
        f"HTTP Status: {status}"
    )


    st.subheader("API Antwort")


    st.json(data)


except Exception as e:

    st.error(
        str(e)
    )
