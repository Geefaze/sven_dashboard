import streamlit as st
import requests
from datetime import datetime
import pandas as pd


# ==========================
# EINSTELLUNGEN
# ==========================

st.set_page_config(
    page_title="Sven AI Betting Cockpit",
    page_icon="⚽",
    layout="wide"
)


API_URL = "https://v3.football.api-sports.io"


# ==========================
# PASSWORT
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
# API ABFRAGE
# ==========================

@st.cache_data(ttl=1800)
def get_matches():


    today = datetime.now().strftime("%Y-%m-%d")


    headers = {

        "x-apisports-key":
        st.secrets["API_KEY"]

    }


    params = {

        "date": today,

        "timezone":
        "Europe/Berlin"

    }


    response = requests.get(

        f"{API_URL}/fixtures",

        headers=headers,

        params=params

    )


    return response.json()



# ==========================
# START
# ==========================


st.title(
    "⚽ Sven's AI Betting Cockpit"
)


st.subheader(
    "📅 Tagesaktueller Match Scanner"
)



try:

    data = get_matches()


except Exception as e:

    st.error(
        f"API Fehler: {e}"
    )

    st.stop()



# ==========================
# DEBUG
# ==========================


with st.expander(
    "🔧 API Diagnose"
):

    st.write(data)



# ==========================
# SPIELE AUSLESEN
# ==========================


matches = []


for game in data.get("response", []):


    matches.append({

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



if len(matches) == 0:


    st.warning(
        "⚠️ Keine Spiele gefunden"
    )


    st.info(
        "Öffne oben 'API Diagnose' und prüfe die Antwort."
    )


    st.stop()



# ==========================
# AUSGABE
# ==========================


st.success(
    f"{len(matches)} Spiele gefunden"
)


df = pd.DataFrame(matches)


st.dataframe(
    df,
    use_container_width=True
)



# ==========================
# SPIELAUSWAHL
# ==========================


st.divider()


auswahl = st.selectbox(

    "⚽ Spiel auswählen",

    [

        f"{x['Heim']} - {x['Auswärts']}"

        for x in matches

    ]

)



st.success(
    f"Ausgewählt: {auswahl}"
)


st.info(
    "Nächster Schritt: Quoten, 8-Säulen-Analyse und AI Edge Score."
)
