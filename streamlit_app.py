import streamlit as st
import requests
import pandas as pd
from datetime import datetime


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

    pw = st.text_input(
        "Passwort:",
        type="password"
    )

    if st.button("Anmelden"):

        if pw == "Sven2026":
            st.session_state.password_correct = True
            st.rerun()

        else:
            st.error("Falsches Passwort")

    st.stop()



# ==========================
# API
# ==========================


def api_get(endpoint, params):

    headers = {
        "x-apisports-key": st.secrets["API_KEY"]
    }


    r = requests.get(
        f"{API_URL}/{endpoint}",
        headers=headers,
        params=params
    )


    return r.json()



# ==========================
# SPIELE
# ==========================


@st.cache_data(ttl=1800)
def get_today_games():

    today = datetime.now().strftime("%Y-%m-%d")


    data = api_get(
        "fixtures",
        {
            "date": today,
            "timezone": "Europe/Berlin"
        }
    )


    games=[]


    for g in data.get("response", []):

        games.append({

            "Heim":
            g["teams"]["home"]["name"],

            "Auswärts":
            g["teams"]["away"]["name"],

            "home_id":
            g["teams"]["home"]["id"],

            "away_id":
            g["teams"]["away"]["id"],

            "Liga":
            g["league"]["name"],

            "Zeit":
            g["fixture"]["date"]

        })


    return games



# ==========================
# FORM
# ==========================


@st.cache_data(ttl=3600)
def get_team_form(team_id):


    data = api_get(

        "fixtures",

        {
            "team": team_id,
            "last": 5
        }

    )


    spiele = []


    for g in data.get("response", []):


        home = g["teams"]["home"]

        away = g["teams"]["away"]

        tore_home = g["goals"]["home"]

        tore_away = g["goals"]["away"]


        if tore_home is None:
            continue


        if home["id"] == team_id:

            tore_fuer = tore_home
            tore_gegen = tore_away

            sieg = home["winner"]


        else:

            tore_fuer = tore_away
            tore_gegen = tore_home

            sieg = away["winner"]



        spiele.append({

            "Tore": tore_fuer,

            "Gegentore":
            tore_gegen,

            "Sieg":
            sieg

        })


    return spiele



def form_score(form):

    if not form:
        return 5


    punkte = 0


    for spiel in form:

        if spiel["Sieg"]:
            punkte += 3

        elif spiel["Sieg"] is None:
            punkte += 1


    return min(
        round(punkte / 15 * 20),
        20
    )



# ==========================
# AI EDGE
# ==========================


def calculate_edge(home_form, away_form):


    heim = form_score(home_form)

    auswaerts = form_score(away_form)


    gesamt = round(
        40 +
        (heim * 1.5) +
        (auswaerts * 1.2)
    )


    return min(
        gesamt,
        100
    )



# ==========================
# APP
# ==========================


st.title(
    "⚽ Sven's AI Betting Cockpit"
)


st.subheader(
    "📅 Tagesaktueller Match Scanner"
)



games = get_today_games()



if not games:

    st.warning(
        "Keine Spiele gefunden"
    )

    st.stop()



df = pd.DataFrame(games)



st.success(
    f"{len(df)} Spiele geladen"
)



choice = st.selectbox(

    "Spiel auswählen",

    [
        f"{x['Heim']} - {x['Auswärts']}"

        for _,x in df.iterrows()

    ]

)



index = [
    f"{x['Heim']} - {x['Auswärts']}"

    for _,x in df.iterrows()

].index(choice)



match = games[index]



st.divider()


st.header(
    f"{match['Heim']} 🆚 {match['Auswärts']}"
)



# FORM LADEN


with st.spinner(
    "Analysiere Form..."
):

    home_form = get_team_form(
        match["home_id"]
    )

    away_form = get_team_form(
        match["away_id"]
    )



score = calculate_edge(
    home_form,
    away_form
)



st.subheader(
    "🤖 AI Edge Score"
)


st.metric(
    "Gesamt",
    f"{score}/100"
)



c1,c2 = st.columns(2)


with c1:

    st.write(
        "🏠 Heim letzte Spiele"
    )

    st.dataframe(
        pd.DataFrame(home_form)
    )


with c2:

    st.write(
        "✈️ Auswärts letzte Spiele"
    )

    st.dataframe(
        pd.DataFrame(away_form)
    )



if score >= 75:

    st.success(
        "🟢 Starkes Signal"
    )

elif score >= 60:

    st.info(
        "🟡 Beobachten"
    )

else:

    st.warning(
        "🔴 Kein klares Signal"
    )


st.caption(
    "Version 2.1 - Form Engine aktiv"
)
