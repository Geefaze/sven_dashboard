import streamlit as st
import requests
import pandas as pd
from datetime import datetime


# ==========================
# SETUP
# ==========================

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

    if st.button("Anmelden"):

        if password == "Sven2026":
            st.session_state.password_correct = True
            st.rerun()

        else:
            st.error("Falsches Passwort")

    st.stop()



# ==========================
# API FUNKTION
# ==========================

@st.cache_data(ttl=1800)
def api_call(endpoint, params):

    headers = {
        "x-apisports-key":
        st.secrets["API_KEY"]
    }


    response = requests.get(
        f"{API_URL}/{endpoint}",
        headers=headers,
        params=params
    )


    return response.json()



# ==========================
# SPIELE HEUTE
# ==========================

@st.cache_data(ttl=1800)
def get_today_matches():

    today = datetime.now().strftime("%Y-%m-%d")


    data = api_call(
        "fixtures",
        {
            "date": today,
            "timezone": "Europe/Berlin"
        }
    )


    matches=[]


    for game in data.get("response", []):

        matches.append({

            "id":
            game["fixture"]["id"],

            "Heim":
            game["teams"]["home"]["name"],

            "Auswärts":
            game["teams"]["away"]["name"],

            "Liga":
            game["league"]["name"],

            "Land":
            game["league"]["country"],

            "home_id":
            game["teams"]["home"]["id"],

            "away_id":
            game["teams"]["away"]["id"]

        })


    return matches



# ==========================
# AI EDGE ENGINE
# ==========================


def calculate_edge_score():

    # Grundgerüst
    # später automatische API-Werte


    form = 10
    home_away = 10
    h2h = 5
    squad = 8
    motivation = 5
    tactics = 5
    history = 3
    value = 5


    total = (
        form +
        home_away +
        h2h +
        squad +
        motivation +
        tactics +
        history +
        value
    )


    return {

        "Gesamt": total,

        "Form": form,

        "Heim/Auswärts": home_away,

        "H2H": h2h,

        "Kader": squad,

        "Motivation": motivation,

        "Taktik": tactics,

        "Historie": history,

        "Value": value

    }



# ==========================
# APP
# ==========================


st.title(
    "⚽ Sven's AI Betting Cockpit"
)


st.subheader(
    "📅 Tagesaktueller Match Scanner"
)



matches = get_today_matches()



if not matches:

    st.warning(
        "Keine Spiele gefunden"
    )

    st.stop()



df = pd.DataFrame(matches)



st.success(
    f"{len(df)} Spiele geladen"
)



# Filter

liga = st.selectbox(
    "Liga:",
    ["Alle"] +
    sorted(df["Liga"].unique())
)


if liga != "Alle":

    df = df[
        df["Liga"] == liga
    ]



auswahl = st.selectbox(

    "⚽ Spiel auswählen",

    [
        f"{x['Heim']} - {x['Auswärts']}"

        for _,x in df.iterrows()

    ]

)



spiel = df.iloc[
    [
        f"{x['Heim']} - {x['Auswärts']}"
        for _,x in df.iterrows()
    ].index(auswahl)
]



st.divider()



st.header(
    f"{spiel['Heim']} 🆚 {spiel['Auswärts']}"
)



st.write(
    f"Liga: {spiel['Liga']}"
)



# ==========================
# SCORE
# ==========================


score = calculate_edge_score()



st.divider()


st.subheader(
    "🤖 AI Edge Score"
)


st.metric(
    "Gesamtbewertung",
    f"{score['Gesamt']}/100"
)



score_df = pd.DataFrame(
    score.items(),
    columns=[
        "Bereich",
        "Punkte"
    ]
)


st.table(score_df)



if score["Gesamt"] >= 75:

    st.success(
        "🟢 Starkes Analyseprofil"
    )

elif score["Gesamt"] >= 60:

    st.info(
        "🟡 Interessantes Spiel"
    )

else:

    st.warning(
        "🔴 Kein starkes Signal"
    )



st.caption(
    "Version 2.0 - AI Edge Framework aktiv"
)
