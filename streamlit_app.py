import streamlit as st
import pandas as pd
import numpy as np
import math
import datetime

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

st.title("📊 Sven's 8-Pillar Live-Betting Algorithm")

# ⚙️ SYSTEMEINSTELLUNGEN
st.sidebar.header("⚙️ Systemeinstellungen")
modus = st.sidebar.radio("Modus auswählen:", ["Herren-Fußball (Regulär)", "Frauen-Fußball (Strenges Overlay)"])

# ⏰ ZEITZONEN-KORREKTUR (Holt den Server-Rückstand auf)
st.sidebar.subheader("⏰ Zeitzonen-Korrektur")
zeit_offset_stunden = st.sidebar.slider("Server-Zeitkorrektur (Stunden)", -5, 5, 2, help="Fügt Stunden hinzu, wenn der Server im Rückstand ist.")

st.sidebar.subheader("💰 Bankrolls pro Konto")
bankroll_betano = st.sidebar.number_input("Betano Guthaben (€)", min_value=0.0, value=26.21, step=5.0)
bankroll_interwetten = st.sidebar.number_input("Interwetten Guthaben (€)", min_value=0.0, value=16.03, step=5.0)
bankroll_winamax = st.sidebar.number_input("Winamax Guthaben (€)", min_value=0.0, value=16.88, step=5.0)

bankrolls = {'Betano': bankroll_betano, 'Interwetten': bankroll_interwetten, 'Winamax': bankroll_winamax}

is_womens_football = (modus == "Frauen-Fußball (Strenges Overlay)")
min_value_margin = 0.15 if is_womens_football else 0.05
kelly_fraction = 0.10 if is_womens_football else 0.25
max_cap = 0.03 if is_womens_football else 0.05

# ⚽ LIVE-SPIELPLAN & ZEITANALYSE
st.header("⚽ Live-Spielplan & Echtzeit-Zeitanalyse")

# Berechne die korrigierte Live-Zeit (holt die 2 fehlenden Stunden vom Server auf)
basis_zeit = datetime.datetime.now()
jetzt = basis_zeit + datetime.timedelta(hours=zeit_offset_stunden)

st.write(f"🖥️ *Server-Zeit (im Rückstand):* {basis_zeit.strftime('%H:%M:%S')} | 🎯 *Deine echte Live-Zeit:* **{jetzt.strftime('%H:%M:%S')}**")

ligen_datenbank = {
    "FIFA Weltmeisterschaft 2026": {
        "Schweiz - Kolumbien": {"home_xg": 1.35, "away_xg": 1.45, "home_inj": 1, "away_inj": 0, "anstoss_stunde": 22, "anstoss_minute": 0},
        "Frankreich - Marokko": {"home_xg": 2.10, "away_xg": 0.95, "home_inj": 0, "away_inj": 2, "anstoss_stunde": 22, "anstoss_minute": 0},
        "Eigenes Spiel manuell eingeben...": {"home_xg": 1.50, "away_xg": 1.10, "home_inj": 0, "away_inj": 0, "anstoss_stunde": 0, "anstoss_minute": 0}
    },
    "Skandinavien & Sommer-Ligen": {
        "Molde FK - Bodø/Glimt": {"home_xg": 1.85, "away_xg": 1.65, "home_inj": 2, "away_inj": 1, "anstoss_stunde": 18, "anstoss_minute": 0},
        "Malmö FF - Djurgårdens IF": {"home_xg": 1.90, "away_xg": 1.20, "home_inj": 1, "away_inj": 0, "anstoss_stunde": 19, "anstoss_minute": 0},
        "Eigenes Spiel manuell eingeben...": {"home_xg": 1.50, "away_xg": 1.10, "home_inj": 0, "away_inj": 0, "anstoss_stunde": 0, "anstoss_minute": 0}
    }
}

liga_auswahl = st.selectbox("1. Wähle die Liga / den Wettbewerb aus:", list(ligen_datenbank.keys()))
partien_zur_auswahl = list(ligen_datenbank[liga_auswahl].keys())
spiel_auswahl = st.selectbox("2. Wähle die aktuelle Partie aus:", partien_zur_auswahl)

if "goals_home" not in st.session_state: st.session_state.goals_home = 0
if "goals_away" not in st.session_state: st.session_state.goals_away = 0
if "last_selected_game" not in st.session_state or st.session_state.last_selected_game != spiel_auswahl:
    st.session_state.last_selected_game = spiel_auswahl
    st.session_state.goals_home = 0
    st.session_state.goals_away = 0

if spiel_auswahl == "Eigenes Spiel manuell eingeben...":
    liga_name = liga_auswahl
    game_input = st.text_input("Manuelle Partie eingeben:", value="Deutschland - Uruguay")
    base_home_val, base_away_val, injuries_home_val, injuries_away_val = 1.50, 1.10, 0, 0
    berechnete_minute = 0
else:
    liga_name = liga_auswahl
    game_input = spiel_auswahl
    base_home_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["home_xg"]
    base_away_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["away_xg"]
    injuries_home_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["home_inj"]
    injuries_away_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["away_inj"]
    
    stunde = ligen_datenbank[liga_auswahl][spiel_auswahl]["anstoss_stunde"]
    minute = ligen_datenbank[liga_auswahl][spiel_auswahl]["anstoss_minute"]
    
    anstoss_zeit = jetzt.replace(hour=stunde, minute=minute, second=0, microsecond=0)
    
    if jetzt >= anstoss_zeit:
        vergangene_minuten = int((jetzt - anstoss_zeit).total_seconds() / 60)
        if vergangene_minuten > 45:
            # Zieht 15 Minuten Pause ab
            berechnete_minute = min(vergangene_minuten - 15, 90)
        else:
            berechnete_minute = max(vergangene_minuten, 0)
    else:
        berechnete_minute = 0

# ⏱️ LIVE-TRACKER INTERFACE
st.markdown("---")
st.subheader("⏱️ Live-Spielstand-Tracker")

c_min, c_gh, c_ga = st.columns(3)
with c_min:
    live_minute = st.number_input("Aktuelle Spielminute:", min_value=0, max_value=90, value=berechnete_minute)
with c_gh:
    st.write("Tore HEIM")
    if st.button("➕ Tor Heim", key="h_plus"): st.session_state.goals_home += 1
    if st.button("➖ Tor Heim", key="h_minus") and st.session_state.goals_home > 0: st.session_state.goals_home -= 1
    st.markdown(f"### **{st.session_state.goals_home}**")
with c_ga:
    st.write("Tore AUSWÄRTS")
    if st.button("➕ Tor Auswärts", key="a_plus"): st.session_state.goals_away += 1
    if st.button("➖ Tor Auswärts", key="a_minus") and st.session_state.goals_away > 0: st.session_state.goals_away -= 1
    st.markdown(f"### **{st.session_state.goals_away}**")

# Adaptive Säulen-Anpassung der Tor-Erwartung
gesamttore_aktuell = st.session_state.goals_home + st.session_state.goals_away
restzeit_anteil = max((90.0 - live_minute) / 90.0, 0.0)

if live_minute > 25 and gesamttore_aktuell == 0:
    taktik_malus = max(1.0 - (live_minute / 180.0), 0.75)
    base_home_val *= taktik_malus
    base_away_val *= taktik_malus
elif gesamttore_aktuell > 0:
    base_home_val *= 1.10
    base_away_val *= 1.10

# 8-Säulen Ausfall-Dämpfung
exp_home_pre = max(base_home_val * (1.0 - (injuries_home_val * 0.08)), 0.1)
exp_away_pre = max(base_away_val * (1.0 - (injuries_away_val * 0.08)), 0.1)

live_exp_home_calc = round(exp_home_pre * restzeit_anteil, 2)
live_exp_away_calc = round(exp_away_pre * restzeit_anteil, 2)

st.markdown("---")
st.subheader(f"📋 Berechnete Live-Erwartungswerte (Restzeit: {int(restzeit_anteil*100)}%)")

col1, col2 = st.columns(2)
with col1:
    exp_home_live = st.slider("Aktuelle Rest-Tor-Erwartung (Heim)", 0.0, 4.0, live_exp_home_calc, 0.05)
with col2:
    exp_away_live = st.slider("Aktuelle Rest-Tor-Erwartung (Auswärts)", 0.0, 4.0, live_exp_away_calc, 0.05)

def poisson_pmf(k, lamb):
    if lamb == 0 and k == 0: return 1.0
    if lamb == 0 and k > 0: return 0.0
    return (lamb ** k * math.exp(-lamb)) / math.factorial(k)

prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
prob_btts_yes, prob_under_25 = 0.0, 0.0

for x in range(0, 11):
    for y in range(0, 11):
        p = poisson_pmf(x, exp_home_live) * poisson_pmf(y, exp_away_live)
        end_home = st.session_state.goals_home + x
        end_away = st.session_state.goals_away + y
        
        if end_home > end_away: prob_home += p
        elif end_home == end_away: prob_draw += p
        else: prob_away += p
        if end_home > 0 and end_away > 0: prob_btts_yes += p
        if (end_home + end_away) < 2.5: prob_under_25 += p

st.subheader("📊 Echtzeit Live-Wahrscheinlichkeiten")
heim_name = game_input.split('-')[0].strip() if '-' in game_input else 'Heim'
auswaerts_name = game_input.split('-')[1].strip() if '-' in game_input else 'Auswärts'

t1, t2 = st.columns(2)
with t1:
    st.write(f"Sieg **{heim_name}**: **{prob_home*100:.1f}%**")
    st.write(f"🤝 Unentschieden: **{prob_draw*100:.1f}%**")
    st.write(f"Sieg **{auswaerts_name}**: **{prob_away*100:.1f}%**")
with t2:
    st.write(f"Beide treffen (BTTS): **{prob_btts_yes*100:.1f}%**")
    st.write(f"Unter 2,5 Tore: **{prob_under_25*100:.1f}%** / Über 2,5: **{(1-prob_under_25)*100:.1f}%**")

# Live-Quoten Generierung
odds_1 = round((1.0 / (prob_home + 0.02)) * 0.95, 2) if prob_home > 0 else 99.0
odds_x = round((1.0 / (prob_draw + 0.02)) * 0.95, 2) if prob_draw > 0 else 99.0
odds_2 = round((1.0 / (prob_away + 0.02)) * 0.95, 2) if prob_away > 0 else 99.0
odds_u25 = round((1.0 / (prob_under_25 + 0.02)) * 0.95, 2) if prob_under_25 > 0 else 99.0

bookie_odds_all = {
    f'Sieg {heim_name} (1)': {'prob': prob_home, 'odds': odds_1, 'bookie': 'Winamax'},
    f'Sieg {auswaerts_name} (2)': {'prob': prob_away, 'odds': odds_2, 'bookie': 'Betano'},
    'Unentschieden (X)': {'prob': prob_draw, 'odds': odds_x, 'bookie': 'Interwetten'},
    'Unter 2,5 Tore': {'prob': prob_under_25, 'odds': odds_u25, 'bookie': 'Interwetten'}
}

max_value = -1.0
best_market = None
best_odds_val = 0.0
best_bookie_val = ""

for market, data in bookie_odds_all.items():
    value = (data['prob'] * data['odds']) - 1
    if value > max_value:
        max_value = value
        best_market = market
        best_odds_val = data['odds']
        best_bookie_val = data['bookie']

st.markdown("---")
st.subheader("🔥 Live-Wetten Tipp-Vorschlag")

if live_minute > 85:
    st.warning("⚠️ Ab Minute 85 wird kein neuer automatischer Tipp mehr empfohlen (Risiko-Overlay).")
elif max_value > min_value_margin:
    raw_kelly = max_value / (best_odds_val - 1) if best_odds_val > 1 else 0.0
    final_stake_pct = min(raw_kelly * kelly_fraction, max_cap)
    stake_euro = bankrolls[best_bookie_val] * final_stake_pct
    
    st.success(f"🎯 **LIVE-TIPP EMPFOHLEN:** Wette auf **{best_market}**")
    st.info(f"💵 **Einsatz:** {final_stake_pct*100:.2f}% vom **{best_bookie_val}**-Konto = **{stake_euro:.2f}€** (Live-Vorteil: +{max_value*100:.1f}%)")
else:
    st.error(f"❌ **KEIN LIVE-VALUE:** Der Markt bietet aktuell keinen ausreichenden Vorteil.")
