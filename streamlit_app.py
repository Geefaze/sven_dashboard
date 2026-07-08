import streamlit as st
import requests
from datetime import datetime
import pandas as pd


# =========================
# KONFIGURATION
# =========================

st.set_page_config(
    page_title="Sven AI Betting Cockpit",
    page_icon="⚽",
    layout="wide"
)


API_URL = "https://v3.football.api-sports.io"


# =========================
# PASSWORT
# =========================

if "password_correct" not in st.session_state:
    st.session_state.password_correct = False


if not st.session_state.password_correct:

    st.title("🔒 Sven's AI Betting Cockpit")

    password = st.text_input(
        "Passwort eingeben:",
        type="password"
    )

    if st.button("Anmelden"):

        if password == "Sven2026":
            st.session_state.password_correct = True
            st.rerun()

        else:
            st.error("Falsches Passwort")

    st.stop()


# =========================
# API FUNKTION
# =========================

@st.cache_data(ttl=1800)
def get_today_matches():

    today = datetime.now().strftime("%Y-%m-%d")


    headers = {
        "x-apisports-key": st.secrets["API_KEY"]
    }


    params = {
        "date": today,
        "timezone": "Europe/Berlin"
    }


    response = requests.get(
        f"{API_URL}/fixtures",
        headers=headers,
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

            "country":
            game["league"]["country"],

            "home":
            game["teams"]["home"]["name"],

            "away":
            game["teams"]["away"]["name"],

            "time":
            game["fixture"]["date"]

        })


    return matches



# =========================
# HAUPTSEITE
# =========================


st.title("⚽ Sven's AI Betting Cockpit")


st.caption(
    "Version 1.0 - Automatischer Tages Match Scanner"
)



# =========================
# SPIELE LADEN
# =========================


st.header("📅 Tagesaktuelle Spiele")


try:

    matches = get_today_matches()


except Exception as e:

    st.error(
        f"API Fehler: {e}"
    )

    st.stop()



if len(matches) == 0:

    st.warning(
        "Keine Spiele gefunden"
    )

    st.stop()



st.success(
    f"{len(matches)} Spiele heute gefunden"
)



# =========================
# FILTER
# =========================


df = pd.DataFrame(matches)


ligen = [
    "Alle"
] + sorted(
    df["league"].unique().tolist()
)


liga = st.selectbox(
    "Liga filtern:",
    ligen
)



if liga != "Alle":

    df = df[
        df["league"] == liga
    ]



# =========================
# SPIELAUSWAHL
# =========================


spiel_liste = []


for index,row in df.iterrows():

    spiel_liste.append(
        f"{row['home']} - {row['away']} | {row['league']}"
    )


auswahl = st.selectbox(
    "⚽ Spiel auswählen:",
    spiel_liste
)



spiel_index = spiel_liste.index(
    auswahl
)



match = df.iloc[
    spiel_index
]



# =========================
# AUSGEWÄHLTES SPIEL
# =========================


st.divider()


st.subheader(
    "🎯 Aktuelle Analyse"
)


col1,col2,col3 = st.columns(3)


with col1:

    st.metric(
        "Heimteam",
        match["home"]
    )


with col2:

    st.metric(
        "Auswärtsteam",
        match["away"]
    )


with col3:

    st.metric(
        "Liga",
        match["league"]
    )



st.info(
    f"""
    Spielzeit:
    {match['time']}
    
    Land:
    {match['country']}
    """
)



# =========================
# PLATZHALTER AI EDGE
# =========================


st.divider()


st.subheader(
    "🤖 AI Edge Analyse"
)


edge_score = 0


st.metric(
    "AI Edge Score",
    f"{edge_score}/100"
)


st.warning(
    "Analysemodule werden in Version 2.0 aktiviert."
)
