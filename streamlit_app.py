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

    except:

        return {}



# ==========================
# SPIELE
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
            g["league"]["name"]

        })


    return games



# ==========================
# LETZTE SPIELE
# ==========================

@st.cache_data(ttl=3600)
def last_games(team_id):

    data = api_get(
        "fixtures",
        {
            "team": team_id,
            "last":5
        }
    )


    spiele=[]


    for g in data.get("response", []):

        if g["goals"]["home"] is None:
            continue


        home=g["teams"]["home"]

        away=g["teams"]["away"]


        if home["id"] == team_id:

            tore_fuer=g["goals"]["home"]
            tore_gegen=g["goals"]["away"]

            sieg=home["winner"]

        else:

            tore_fuer=g["goals"]["away"]
            tore_gegen=g["goals"]["home"]

            sieg=away["winner"]



        spiele.append({

            "Tore":
            tore_fuer,

            "Gegentore":
            tore_gegen,

            "Sieg":
            sieg

        })


    return spiele



# ==========================
# H2H
# ==========================

@st.cache_data(ttl=86400)
def get_h2h(team1,team2):

    data=api_get(
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


def form_points(data):

    punkte=0


    for x in data:

        if x["Sieg"]:

            punkte+=3

        elif x["Sieg"] is None:

            punkte+=1


    return min(
        round((punkte/15)*20),
        20
    )



def goal_points(data):

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



def h2h_points(data):

    if not data:
        return 5


    return min(
        10,
        5+len(data)
    )



# ==========================
# APP
# ==========================


st.title(
    "⚽ Sven AI Betting Cockpit"
)


games=get_games()


if not games:

    st.warning(
        "Keine Spiele gefunden"
    )

    st.stop()



df=pd.DataFrame(games)



st.success(
    f"{len(df)} Spiele geladen"
)



auswahl=st.selectbox(

    "Spiel auswählen",

    [
        f"{x['Heim']} - {x['Auswärts']}"

        for x in games

    ]

)



idx=[
    f"{x['Heim']} - {x['Auswärts']}"

    for x in games

].index(auswahl)



match=games[idx]



st.header(
    f"{match['Heim']} 🆚 {match['Auswärts']}"
)


heim_form=last_games(
    match["home_id"]
)


aus_form=last_games(
    match["away_id"]
)


h2h=get_h2h(
    match["home_id"],
    match["away_id"]
)


form_score=(
    form_points(heim_form)
    +
    form_points(aus_form)
)/2


tor_score=(
    goal_points(heim_form)
    +
    goal_points(aus_form)
)/2


h2h_score=h2h_points(h2h)



edge=round(
    form_score
    +
    tor_score
    +
    h2h_score
    +
    35
)



edge=min(
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
        f"{round(form_score)}/20",
        f"{round(tor_score)}/10",
        f"{h2h_score}/10",
        "Basis",
        "Basis",
        "Offen",
        "Offen",
        "Offen"
    ]

})


st.table(score_table)
