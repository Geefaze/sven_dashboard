import streamlit as st
import requests
import pandas as pd
from datetime import datetime


# ==========================
# CONFIG
# ==========================

st.set_page_config(
    page_title="Sven AI Betting Cockpit",
    page_icon="⚽",
    layout="wide"
)


API_URL = "https://api.football-data.org/v4"



# ==========================
# LOGIN
# ==========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if not st.session_state.logged_in:

    st.title("🔒 Sven AI Betting Cockpit")


    password = st.text_input(
        "Passwort",
        type="password"
    )


    if st.button("Anmelden"):

        if password == "Sven2026":

            st.session_state.logged_in = True
            st.rerun()

        else:

            st.error(
                "Falsches Passwort"
            )


    st.stop()



# ==========================
# API FUNKTION
# ==========================


def api_call(endpoint):

    try:

        response = requests.get(

            API_URL + endpoint,

            headers={
                "X-Auth-Token": st.secrets["API_KEY"]
            },

            timeout=15

        )


        return response.json()


    except Exception as e:

        return {
            "error": str(e)
        }



# ==========================
# WETTBEWERBE
# ==========================


@st.cache_data(ttl=3600)
def load_competitions():

    data = api_call(
        "/competitions"
    )

    return data.get(
        "competitions",
        []
    )



# ==========================
# SPIELE
# ==========================


@st.cache_data(ttl=600)
def load_matches(competition_id):

    data = api_call(

        f"/competitions/{competition_id}/matches"

    )


    return data.get(
        "matches",
        []
    )



# ==========================
# TABELLE
# ==========================


@st.cache_data(ttl=3600)
def load_table(competition_id):

    data = api_call(

        f"/competitions/{competition_id}/standings"

    )


    try:

        return data["standings"][0]["table"]

    except:

        return []



# ==========================
# EDGE SCORE
# ==========================


def edge_score(home_id, away_id, table):


    score = 50


    home_pos = 10
    away_pos = 10


    for team in table:


        if team["team"]["id"] == home_id:

            home_pos = team["position"]


        if team["team"]["id"] == away_id:

            away_pos = team["position"]



    score += away_pos - home_pos


    if score > 100:
        score = 100


    if score < 1:
        score = 1


    return score



# ==========================
# START APP
# ==========================


st.title(
    "⚽ Sven AI Betting Cockpit"
)


competitions = load_competitions()


if not competitions:

    st.error(
        "Keine Ligen gefunden"
    )

    st.stop()



st.sidebar.title(
    "🔧 Diagnose"
)


st.sidebar.write(
    "Ligen:",
    len(competitions)
)


competition_names = [

    c["name"]

    for c in competitions

]


selected_comp = st.selectbox(

    "🏆 Liga auswählen",

    competition_names

)


competition = next(

    c for c in competitions

    if c["name"] == selected_comp

)


matches = load_matches(

    competition["id"]

)


table = load_table(

    competition["id"]

)


st.success(

    f"{len(matches)} Spiele geladen"

)



games = []


for match in matches:


    if not match.get("homeTeam"):

        continue


    games.append({

        "Heim":
        match["homeTeam"]["name"],

        "Auswärts":
        match["awayTeam"]["name"],

        "home_id":
        match["homeTeam"]["id"],

        "away_id":
        match["awayTeam"]["id"],

        "Datum":
        match["utcDate"],

        "Score":
        edge_score(

            match["homeTeam"]["id"],

            match["awayTeam"]["id"],

            table

        )

    })



if not games:

    st.warning(
        "Keine Spiele vorhanden"
    )

    st.stop()

# ==========================
# RANKING
# ==========================


df = pd.DataFrame(games)


df = df.sort_values(

    by="Score",

    ascending=False

)



st.divider()


st.header(
    "🔥 AI Edge Ranking"
)



st.dataframe(

    df[

        [

            "Heim",

            "Auswärts",

            "Score"

        ]

    ],

    use_container_width=True

)



# ==========================
# SPIELAUSWAHL
# ==========================


st.divider()


st.header(
    "⚽ Detailanalyse"
)



match_names = [

    f"{g['Heim']} - {g['Auswärts']}"

    for g in games

]



selected_match = st.selectbox(

    "Spiel auswählen",

    match_names

)



index = match_names.index(

    selected_match

)



match = games[index]



st.subheader(

    f"{match['Heim']} 🆚 {match['Auswärts']}"

)



score = match["Score"]



# ==========================
# AI EDGE SCORE
# ==========================


st.metric(

    "🤖 AI Edge Score",

    f"{score}/100"

)



st.divider()



st.subheader(

    "📊 8-Säulen-System"

)



columns = pd.DataFrame({

    "Säule":[

        "Form",

        "Kader",

        "H2H",

        "Heim/Auswärts",

        "Historie",

        "Taktik",

        "Motivation",

        "Value"

    ],

    "Status":[

        "Basis",

        "Basis",

        "Offen",

        "Basis",

        "Basis",

        "Offen",

        "Offen",

        "Offen"

    ]

})



st.table(columns)



# ==========================
# TABELLE
# ==========================


st.divider()


st.subheader(

    "🏆 Tabelle"

)



if table:


    table_view = []


    for t in table:


        table_view.append({

            "Platz":
            t["position"],

            "Team":
            t["team"]["name"],

            "Punkte":
            t["points"],

            "Tore":
            f"{t['goalsFor']}:{t['goalsAgainst']}"

        })


    st.dataframe(

        pd.DataFrame(table_view),

        use_container_width=True

    )



# ==========================
# WETT ENGINE
# ==========================


st.divider()


st.subheader(

    "🎯 Wett-Engine"

)



quote = st.number_input(

    "Deine Quote",

    min_value=1.01,

    max_value=100.0,

    value=2.00,

    step=0.05

)



chance = score / 100



fair_quote = round(

    1 / chance,

    2

)



value = round(

    ((quote * chance)-1)*100,

    1

)



c1,c2,c3 = st.columns(3)



with c1:

    st.metric(

        "Modellchance",

        f"{chance*100:.1f}%"

    )


with c2:

    st.metric(

        "Faire Quote",

        fair_quote

    )


with c3:

    st.metric(

        "Value",

        f"{value}%"

    )



if value >= 10:

    st.success(

        "🟢 VALUE BET"

    )

elif value >= 0:

    st.info(

        "🟡 Kleine Kante"

    )

else:

    st.warning(

        "🔴 Kein Value"

    )



# ==========================
# BANKROLL
# ==========================


st.divider()


st.subheader(

    "💰 Einsatz"

)



bankroll = st.number_input(

    "Bankroll (€)",

    min_value=1.0,

    value=18.88

)



stake = round(

    bankroll * 0.03,

    2

)



st.metric(

    "3% Einsatz",

    f"{stake} €"

)
