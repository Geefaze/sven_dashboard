import streamlit as st
import requests
import pandas as pd
from datetime import datetime


st.set_page_config(
    page_title="Sven AI Betting Cockpit 3.0",
    page_icon="⚽",
    layout="wide"
)


API_URL = "https://api.football-data.org/v4"



# ==========================
# LOGIN
# ==========================

if "login" not in st.session_state:
    st.session_state.login = False


if not st.session_state.login:

    st.title("🔒 Sven AI Betting Cockpit")

    pw = st.text_input(
        "Passwort",
        type="password"
    )


    if st.button("Anmelden"):

        if pw == "Sven2026":

            st.session_state.login = True
            st.rerun()

        else:

            st.error(
                "Falsches Passwort"
            )


    st.stop()



# ==========================
# API
# ==========================


def api_get(url):

    try:

        r = requests.get(

            url,

            headers={

                "X-Auth-Token":
                st.secrets["API_KEY"]

            },

            timeout=15

        )


        return r.json()


    except Exception as e:


        return {

            "error": str(e)

        }



# ==========================
# VERFÜGBARE LIGEN
# ==========================


@st.cache_data(ttl=3600)
def get_competitions():


    data = api_get(

        f"{API_URL}/competitions"

    )


    return data.get(

        "competitions",

        []

    )



# ==========================
# SPIELE EINER LIGA
# ==========================


@st.cache_data(ttl=300)
def get_matches(comp_id):


    data = api_get(

        f"{API_URL}/competitions/{comp_id}/matches"

    )


    return data.get(

        "matches",

        []

    )



# ==========================
# TEAM TABELLE
# ==========================


@st.cache_data(ttl=3600)
def get_table(comp_id):


    data = api_get(

        f"{API_URL}/competitions/{comp_id}/standings"

    )


    try:

        return data["standings"][0]["table"]

    except:

        return []



# ==========================
# FORM
# ==========================


@st.cache_data(ttl=3600)
def get_team_form(team_id):


    data = api_get(

        f"{API_URL}/teams/{team_id}/matches?limit=5"

    )


    return data.get(

        "matches",

        []

    )



# ==========================
# AI SCORE
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



    score += (

        away_pos

        -

        home_pos

    )



    return max(

        1,

        min(

            100,

            score

        )

    )



# ==========================
# APP
# ==========================


st.title(
    "⚽ Sven AI Betting Cockpit 3.0"
)


competitions = get_competitions()



if not competitions:

    st.error(
        "Keine Wettbewerbe gefunden"
    )

    st.stop()



st.sidebar.subheader(
    "🔧 API Diagnose"
)


st.sidebar.write(

    "Wettbewerbe:",

    len(competitions)

)



liga_namen = [

    x["name"]

    for x in competitions

]


liga = st.selectbox(

    "🏆 Liga auswählen",

    liga_namen

)



competition = next(

    x for x in competitions

    if x["name"] == liga

)



matches = get_matches(

    competition["id"]

)



st.success(

    f"{len(matches)} Spiele geladen"

)



if not matches:

    st.warning(
        "Keine Spiele in dieser Liga"
    )

    st.stop()



table = get_table(

    competition["id"]

)



spiele=[]


for m in matches:


    if m["status"] != "SCHEDULED":

        continue


    spiele.append({

        "Heim":
        m["homeTeam"]["name"],

        "Auswärts":
        m["awayTeam"]["name"],

        "home_id":
        m["homeTeam"]["id"],

        "away_id":
        m["awayTeam"]["id"],

        "Datum":
        m["utcDate"],

        "AI Edge":
        calculate_edge(

            m["homeTeam"]["id"],

            m["awayTeam"]["id"],

            table

        )

    })


if not spiele:

    st.warning(
        "Keine kommenden Spiele gefunden"
    )

    st.stop()



df = pd.DataFrame(spiele)


df = df.sort_values(

    "AI Edge",

    ascending=False

)


st.divider()

st.header(
    "🔥 AI Ranking"
)


st.dataframe(

    df[

        [

            "Heim",

            "Auswärts",

            "AI Edge"

        ]

    ],
# ==========================
# DETAILANALYSE
# ==========================


st.divider()


st.header(
    "⚽ Detailanalyse"
)



spiel_namen = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in spiele

]



auswahl = st.selectbox(

    "Spiel auswählen",

    spiel_namen

)



match = spiele[

    spiel_namen.index(auswahl)

]



st.subheader(

    f"{match['Heim']} 🆚 {match['Auswärts']}"

)



edge = match["AI Edge"]



# ==========================
# 8 SÄULEN SYSTEM
# ==========================


st.subheader(
    "🤖 AI Edge Score"
)


st.metric(

    "Gesamt",

    f"{edge}/100"

)



# aktuelle Basisbewertung

form = min(

    20,

    10 + edge % 11

)


tore = min(

    10,

    5 + edge % 6

)


h2h = min(

    10,

    5 + edge % 6

)


heim = min(

    15,

    8 + edge % 8

)


historie = 5


taktik = 5


motivation = 5


value = 5



score = pd.DataFrame({

    "Säule":[

        "Form",

        "Torprofil",

        "H2H",

        "Heim/Auswärts",

        "Historie",

        "Taktik",

        "Motivation",

        "Value"

    ],

    "Punkte":[

        f"{form}/20",

        f"{tore}/10",

        f"{h2h}/10",

        f"{heim}/15",

        f"{historie}/10",

        f"{taktik}/10",

        f"{motivation}/10",

        f"{value}/15"

    ]

})



st.table(score)



# ==========================
# TABELLE
# ==========================


st.divider()


st.subheader(
    "📊 Tabelleninfo"
)



if table:


    table_df = pd.DataFrame(table)


    st.dataframe(

        table_df[

            [

                "position",

                "team",

                "points",

                "goalsFor",

                "goalsAgainst"

            ]

        ],

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



modell = edge / 100



faire_quote = round(

    1 / modell,

    2

)



value_percent = round(

    ((quote * modell)-1)*100,

    1

)



c1,c2,c3 = st.columns(3)



with c1:

    st.metric(

        "Modellwahrscheinlichkeit",

        f"{modell*100:.1f}%"

    )


with c2:

    st.metric(

        "Faire Quote",

        faire_quote

    )


with c3:

    st.metric(

        "Value",

        f"{value_percent}%"

    )



if value_percent >= 10:

    st.success(

        "🟢 VALUE BET"

    )


elif value_percent >= 0:

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

    "3%-Regel Einsatz",

    f"{einsatz} €"

)
    use_container_width=True

)
