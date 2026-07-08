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


    except:

        return {}



# ==========================
# TAGESMATCHES
# ==========================

@st.cache_data(ttl=1800)
def get_games():


    today = datetime.now().strftime("%Y-%m-%d")


    data = api_get(
        "fixtures",
        {
            "date": today,
            "timezone": "Europe/Berlin"
        }
    )


    games = []


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


            "Land":
            g["league"]["country"]

        })


    return games



# ==========================
# START APP
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


liga_liste = sorted(
    list(
        set(
            x["Liga"]
            for x in games
        )
    )
)


liga = st.selectbox(
    "🏆 Liga auswählen:",
    liga_liste
)



liga_games = [

    x for x in games

    if x["Liga"] == liga

]



st.info(
    f"{len(liga_games)} Spiele in {liga}"
)



# ==========================
# SPIELAUSWAHL
# ==========================


auswahl = st.selectbox(

    "⚽ Spiel auswählen:",

    [

        f"{x['Heim']} - {x['Auswärts']}"

        for x in liga_games

    ]

)



index = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in liga_games

].index(auswahl)



match = liga_games[index]


st.divider()


st.header(
    f"{match['Heim']} 🆚 {match['Auswärts']}"
)
# ==========================
# FORM DATEN
# ==========================


@st.cache_data(ttl=3600)
def last_games(team_id):


    data = api_get(
        "fixtures",
        {
            "team": team_id,
            "last": 5
        }
    )


    spiele = []


    for g in data.get("response", []):


        if g["goals"]["home"] is None:
            continue


        home = g["teams"]["home"]
        away = g["teams"]["away"]


        if home["id"] == team_id:

            tore_fuer = g["goals"]["home"]
            tore_gegen = g["goals"]["away"]
            sieg = home["winner"]


        else:

            tore_fuer = g["goals"]["away"]
            tore_gegen = g["goals"]["home"]
            sieg = away["winner"]



        spiele.append({

            "Tore": tore_fuer,
            "Gegentore": tore_gegen,
            "Sieg": sieg

        })


    return spiele



# ==========================
# H2H
# ==========================


@st.cache_data(ttl=86400)
def get_h2h(team1, team2):


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
# SCORE BERECHNUNG
# ==========================


def form_score(data):


    if not data:
        return 10


    punkte = 0


    for x in data:


        if x["Sieg"]:

            punkte += 3


        elif x["Sieg"] is None:

            punkte += 1



    return min(
        round((punkte / 15) * 20),
        20
    )



def goal_score(data):


    if not data:
        return 5


    tore = sum(
        x["Tore"]
        for x in data
    )


    gegentore = sum(
        x["Gegentore"]
        for x in data
    )


    wert = 5 + ((tore-gegentore)/2)


    return max(
        0,
        min(
            10,
            round(wert)
        )
    )



def h2h_score(data):


    if not data:
        return 5


    return min(
        10,
        5 + len(data)
    )



# ==========================
# ANALYSE
# ==========================


heim_form = last_games(
    match["home_id"]
)


aus_form = last_games(
    match["away_id"]
)


h2h = get_h2h(
    match["home_id"],
    match["away_id"]
)



form_points = round(
    (
        form_score(heim_form)
        +
        form_score(aus_form)
    ) / 2
)



tor_points = round(
    (
        goal_score(heim_form)
        +
        goal_score(aus_form)
    ) / 2
)



h2h_points = h2h_score(h2h)



# Basiswerte für restliche Säulen
heim_auswaerts = 8
motivation = 5
kader = 5
taktik = 5
value = 5



edge = (

    form_points
    +
    tor_points
    +
    h2h_points
    +
    heim_auswaerts
    +
    motivation
    +
    kader
    +
    taktik
    +
    value

)



edge = min(
    100,
    edge
)



st.divider()


st.subheader(
    "🤖 AI Edge Score"
)


st.metric(
    "Gesamt",
    f"{edge}/100"
)



score_table = pd.DataFrame({

    "Säule":[

        "Form",
        "Torprofil",
        "H2H",
        "Heim/Auswärts",
        "Motivation",
        "Kader",
        "Taktik",
        "Value"

    ],


    "Punkte":[

        f"{form_points}/20",
        f"{tor_points}/10",
        f"{h2h_points}/10",
        f"{heim_auswaerts}/15",
        f"{motivation}/10",
        f"{kader}/10",
        f"{taktik}/10",
        f"{value}/15"

    ]

})


st.table(score_table)



# ==========================
# WETT ENGINE
# ==========================


st.divider()

st.subheader(
    "🎯 Value Analyse"
)



quote = st.number_input(

    "Aktuelle Quote:",

    min_value=1.01,

    max_value=100.0,

    value=2.00,

    step=0.05

)



modell_prob = edge / 100



faire_quote = round(
    1 / modell_prob,
    2
)



value_percent = round(

    ((quote * modell_prob)-1)*100,

    1

)



c1,c2,c3 = st.columns(3)


with c1:

    st.metric(
        "Modellchance",
        f"{modell_prob*100:.1f}%"
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
        "🟡 kleine Kante"
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

    value=16.88

)



einsatz = round(
    bankroll * 0.03,
    2
)



st.metric(
    "Empfohlener Einsatz",
    f"{einsatz} €"
)
