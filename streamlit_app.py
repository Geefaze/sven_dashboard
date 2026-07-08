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

    st.title("🔒 Sven AI Betting Cockpit")

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


def api_get(endpoint, params):

    headers = {
        "x-apisports-key":
        st.secrets["API_KEY"]
    }


    try:

        response = requests.get(

            f"{API_URL}/{endpoint}",

            headers=headers,

            params=params,

            timeout=10

        )


        return response.json()


    except Exception:

        return {}



# ==========================
# SPIELE DES TAGES
# ==========================


@st.cache_data(ttl=900)
def get_games():


    today = datetime.now().strftime("%Y-%m-%d")


    data = api_get(

        "fixtures",

        {
            "date": today,
            "timezone": "Europe/Berlin"
        }

    )


    games=[]


    for item in data.get("response", []):


        games.append({

            "Heim":
            item["teams"]["home"]["name"],


            "Auswärts":
            item["teams"]["away"]["name"],


            "home_id":
            item["teams"]["home"]["id"],


            "away_id":
            item["teams"]["away"]["id"],


            "Liga":
            item["league"]["name"],


            "Land":
            item["league"]["country"]

        })


    return games



# ==========================
# START
# ==========================


st.title(
    "⚽ Sven AI Betting Cockpit"
)


st.subheader(
    "📅 Tagesaktueller Match Scanner"
)



games = get_games()



if not games:

    st.warning(
        "Keine Spiele gefunden"
    )

    st.stop()



st.success(
    f"{len(games)} Spiele geladen"
)



# ==========================
# LIGA FILTER
# ==========================


ligen = sorted(

    list(

        set(

            game["Liga"]

            for game in games

        )

    )

)



liga = st.selectbox(

    "🏆 Liga",

    ligen

)



liga_spiele = [

    game

    for game in games

    if game["Liga"] == liga

]



st.info(

    f"{len(liga_spiele)} Spiele in {liga}"

)



# ==========================
# SPIELAUSWAHL
# ==========================


spiele_namen = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in liga_spiele

]



auswahl = st.selectbox(

    "⚽ Spiel",

    spiele_namen

)



spiel_index = spiele_namen.index(
    auswahl
)



match = liga_spiele[spiel_index]



st.divider()



st.header(

    f"{match['Heim']} 🆚 {match['Auswärts']}"

)
# ==========================
# FORM DATEN
# ==========================


@st.cache_data(ttl=1800)
def get_last_games(team_id):

    data = api_get(
        "fixtures",
        {
            "team": team_id,
            "last": 5
        }
    )


    result = []


    for game in data.get("response", []):

        home = game["teams"]["home"]
        away = game["teams"]["away"]

        home_goals = game["goals"]["home"]
        away_goals = game["goals"]["away"]


        if home_goals is None or away_goals is None:
            continue


        if home["id"] == team_id:

            goals_for = home_goals
            goals_against = away_goals
            winner = home["winner"]


        else:

            goals_for = away_goals
            goals_against = home_goals
            winner = away["winner"]



        result.append({

            "Tore": goals_for,

            "Gegentore": goals_against,

            "Sieg": winner

        })


    return result



# ==========================
# H2H
# ==========================


@st.cache_data(ttl=3600)
def get_head_to_head(team1, team2):


    data = api_get(

        "fixtures/headtohead",

        {
            "h2h": f"{team1}-{team2}",
            "last": 5
        }

    )


    return data.get(
        "response",
        []
    )



# ==========================
# SCORE FUNKTIONEN
# ==========================


def calculate_form(points):

    if not points:
        return 10


    value = 0


    for match in points:


        if match["Sieg"] is True:

            value += 3


        elif match["Sieg"] is None:

            value += 1



    return min(
        20,
        round((value / 15) * 20)
    )



def calculate_attack(data):

    if not data:
        return 5


    goals = sum(
        x["Tore"]
        for x in data
    )


    conceded = sum(
        x["Gegentore"]
        for x in data
    )


    score = 5 + ((goals-conceded)/2)


    return max(
        0,
        min(
            10,
            round(score)
        )
    )



def calculate_h2h(data):

    if not data:
        return 5


    return min(
        10,
        5 + len(data)
    )



# ==========================
# DATEN LADEN
# ==========================


with st.spinner(
    "🤖 AI Analyse läuft..."
):

    home_form = get_last_games(
        match["home_id"]
    )


    away_form = get_last_games(
        match["away_id"]
    )


    h2h_data = get_head_to_head(

        match["home_id"],

        match["away_id"]

    )



# ==========================
# EDGE SCORE
# ==========================


form_score = round(

    (
        calculate_form(home_form)
        +
        calculate_form(away_form)

    ) / 2

)



goal_score = round(

    (
        calculate_attack(home_form)
        +
        calculate_attack(away_form)

    ) / 2

)



h2h_score = calculate_h2h(
    h2h_data
)



home_advantage = 8


motivation = 5
squad = 5
tactics = 5
value = 5



edge_score = (

    form_score

    +

    goal_score

    +

    h2h_score

    +

    home_advantage

    +

    motivation

    +

    squad

    +

    tactics

    +

    value

)



edge_score = min(
    100,
    edge_score
)



# ==========================
# AUSGABE
# ==========================


st.divider()

st.subheader(
    "🤖 AI Edge Score"
)


st.metric(
    "Gesamtbewertung",
    f"{edge_score}/100"
)



score = pd.DataFrame({

    "Bereich":[

        "Form",
        "Tore",
        "H2H",
        "Heimvorteil",
        "Motivation",
        "Kader",
        "Taktik",
        "Value"

    ],


    "Punkte":[

        f"{form_score}/20",
        f"{goal_score}/10",
        f"{h2h_score}/10",
        f"{home_advantage}/15",
        f"{motivation}/10",
        f"{squad}/10",
        f"{tactics}/10",
        f"{value}/15"

    ]

})


st.table(score)



# ==========================
# DATENKONTROLLE
# ==========================


with st.expander(
    "🔎 Analyse-Daten"
):

    st.write(
        "Heim letzte Spiele"
    )

    st.dataframe(
        pd.DataFrame(home_form)
    )


    st.write(
        "Auswärts letzte Spiele"
    )

    st.dataframe(
        pd.DataFrame(away_form)
    )


    st.write(
        "H2H Anzahl:"
    )

    st.write(
        len(h2h_data)
    )



# ==========================
# VALUE ENGINE
# ==========================


st.divider()

st.subheader(
    "🎯 Wett-Engine"
)



quote = st.number_input(

    "Buchmacher Quote",

    min_value=1.01,

    max_value=100.0,

    value=2.00,

    step=0.05

)



model_probability = edge_score / 100



fair_odds = round(

    1 / model_probability,

    2

)



value_percent = round(

    ((quote * model_probability)-1)*100,

    1

)



c1,c2,c3 = st.columns(3)


with c1:

    st.metric(

        "Modell",

        f"{model_probability*100:.1f}%"

    )


with c2:

    st.metric(

        "Faire Quote",

        fair_odds

    )


with c3:

    st.metric(

        "Value",

        f"{value_percent}%"

    )



if value_percent >= 10:

    st.success(
        "🟢 Value Bet"
    )

elif value_percent >= 0:

    st.info(
        "🟡 Kleine Kante"
    )

else:

    st.warning(
        "🔴 Kein Value"
    )
