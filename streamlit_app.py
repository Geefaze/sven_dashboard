import streamlit as st
import requests
import pandas as pd
from datetime import datetime


st.set_page_config(
    page_title="Sven AI Betting Cockpit 2.0",
    page_icon="⚽",
    layout="wide"
)


API_URL = "https://v3.football.api-sports.io"


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
            st.error("Falsches Passwort")

    st.stop()



# ==========================
# API
# ==========================


def api_get(endpoint, params):

    try:

        r = requests.get(

            f"{API_URL}/{endpoint}",

            headers={
                "x-apisports-key":
                st.secrets["API_KEY"]
            },

            params=params,

            timeout=15

        )

        return r.json()


    except Exception as e:

        return {
            "response": [],
            "errors": str(e)
        }



# ==========================
# SPIELE
# ==========================


@st.cache_data(ttl=300)
def load_games():


    today = datetime.now().strftime("%Y-%m-%d")


    data = api_get(

        "fixtures",

        {
            "date": today
        }

    )


    st.sidebar.subheader(
        "🔧 API Diagnose"
    )

    st.sidebar.write(
        "Datum:",
        today
    )

    st.sidebar.write(
        "Ergebnisse:",
        data.get("results")
    )

    st.sidebar.write(
        "Fehler:",
        data.get("errors")
    )


    games=[]


    for g in data.get("response", []):


        games.append({

            "Liga":
            g["league"]["name"],

            "Land":
            g["league"]["country"],

            "Heim":
            g["teams"]["home"]["name"],

            "Auswärts":
            g["teams"]["away"]["name"],

            "home_id":
            g["teams"]["home"]["id"],

            "away_id":
            g["teams"]["away"]["id"]

        })


    return games



# ==========================
# AI SCORE BASIS
# ==========================


def calculate_edge(game):


    home = game["home_id"]

    away = game["away_id"]


    score = 50


    # kleiner neutraler Algorithmus
    # wird später mit Form/H2H ersetzt

    score += home % 20

    score -= away % 10


    if game["Land"] != "World":

        score += 5



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
    "⚽ Sven AI Betting Cockpit 2.0"
)


games = load_games()



if not games:

    st.error(
        "Keine Spiele gefunden"
    )

    st.stop()



st.success(

    f"{len(games)} Spiele geladen"

)



# ==========================
# SCANNER
# ==========================


for g in games:

    g["AI Edge"] = calculate_edge(g)



df = pd.DataFrame(games)



df = df.sort_values(

    by="AI Edge",

    ascending=False

)



st.divider()


st.header(
    "🔥 Tages Scanner Ranking"
)



minimum = st.slider(

    "Minimaler AI Edge Score",

    0,

    100,

    60

)



ranking = df[

    df["AI Edge"] >= minimum

]



st.dataframe(

    ranking[

        [

            "Liga",

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
    "⚽ Detailanalyse"
)



spiele = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in ranking.to_dict("records")

]



if not spiele:

    st.warning(
        "Keine Spiele mit diesem Score"
    )

    st.stop()



auswahl = st.selectbox(

    "Spiel auswählen",

    spiele

)

# ==========================
# AUSGEWÄHLTES SPIEL
# ==========================


match_list = ranking.to_dict(
    "records"
)


match = None


for m in match_list:

    if f"{m['Heim']} - {m['Auswärts']}" == auswahl:

        match = m
        break



if match:


    st.divider()


    st.header(

        f"{match['Heim']} 🆚 {match['Auswärts']}"

    )



    edge = match["AI Edge"]



    # ==========================
    # 8-SÄULEN SYSTEM
    # ==========================


    st.subheader(
        "🤖 AI Edge Score"
    )



    st.metric(

        "Gesamt",

        f"{edge}/100"

    )



    # vorläufige Säulen
    # werden im nächsten Ausbau mit echten API-Daten gefüllt


    form = min(
        20,
        10 + edge % 11
    )


    kader = 5 + edge % 5


    h2h = 5 + edge % 5


    heim = 8 + edge % 5


    historie = 5


    taktik = 5


    motivation = 5


    value = 5



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


        "Punkte":[

            f"{form}/20",

            f"{kader}/10",

            f"{h2h}/10",

            f"{heim}/15",

            f"{historie}/10",

            f"{taktik}/10",

            f"{motivation}/10",

            f"{value}/15"

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

        "Aktuelle Quote",

        min_value=1.01,

        max_value=100.0,

        value=2.00,

        step=0.05

    )



    modell_chance = edge / 100



    faire_quote = round(

        1 / modell_chance,

        2

    )



    value_percent = round(

        ((quote * modell_chance)-1)*100,

        1

    )



    c1,c2,c3 = st.columns(3)



    with c1:

        st.metric(

            "Modellchance",

            f"{modell_chance*100:.1f}%"

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
        "💰 Einsatzberechnung"
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



else:

    st.warning(
        "Spiel konnte nicht geladen werden"
    )
