
import requests
import streamlit as st
from datetime import datetime


BASE_URL = "https://v3.football.api-sports.io"


def get_headers():

    return {
        "x-apisports-key": st.secrets["API_KEY"]
    }


def get_today_matches():

    today = datetime.now().strftime("%Y-%m-%d")

    url = f"{BASE_URL}/fixtures"

    params = {
        "date": today
    }

    response = requests.get(
        url,
        headers=get_headers(),
        params=params
    )

    data = response.json()

    matches = []

    for game in data.get("response", []):

        matches.append({

            "id":
            game["fixture"]["id"],

            "league":
            game["league"]["name"],

            "home":
            game["teams"]["home"]["name"],

            "away":
            game["teams"]["away"]["name"],

            "time":
            game["fixture"]["date"]

        })

    return matches
