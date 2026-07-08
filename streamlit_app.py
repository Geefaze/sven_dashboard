import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta


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

    try:

        response = requests.get(

            f"{API_URL}/{endpoint}",

            headers={
                "x-apisports-key":
                st.secrets["API_KEY"]
            },

            params=params,

            timeout=15

        )


        return response.json()


    except Exception as e:

        return {
            "errors": str(e),
            "response": []
        }



# ==========================
# SPIELE LADEN
# ==========================


@st.cache_data(ttl=600)
def get_games():


    heute = datetime.now()


    # mehrere Tage prüfen falls Zeitzone abweicht

    tage = [

        heute.strftime("%Y-%m-%d"),

        (heute + timedelta(days=1)).strftime("%Y-%m-%d"),

        (heute - timedelta(days=1)).strftime("%Y-%m-%d")

    ]



    alle_spiele=[]



    for tag in tage:


        data = api_get(

            "fixtures",

            {

                "date": tag,

                "timezone": "Europe/Berlin"

            }

        )



        for item in data.get("response", []):


            alle_spiele.append({

                "Datum":
                tag,


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



    return alle_spiele



# ==========================
# APP
# ==========================


st.title(
    "⚽ Sven AI Betting Cockpit"
)


st.subheader(
    "📅 Tagesaktueller Match Scanner"
)



games = get_games()



# API DIAGNOSE

with st.expander(
    "🔧 API Diagnose"
):


    st.write(
        "Aktuelles Datum:"
    )

    st.write(
        datetime.now().strftime("%Y-%m-%d")
    )


    st.write(
        "Geladene Spiele:"
    )

    st.write(
        len(games)
    )



if not games:

    st.error(
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

            x["Liga"]

            for x in games

        )

    )

)



liga = st.selectbox(

    "🏆 Liga auswählen",

    ligen

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


spiel_liste=[

    f"{x['Heim']} - {x['Auswärts']}"

    for x in liga_games

]



auswahl = st.selectbox(

    "⚽ Spiel auswählen",

    spiel_liste

)



index = spiel_liste.index(

    auswahl

)



match = liga_games[index]



st.divider()


st.header(

    f"{match['Heim']} 🆚 {match['Auswärts']}"

)
# ==========================
# LETZTE SPIELE
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


    spiele=[]


    for g in data.get("response", []):


        home = g["teams"]["home"]
        away = g["teams"]["away"]


        hg = g["goals"]["home"]
        ag = g["goals"]["away"]


        if hg is None or ag is None:
            continue



        if home["id"] == team_id:

            tore = hg
            gegentore = ag
            sieg = home["winner"]


        else:

            tore = ag
            gegentore = hg
            sieg = away["winner"]



        spiele.append({

            "Tore": tore,

            "Gegentore": gegentore,

            "Sieg": sieg

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


def form_points(data):


    if not data:

        return 10



    punkte=0



    for x in data:


        if x["Sieg"] is True:

            punkte += 3


        elif x["Sieg"] is None:

            punkte += 1



    return min(

        20,

        round(

            (punkte/15)*20

        )

    )



def goal_points(data):


    if not data:

        return 5



    tore=sum(

        x["Tore"]

        for x in data

    )


    gegentore=sum(

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



def h2h_points(data):


    if not data:

        return 5



    return min(

        10,

        5+len(data)

    )



# ==========================
# ANALYSE
# ==========================


with st.spinner(
    "🤖 Berechne AI Edge Score..."
):


    heim_form = get_last_games(

        match["home_id"]

    )


    aus_form = get_last_games(

        match["away_id"]

    )


    h2h = get_h2h(

        match["home_id"],

        match["away_id"]

    )



form = round(

    (

        form_points(heim_form)

        +

        form_points(aus_form)

    ) / 2

)



tore = round(

    (

        goal_points(heim_form)

        +

        goal_points(aus_form)

    ) / 2

)



h2h_score = h2h_points(h2h)



heimvorteil = 8



motivation = 5

kader = 5

taktik = 5

value = 5



edge = (

    form

    +

    tore

    +

    h2h_score

    +

    heimvorteil

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



score_df = pd.DataFrame({

    "Säule":[

        "Form",
        "Tore",
        "H2H",
        "Heim/Auswärts",
        "Motivation",
        "Kader",
        "Taktik",
        "Value"

    ],


    "Punkte":[

        f"{form}/20",

        f"{tore}/10",

        f"{h2h_score}/10",

        f"{heimvorteil}/15",

        f"{motivation}/10",

        f"{kader}/10",

        f"{taktik}/10",

        f"{value}/15"

    ]

})


st.table(score_df)



# ==========================
# DATENKONTROLLE
# ==========================


with st.expander(

    "🔎 Teamdaten prüfen"

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

        "H2H Spiele"

    )


    st.write(

        len(h2h)

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



wahrscheinlichkeit = edge/100



faire_quote = round(

    1/wahrscheinlichkeit,

    2

)



value_prozent = round(

    ((quote*wahrscheinlichkeit)-1)*100,

    1

)



c1,c2,c3 = st.columns(3)



with c1:

    st.metric(

        "Modell",

        f"{wahrscheinlichkeit*100:.1f}%"

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
        "🟢 VALUE BET"
    )


elif value_prozent >= 0:

    st.info(
        "🟡 Kleine Kante"
    )


else:

    st.warning(
        "🔴 Kein Value"
    )
