import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


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

            st.error("Falsches Passwort")


    st.stop()



# ==========================
# API
# ==========================

def api_get(endpoint):

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

        return {}



# ==========================
# WETTBEWERBE
# ==========================

@st.cache_data(ttl=3600)
def get_competitions():

    data = api_get(
        "/competitions"
    )

    return data.get(
        "competitions",
        []
    )



# ==========================
# SPIELE EINER LIGA
# ==========================

@st.cache_data(ttl=600)
def get_matches(comp_id):

    data = api_get(

        f"/competitions/{comp_id}/matches"

    )

    return data.get(
        "matches",
        []
    )



# ==========================
# TABELLE
# ==========================

@st.cache_data(ttl=3600)
def get_table(comp_id):

    data = api_get(

        f"/competitions/{comp_id}/standings"

    )


    try:

        return data["standings"][0]["table"]

    except:

        return []



# ==========================
# AI EDGE SCORE
# ==========================

def calculate_edge(home, away, table):

    score = 50

    home_pos = 10
    away_pos = 10


    for t in table:

        if t["team"]["id"] == home:

            home_pos = t["position"]


        if t["team"]["id"] == away:

            away_pos = t["position"]



    score += away_pos - home_pos


    return max(
        1,
        min(
            100,
            score
        )
    )



# ==========================
# START
# ==========================

st.title(
    "⚽ Sven AI Betting Cockpit"
)



now = datetime.now(
    ZoneInfo("Europe/Berlin")
)



today = now.date()


end_day = today + timedelta(days=7)



st.info(

    f"📅 Scanner: {today.strftime('%d.%m.%Y')} bis {end_day.strftime('%d.%m.%Y')}"

)



competitions = get_competitions()



st.sidebar.subheader(
    "🔧 API Diagnose"
)


st.sidebar.write(
    "Wettbewerbe:",
    len(competitions)
)



if not competitions:

    st.error(
        "Keine Wettbewerbe gefunden"
    )

    st.stop()



# ==========================
# ALLE SPIELE SCANNEN
# ==========================


all_games = []



progress = st.progress(0)



for index, comp in enumerate(competitions):


    matches = get_matches(

        comp["id"]

    )


    table = get_table(

        comp["id"]

    )



    for m in matches:


        if not m.get("homeTeam"):

            continue



        match_time = datetime.fromisoformat(

            m["utcDate"].replace(
                "Z",
                "+00:00"
            )

        ).astimezone(

            ZoneInfo("Europe/Berlin")

        )



        if match_time.date() < today:

            continue



        if match_time.date() > end_day:

            continue



        if m["status"] == "FINISHED":

            continue



        all_games.append({

            "Liga":
            comp["name"],


            "Zeit":
            match_time.strftime(
                "%d.%m.%Y %H:%M"
            ),


            "Heim":
            m["homeTeam"]["name"],


            "Auswärts":
            m["awayTeam"]["name"],


            "home_id":
            m["homeTeam"]["id"],


            "away_id":
            m["awayTeam"]["id"],


            "AI Edge":
            calculate_edge(

                m["homeTeam"]["id"],

                m["awayTeam"]["id"],

                table

            )

        })


    progress.progress(

        (index + 1) / len(competitions)

    )
    # ==========================
# AUSWERTUNG
# ==========================


if not all_games:

    st.warning(
        "Keine Spiele im Zeitraum gefunden"
    )

    st.stop()



df = pd.DataFrame(all_games)



df = df.sort_values(

    by="AI Edge",

    ascending=False

)



st.success(

    f"{len(df)} Spiele gefunden"

)



# ==========================
# TOP RANKING
# ==========================


st.divider()


st.header(
    "🔥 AI Match Ranking"
)



st.dataframe(

    df[

        [

            "Liga",

            "Zeit",

            "Heim",

            "Auswärts",

            "AI Edge"

        ]

    ],

    use_container_width=True

)



# ==========================
# SPIEL AUSWAHL
# ==========================


st.divider()


st.header(
    "⚽ Detailanalyse"
)



match_list = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in all_games

]



selected = st.selectbox(

    "Spiel auswählen",

    match_list

)



match = all_games[

    match_list.index(selected)

]



st.subheader(

    f"{match['Heim']} 🆚 {match['Auswärts']}"

)



edge = match["AI Edge"]



st.metric(

    "🤖 AI Edge Score",

    f"{edge}/100"

)



# ==========================
# 8 SÄULEN
# ==========================


st.divider()


st.subheader(

    "📊 8-Säulen-System"

)



score_table = pd.DataFrame({

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

    "Bewertung":[

        "Basis",

        "Offen",

        "Offen",

        "Basis",

        "Basis",

        "Offen",

        "Offen",

        "Offen"

    ]

})


st.table(

    score_table

)



# ==========================
# WETT ENGINE
# ==========================


st.divider()


st.subheader(

    "🎯 Wett-Engine"

)



quote = st.number_input(

    "Quote",

    min_value=1.01,

    max_value=100.0,

    value=2.00,

    step=0.05

)



probability = edge / 100



fair_quote = round(

    1 / probability,

    2

)



value = round(

    ((quote * probability)-1)*100,

    1

)



a,b,c = st.columns(3)



with a:

    st.metric(

        "Modellchance",

        f"{probability*100:.1f}%"

    )


with b:

    st.metric(

        "Faire Quote",

        fair_quote

    )


with c:

    st.metric(

        "Value",

        f"{value}%"

    )



if value >= 10:

    st.success(
        "🟢 VALUE BET erkannt"
    )

elif value >= 0:

    st.info(
        "🟡 Kleine Modellkante"
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

    "💰 Bankroll"

)



bankroll = st.number_input(

    "Kontostand (€)",

    min_value=1.0,

    value=18.88

)



stake = round(

    bankroll * 0.03,

    2

)



st.metric(

    "Empfohlener Einsatz",

    f"{stake} €"

)
