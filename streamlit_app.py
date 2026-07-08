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
# API
# ==========================


@st.cache_data(ttl=1800)
def get_matches():


    today = datetime.now().strftime("%Y-%m-%d")


    headers = {

        "x-apisports-key":
        st.secrets["API_KEY"]

    }


    params = {

        "date":
        today,

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
# DATEN LADEN
# ==========================


st.title(
    "⚽ Sven's AI Betting Cockpit"
)


st.subheader(
    "📅 Tagesaktueller Match Scanner"
)



data = get_matches()



# ==========================
# LIGEN FILTER
# ==========================


wichtige_ligen = [

    "UEFA Champions League",

    "UEFA Europa League",

    "UEFA Europa Conference League",

    "Bundesliga",

    "2. Bundesliga",

    "Premier League",

    "Championship",

    "La Liga",

    "Serie A",

    "Ligue 1",

    "Eredivisie",

    "Liga Portugal",

    "Belgian Pro League",

    "Super Lig",

    "Major League Soccer",

    "Brasileirão Série A",

    "Liga Profesional Argentina",

    "Eliteserien",

    "Allsvenskan"

]



matches = []


for game in data.get("response", []):


    liga = game["league"]["name"]


    if liga in wichtige_ligen:


        matches.append({

            "Liga":
            liga,


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
# AUSGABE
# ==========================


if not matches:

    st.warning(
        "Keine Spiele in den ausgewählten Ligen gefunden."
    )

    st.info(
        "Heute sind möglicherweise nur kleinere Ligen aktiv."
    )

    st.stop()



st.success(
    f"{len(matches)} relevante Spiele gefunden"
)



df = pd.DataFrame(matches)



# Suche

suche = st.text_input(
    "🔎 Team oder Liga suchen:"
)


if suche:

    df = df[
        df.astype(str)
        .apply(
            lambda x:
            x.str.contains(
                suche,
                case=False
            )
        )
        .any(axis=1)
    ]



st.dataframe(
    df,
    use_container_width=True
)



# ==========================
# SPIEL AUSWAHL
# ==========================


spiele = [

    f"{row['Heim']} - {row['Auswärts']} ({row['Liga']})"

    for _,row in df.iterrows()

]


auswahl = st.selectbox(
    "⚽ Spiel auswählen:",
    spiele
)



spiel = df.iloc[
    spiele.index(auswahl)
]



st.divider()


st.subheader(
    "🎯 Analyse Vorbereitung"
)



c1,c2,c3 = st.columns(3)


with c1:

    st.metric(
        "Heim",
        spiel["Heim"]
    )


with c2:

    st.metric(
        "Auswärts",
        spiel["Auswärts"]
    )


with c3:

    st.metric(
        "Liga",
        spiel["Liga"]
    )



st.info(
    f"""
    Spielzeit:
    {spiel['Zeit']}
    
    Land:
    {spiel['Land']}
    """
)



# ==========================
# NÄCHSTER SCHRITT
# ==========================


st.divider()


st.subheader(
    "🤖 AI Edge Score"
)


st.metric(
    "Score",
    "Wird berechnet..."
)


st.caption(
    "Nächster Ausbau: Form, H2H, Quoten, xG, Kader, Motivation und Value."
)
