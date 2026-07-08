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
# API
# ==========================

def api_get(endpoint, params):

    headers = {
        "x-apisports-key":
        st.secrets["API_KEY"]
    }


    try:

        r = requests.get(
            f"{API_URL}/{endpoint}",
            headers=headers,
            params=params,
            timeout=10
        )


        return r.json()


    except Exception:

        return {}



# ==========================
# SPIELE LADEN
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
# APP START
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
# LIGA AUSWAHL
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

    "🏆 Liga auswählen",

    liga_liste

)



liga_games = [

    x

    for x in games

    if x["Liga"] == liga

]



st.info(

    f"{len(liga_games)} Spiele in {liga}"

)



# ==========================
# SPIEL AUSWAHL
# ==========================


spiel_namen = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in liga_games

]



auswahl = st.selectbox(

    "⚽ Spiel auswählen",

    spiel_namen

)



index = spiel_namen.index(

    auswahl

)



match = liga_games[index]



st.divider()



st.header(

    f"{match['Heim']} 🆚 {match['Auswärts']}"

)# ==========================
# FORM DATEN
# ==========================


@st.cache_data(ttl=300)
def last_games(team_id):


    data = api_get(

        "fixtures",

        {
            "team": team_id,
            "last": 5
        }

    )


    spiele=[]


    for g in data.get("response", []):


        home = g["teams"]["home"]
        away = g["teams"]["away"]


        gh = g["goals"]["home"]
        ga = g["goals"]["away"]


        if gh is None or ga is None:
            continue



        if home["id"] == team_id:


            tore_fuer = gh
            tore_gegen = ga
            gewonnen = home["winner"]


        else:


            tore_fuer = ga
            tore_gegen = gh
            gewonnen = away["winner"]



        spiele.append({

            "Tore":
            tore_fuer,

            "Gegentore":
            tore_gegen,

            "Sieg":
            gewonnen

        })


    return spiele



# ==========================
# H2H
# ==========================


@st.cache_data(ttl=3600)
def get_h2h(team1, team2):


    data = api_get(

        "fixtures/headtohead",

        {
            "h2h":
            f"{team1}-{team2}",

            "last":5

        }

    )


    return data.get(
        "response",
        []
    )



# ==========================
# SCORE FUNKTIONEN
# ==========================


def calc_form(data):


    if not data:
        return 10


    punkte=0


    for x in data:


        if x["Sieg"]:

            punkte += 3


        elif x["Sieg"] is None:

            punkte += 1



    return round(
        (punkte/15)*20
    )



def calc_goals(data):


    if not data:
        return 5


    tore=sum(
        x["Tore"]
        for x in data
    )


    geg=sum(
        x["Gegentore"]
        for x in data
    )


    wert=5+(tore-geg)/2


    return max(
        0,
        min(
            10,
            round(wert)
        )
    )



def calc_h2h(data):


    if not data:
        return 5


    heim=0


    for g in data:


        if g["teams"]["home"]["winner"]:

            heim+=1



    return min(
        10,
        5+heim
    )



# ==========================
# ANALYSE START
# ==========================


with st.spinner(
    "Analysiere Spiel..."
):


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



form_score = round(

    (
        calc_form(heim_form)
        +
        calc_form(aus_form)

    ) / 2

)



tor_score = round(

    (
        calc_goals(heim_form)
        +
        calc_goals(aus_form)

    ) / 2

)



h2h_score = calc_h2h(h2h)



# Heimvorteil dynamisch

heim_bonus = 8



# Restliche Säulen vorerst neutral

motivation = 5
kader = 5
taktik = 5
value = 5



edge = (

    form_score
    +
    tor_score
    +
    h2h_score
    +
    heim_bonus
    +
    motivation
    +
    kader
    +
    taktik
    +
    value

)



edge=min(
    100,
    edge
)



# ==========================
# AUSGABE
# ==========================


st.divider()

st.subheader(
    "🤖 AI Edge Score"
)



st.metric(
    "Gesamt",
    f"{edge}/100"
)



score_table=pd.DataFrame({

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

        f"{form_score}/20",
        f"{tor_score}/10",
        f"{h2h_score}/10",
        f"{heim_bonus}/15",
        f"{motivation}/10",
        f"{kader}/10",
        f"{taktik}/10",
        f"{value}/15"

    ]

})



st.table(score_table)



# ==========================
# DEBUG
# ==========================


with st.expander(
    "🔎 Rohdaten prüfen"
):

    st.write(
        "Heim letzte 5 Spiele"
    )

    st.dataframe(
        pd.DataFrame(heim_form)
    )


    st.write(
        "Auswärts letzte 5 Spiele"
    )

    st.dataframe(
        pd.DataFrame(aus_form)
    )


    st.write(
        "H2H Spiele:"
    )

    st.write(
        len(h2h)
    )



# ==========================
# VALUE ENGINE
# ==========================


st.divider()

st.subheader(
    "🎯 Value Analyse"
)



quote = st.number_input(

    "Aktuelle Quote",

    min_value=1.01,

    max_value=100.0,

    value=2.00,

    step=0.05

)



modell = edge / 100



faire_quote = round(
    1/modell,
    2
)



value_prozent = round(

    ((quote*modell)-1)*100,

    1

)



c1,c2,c3 = st.columns(3)



with c1:

    st.metric(
        "Modell",
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
        f"{value_prozent}%"
    )



if value_prozent >= 10:

    st.success(
        "🟢 Value vorhanden"
    )

elif value_prozent >= 0:

    st.info(
        "🟡 Kleine Kante"
    )

else:

    st.warning(
        "🔴 Kein Value"
    )
