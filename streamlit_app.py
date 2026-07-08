import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd


st.set_page_config(
    page_title="Sven AI Betting Cockpit",
    page_icon="⚽",
    layout="wide"
)


API_URL = "https://v3.football.api-sports.io"


# ==========================
# LOGIN
# ==========================

if "password_correct" not in st.session_state:
    st.session_state.password_correct = False


if not st.session_state.password_correct:

    st.title("🔒 Sven's AI Betting Cockpit")

    password = st.text_input(
        "Passwort:",
        type="password"
    )

    if st.button("Login"):

        if password == "Sven2026":

            st.session_state.password_correct = True
            st.rerun()

        else:

            st.error("Falsches Passwort")

    st.stop()



# ==========================
# API
# ==========================

def api_request(date):

    headers = {
        "x-apisports-key": st.secrets["API_KEY"]
    }


    params = {

        "date": date,

        "timezone": "Europe/Berlin"

    }


    r = requests.get(
        f"{API_URL}/fixtures",
        headers=headers,
        params=params
    )


    return r.json()



# ==========================
# SCANNER
# ==========================


st.title(
    "⚽ Sven's AI Betting Cockpit"
)


st.subheader(
    "📅 Match Scanner"
)



today = datetime.now()


dates = []


for i in range(0,3):

    dates.append(
        (
            today + timedelta(days=i)
        ).strftime("%Y-%m-%d")
    )



all_matches = []


for date in dates:

    result = api_request(date)


    if "response" in result:

        for game in result["response"]:

            all_matches.append({

                "Datum": date,

                "Liga":
                game["league"]["name"],

                "Land":
                game["league"]["country"],

                "Heim":
                game["teams"]["home"]["name"],

                "Auswärts":
                game["teams"]["away"]["name"],

                "Zeit":
                game["fixture"]["date"]

            })



# ==========================
# DIAGNOSE
# ==========================


with st.expander("🔧 API Diagnose"):

    st.write(
        f"Abgefragte Tage: {dates}"
    )

    st.write(
        f"Gefundene Spiele: {len(all_matches)}"
    )



# ==========================
# AUSGABE
# ==========================


if len(all_matches) == 0:

    st.warning(
        "⚠️ Keine Spiele gefunden"
    )

    st.info(
        """
        Mögliche Ursachen:
        
        - API-Football Free Plan liefert keine Fixtures
        - API-Key ist nicht aktiv
        - Heute gibt es keine Spiele im verfügbaren Datenumfang
        """
    )

    st.stop()



st.success(
    f"{len(all_matches)} Spiele gefunden"
)



df = pd.DataFrame(all_matches)


st.dataframe(
    df,
    use_container_width=True
)



# ==========================
# AUSWAHL
# ==========================


spiel = st.selectbox(

    "⚽ Spiel auswählen",

    [
        f"{x['Heim']} - {x['Auswärts']}"

        for x in all_matches

    ]

)


st.success(
    f"Ausgewählt: {spiel}"
)
