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

    pw = st.text_input(
        "Passwort",
        type="password"
    )


    if st.button("Anmelden"):

        if pw == "Sven2026":

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
# COMPETITIONS
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
# MATCHES
# ==========================

@st.cache_data(ttl=900)
def get_matches(comp_id):

    data = api_get(

        f"/competitions/{comp_id}/matches"

    )

    return data.get(
        "matches",
        []
    )



# ==========================
# TABLE
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

def edge_score(home_id, away_id, table):

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


competitions = get_competitions()



st.sidebar.header(
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



games = []



progress = st.progress(0)



for i, comp in enumerate(competitions):


    matches = get_matches(

        comp["id"]

    )


    table = get_table(

        comp["id"]

    )


    for m in matches:


        if not m.get("homeTeam"):

            continue


        if m["status"] == "FINISHED":

            continue


        try:

            dt = datetime.fromisoformat(

                m["utcDate"].replace(

                    "Z",

                    "+00:00"

                )

            ).astimezone(

                ZoneInfo(
                    "Europe/Berlin"
                )

            )

        except:

            continue



        games.append({

            "Liga":
            comp["name"],


            "Datum":
            dt.strftime(

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
            edge_score(

                m["homeTeam"]["id"],

                m["awayTeam"]["id"],

                table

            )

        })


    progress.progress(

        (i+1)/len(competitions)

    )
    # ==========================
# AUSWERTUNG
# ==========================


st.sidebar.write(

    "Gefundene Spiele:",

    len(games)

)



if not games:

    st.warning(

        "Keine zukünftigen Spiele gefunden"

    )


    st.info(

        "Die API hat zwar Wettbewerbe geliefert, aber aktuell keine offenen Spiele."

    )


    st.stop()



df = pd.DataFrame(games)



df = df.sort_values(

    by="AI Edge",

    ascending=False

)



st.success(

    f"{len(df)} Spiele gefunden"

)



# ==========================
# RANKING
# ==========================


st.divider()


st.header(

    "🔥 AI Match Ranking"

)



st.dataframe(

    df[

        [

            "Liga",

            "Datum",

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



spiel_liste = [

    f"{x['Heim']} - {x['Auswärts']}"

    for x in games

]



auswahl = st.selectbox(

    "Spiel auswählen",

    spiel_liste

)



match = games[

    spiel_liste.index(auswahl)

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



saeulen = pd.DataFrame({

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

    saeulen

)



# ==========================
# WETT ENGINE
# ==========================


st.divider()


st.subheader(

    "🎯 Wett-Engine"

)



quote = st.number_input(

    "Quote eingeben",

    min_value=1.01,

    max_value=100.0,

    value=2.00,

    step=0.05

)



chance = edge / 100



faire_quote = round(

    1/chance,

    2

)



value = round(

    ((quote * chance)-1)*100,

    1

)



a,b,c = st.columns(3)



with a:

    st.metric(

        "Modellwahrscheinlichkeit",

        f"{chance*100:.1f}%"

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

    "💰 Bankroll"

)



bankroll = st.number_input(

    "Kontostand €",

    min_value=1.0,

    value=18.88

)



einsatz = round(

    bankroll * 0.03,

    2

)



st.metric(

    "Empfohlener Einsatz",

    f"{einsatz} €"

)
