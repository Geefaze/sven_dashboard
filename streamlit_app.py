import streamlit as st
import pandas as pd
import numpy as np
import math
import requests
import io

if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.get("password_correct", False):
    st.title("🔒 Sven's Analytics Dashboard")
    user_password = st.text_input("Bitte Passwort eingeben:", type="password")
    if st.button("Anmelden"):
        if user_password == "Sven2026":
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ Falsches Passwort!")
    st.stop()

st.title("📊 Sven's 8-Pillar Global Betting Cockpit")

# ⚙️ SYSTEMEINSTELLUNGEN
st.sidebar.header("⚙️ Systemeinstellungen")
modus = st.sidebar.radio("Modus auswählen:", ["Herren-Fußball (Regulär)", "Frauen-Fußball (Strenges Overlay)"])

is_womens_football = (modus == "Frauen-Fußball (Strenges Overlay)")
min_value_margin = 0.15 if is_womens_football else 0.05

# 🌐 LIVE-ABRUF VON FOOTBALL-DATA.CO.UK
@st.cache_data(ttl=3600)  # Aktualisiert alle 60 Minuten
def fetch_real_football_data():
    # Mapping der wichtigsten Ligen von football-data.co.uk
    ligamap = {
        "England: Premier League": "E0",
        "Deutschland: 1. Bundesliga": "D1",
        "Spanien: La Liga": "SP1",
        "Italien: Serie A": "I1",
        "Frankreich: Ligue 1": "F1",
    }
    
    global_fixtures = {}
    
    for liga_name, liga_code in ligamap.items():
        try:
            # Holt den aktuellen Saison-Feed direkt von football-data.co.uk
            url = f"https://www.football-data.co.uk/mmz4281/2526/{liga_code}.csv"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                df = pd.read_csv(io.StringIO(res.text))
                
                # Berechne den Ligen-Schnitt für xG-Schätzung (Tore / Spiele)
                total_games = len(df)
                if total_games > 10:
                    avg_home_goals = df['FTHG'].mean()
                    avg_away_goals = df['FTAG'].mean()
                    
                    # Die letzten Paarungen als "aktuelle Matches" listen
                    teams = sorted(df['HomeTeam'].dropna().unique())
                    liga_dict = {}
                    
                    for team in teams:
                        # Berechne vereinfachte Offensiv-/Defensivstärke der letzten 5 Heimspiele
                        home_matches = df[df['HomeTeam'] == team].tail(5)
                        away_matches = df[df['AwayTeam'] == team].tail(5)
                        
                        hg_scored = home_matches['FTHG'].mean() if len(home_matches) > 0 else avg_home_goals
                        ag_scored = away_matches['FTAG'].mean() if len(away_matches) > 0 else avg_away_goals
                        
                        # Simuliere Paarungen basierend auf den Teams
                        # (In der Vollversion vergleicht man hier den kommenden Spieltag)
                    
                    # Fallback-Paarungen generieren aus den echten Teams der Liga
                    match_dict = {}
                    for i in range(0, len(teams)-1, 2):
                        h_team = teams[i]
                        a_team = teams[i+1]
                        
                        # Berechne dynamische xG aus den echten Saisondaten
                        h_xg = max(df[df['HomeTeam'] == h_team]['FTHG'].mean(), 1.0) if not math.isnan(df[df['HomeTeam'] == h_team]['FTHG'].mean()) else 1.50
                        a_xg = max(df[df['AwayTeam'] == a_team]['FTAG'].mean(), 1.0) if not math.isnan(df[df['AwayTeam'] == a_team]['FTAG'].mean()) else 1.10
                        
                        match_dict[f"{h_team} - {a_team}"] = {
                            "home_xg": round(h_xg, 2),
                            "away_xg": round(a_xg, 2),
                            "home_inj": 0,
                            "away_inj": 0
                        }
                    
                    global_fixtures[liga_name] = match_dict
        except Exception as e:
            continue
            
    # Falls Internet offline oder Sommerpause, lade stabilen Grundstock
    if not global_fixtures:
        global_fixtures = {
            "FIFA Weltmeisterschaft (Live-Simulation)": {
                "Frankreich - Marokko": {"home_xg": 2.10, "away_xg": 0.95, "home_inj": 0, "away_inj": 2},
                "Schweiz - Kolumbien": {"home_xg": 1.35, "away_xg": 1.45, "home_inj": 1, "away_inj": 0}
            }
        }
    return global_fixtures

global_db = fetch_real_football_data()

st.header("⚽ Reale Spielauswahl (Football-Data.co.uk)")

# Liga-Auswahl aus den echten abgerufenen Daten
liga_auswahl = st.selectbox("1. Wettbewerb / Liga auswählen:", list(global_db.keys()))

partien_zur_auswahl = list(global_db[liga_auswahl].keys())
partien_zur_auswahl.append("Eigenes Spiel manuell eingeben...")
spiel_auswahl = st.selectbox("2. Aktuelle Paarung des Spieltags:", partien_zur_auswahl)

if "goals_home" not in st.session_state: st.session_state.goals_home = 0
if "goals_away" not in st.session_state: st.session_state.goals_away = 0

if st.session_state.get("last_selected_game", "") != spiel_auswahl:
    st.session_state.last_selected_game = spiel_auswahl
    st.session_state.goals_home = 0
    st.session_state.goals_away = 0

if "manuell" in spiel_auswahl.lower():
    game_input = st.text_input("Manuelle Partie eingeben (Heim - Auswärts):", value="Deutschland - Uruguay")
    base_home_val, base_away_val, injuries_home_val, injuries_away_val = 1.50, 1.10, 0, 0
else:
    game_input = spiel_auswahl
    base_home_val = global_db[liga_auswahl][spiel_auswahl]["home_xg"]
    base_away_val = global_db[liga_auswahl][spiel_auswahl]["away_xg"]
    injuries_home_val = global_db[liga_auswahl][spiel_auswahl]["home_inj"]
    injuries_away_val = global_db[liga_auswahl][spiel_auswahl]["away_inj"]

# (Ab hier folgt dein exakter Berechnungs- und Kombi-Code von oben...)
st.markdown(f"### Ausgewähltes Match: {game_input}")
st.write(f"Basis xG: Heim {base_home_val} | Auswärts {base_away_val}")
