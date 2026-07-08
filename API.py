import streamlit as st

st.write("🔥 NEUE API.PY GELADEN")import requests
import streamlit as st
from datetime import datetime
import pytz


BASE_URL = "https://v3.football.api-sports.io"


def get_headers():
    return {
        "x-apisports-key": st.secrets["API_KEY"]
    }


def get_today_matches():

    # Deutsche Zeitzone
    germany = pytz.timezone("Europe/Berlin")
    today = datetime.now(germany).strftime("%Y-%m-%d")


    url = f"{BASE_URL}/fixtures"


    params = {
        "date": today,
        "timezone": "Europe/Berlin"
    }


    response = requests.get(
        url,
        headers=get_headers(),
        params=params
    )


    data = response.json()
st.write(data)

    matches = []


    for game in data.get("response", []):

        fixture = game["fixture"]
        teams = game["teams"]
        league = game["league"]


        matches.append({

            "id": fixture["id"],

            "date":
            fixture["date"],

            "league":
            league["name"],

            "country":
            league["country"],

            "home":
            teams["home"]["name"],

            "away":
            teams["away"]["name"]

        })


    return matches
