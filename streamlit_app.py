import streamlit as st
import requests
import pandas as pd
from datetime import datetime
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

def api_call(endpoint):

    try:

        r = requests.get(

            API_URL + endpoint,

            headers={
                "X-Auth-Token": st.secrets["API_KEY"]
            },

            timeout=15

        )

        return r.json()


    except Exception as e:

        return {
            "error": str(e)
        }



# ==========================
# WETTBEWERBE
# ==========================

@st.cache_data(ttl=3600)
def get_competitions():

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

@st.cache_data(ttl=300)
def get_matches(comp_id):

    data = api_call(

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

    data = api_call(

        f"/competitions/{comp_id}/standings"

    )

    try:

        return data["standings"][0]["table"]

    except:

        return []



# ==========================
# AI SCORE
# ==========================

def calculate_score(home_id, away_id, table):

    score = 50

    home_pos = 10
    away_pos = 10


    for t in table:

        if t["team"]["id"] == home_id:
            home_pos = t["position"]


        if t["team"]["id"] == away_id:
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


today = datetime.now(
    ZoneInfo("Europe/Berlin")
).strftime("%Y-%m-%d")



st.info(
    f"📅 Scanner Datum: {today}"
)



competitions = get_competitions()



st.sidebar.subheader(
    "🔧 API Diagnose"
)


st.sidebar.write(
    "Ligen geladen:",
    len(competitions)
)



if not competitions:

    st.error(
        "Keine Ligen gefunden"
    )

    st.stop()



liga_namen = [

    c["name"]

    for c in competitions

]



liga = st.selectbox(

    "🏆 Liga",

    liga_namen

)



competition = next(

    x for x in competitions

    if x["name"] == liga

)



matches = get_matches(

    competition["id"]

)



table = get_table(

    competition["id"]

)



games = []



for m in matches:


    # nur heutige Spiele

    if m["utcDate"][:10] != today:

        continue


    # keine fertigen Spiele

    if m["status"] == "FINISHED":

        continue


    games.append({

        "Heim":
        m["homeTeam"]["name"],


        "Auswärts":
        m["awayTeam"]["name"],


        "home_id":
        m["homeTeam"]["id"],


        "away_id":
        m["awayTeam"]["id"],


        "Zeit":
        datetime.fromisoformat(

            m["utcDate"].replace(
                "Z",
                "+00:00"
            )

        ).astimezone(

            ZoneInfo("Europe/Berlin")

        ).strftime(
            "%H:%M"
        ),


        "AI Edge":
        calculate_score(

            m["homeTeam"]["id"],

            m["awayTeam"]["id"],

            table

        )

    })



st.sidebar.write(
    "Heutige Spiele:",
    len(games)
)


if not games:

    st.warning(
        "Heute keine Spiele in dieser Liga gefunden"
    )

    st.stop()
    # ==========================
# RANKING
# ==========================


df = pd.DataFrame(games)


df = df.sort_values(

    by="AI Edge",

    ascending=False

)



st.divider()


st.header(
    "🔥 Tages Ranking"
)



st.dataframe(

    df[

        [

            "Zeit",

            "Heim",

            "Auswärts",

            "AI Edge"

        ]

    ],

    use_container_width=True

)



# ==========================
# SPIELAUSWAHL
# ==========================


st.divider()


st.header(
    "⚽ Spielanalyse"
)



spiel_namen = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in games

]



auswahl = st.selectbox(

    "Spiel auswählen",

    spiel_namen

)



match = games[

    spiel_namen.index(auswahl)

]



st.subheader(

    f"{match['Heim']} 🆚 {match['Auswärts']}"

)



score = match["AI Edge"]



st.metric(

    "🤖 AI Edge Score",

    f"{score}/100"

)



# ==========================
# 8 SÄULEN SYSTEM
# ==========================


st.divider()


st.subheader(

    "📊 8-Säulen Analyse"

)



analyse = pd.DataFrame({

    "Bereich":[

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


st.table(analyse)



# ==========================
# TABELLE
# ==========================


st.divider()


st.subheader(

    "🏆 Tabelle"

)



if table:


    rows = []


    for t in table:


        rows.append({

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

        pd.DataFrame(rows),

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

    "Buchmacher Quote",

    min_value=1.01,

    max_value=100.0,

    value=2.00,

    step=0.05

)



wahrscheinlichkeit = score / 100



faire_quote = round(

    1 / wahrscheinlichkeit,

    2

)



value = round(

    ((quote * wahrscheinlichkeit)-1)*100,

    1

)



a,b,c = st.columns(3)



with a:

    st.metric(

        "Modell",

        f"{wahrscheinlichkeit*100:.1f}%"

    )


with b:

    st.metric(

        "Faire Quote",

        faire_quote

    )


with c:

    st.metric(

        "Value",

        f"{value}%"

    )



if value >= 10:

    st.success(
        "🟢 Value Bet"
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



einsatz = round(

    bankroll * 0.03,

    2

)



st.metric(

    "3%-Einsatz",

    f"{einsatz} €"

)
