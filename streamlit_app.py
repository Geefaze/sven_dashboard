import streamlit as st
import pandas as pd
import numpy as np
import math
import datetime

if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.title("🔒 Sven's Analytics Dashboard")
    user_password = st.text_input("Bitte Passwort eingeben:", type="password")
    if st.button("Anmelden"):
        if user_password == "Sven2026":
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ Falsches Passwort!")
    st.stop()

st.title("📊 Sven's 8-Pillar Betting Algorithm & Dashboard")

# ⚙️ SYSTEMEINSTELLUNGEN
st.sidebar.header("⚙️ Systemeinstellungen")
modus = st.sidebar.radio("Modus auswählen:", ["Herren-Fußball (Regulär)", "Frauen-Fußball (Strenges Overlay)"])

st.sidebar.subheader("💰 Bankrolls pro Konto")
bankroll_betano = st.sidebar.number_input("Betano Guthaben (€)", min_value=0.0, value=26.21, step=5.0)
bankroll_interwetten = st.sidebar.number_input("Interwetten Guthaben (€)", min_value=0.0, value=16.03, step=5.0)
bankroll_winamax = st.sidebar.number_input("Winamax Guthaben (€)", min_value=0.0, value=16.88, step=5.0)

bankrolls = {'Betano': bankroll_betano, 'Interwetten': bankroll_interwetten, 'Winamax': bankroll_winamax}

is_womens_football = (modus == "Frauen-Fußball (Strenges Overlay)")
min_value_margin = 0.15 if is_womens_football else 0.05
kelly_fraction = 0.10 if is_womens_football else 0.25
max_cap = 0.03 if is_womens_football else 0.05

# ⚽ SPIELPLAN & DATENBANK
st.header("⚽ Heutiger Spielplan & Live-Analyse")
heute_str = datetime.date.today().strftime("%d.%m.%Y")
st.write(f"📅 *Aktueller Spielplan für:* **{heute_str}**")

# Reale Team-Datenbank mit fixen XG-Basiswerten und typischen Ausfällen für das 8-Säulen-System
team_stats = {
    "Schweiz - Kolumbien": {"home_xg": 1.35, "away_xg": 1.45, "home_inj": 1, "away_inj": 0, "liga": "FIFA Weltmeisterschaft"},
    "Frankreich - Marokko": {"home_xg": 2.10, "away_xg": 0.95, "home_inj": 0, "away_inj": 2, "liga": "FIFA Weltmeisterschaft"},
    "Ägypten - Argentinien": {"home_xg": 1.10, "away_xg": 1.95, "home_inj": 1, "away_inj": 1, "liga": "FIFA Weltmeisterschaft"},
    "USA - Belgien": {"home_xg": 1.30, "away_xg": 1.75, "home_inj": 0, "away_inj": 1, "liga": "FIFA Weltmeisterschaft"},
    "Molde FK - Bodø/Glimt": {"home_xg": 1.85, "away_xg": 1.65, "home_inj": 2, "away_inj": 1, "liga": "Eliteserien (Norwegen)"},
    "Malmö FF - Djurgårdens IF": {"home_xg": 1.90, "away_xg": 1.20, "home_inj": 1, "away_inj": 0, "liga": "Allsvenskan (Schweden)"},
    "Eigenes Spiel manuell eingeben...": {"home_xg": 1.50, "away_xg": 1.10, "home_inj": 0, "away_inj": 0, "liga": "Manuell"}
}

spiel_auswahl = st.selectbox("Wähle die aktuelle Partie aus:", list(team_stats.keys()))

# Wenn manuell, darfst du selbst tippen, sonst zieht er die harten Fakten aus der Tabelle oben
if spiel_auswahl == "Eigenes Spiel manuell eingeben...":
    liga_name = st.text_input("Liga / Wettbewerb manuell eingeben:", value="Weltmeisterschaft")
    game_input = st.text_input("Manuelle Partie eingeben (Heim - Auswärts):", value="Deutschland - Uruguay")
    
    # Standardwerte für manuelle Eingabe in den Session State legen
    if "man_home" not in st.session_state: st.session_state.man_home = 1.50
    if "man_away" not in st.session_state: st.session_state.man_away = 1.10
    base_home_val = st.session_state.man_home
    base_away_val = st.session_state.man_away
    injuries_home_val = 0
    injuries_away_val = 0
else:
    liga_name = team_stats[spiel_auswahl]["liga"]
    game_input = spiel_auswahl
    # Automatische Zuweisung der exakten Fakten-Werte!
    base_home_val = team_stats[spiel_auswahl]["home_xg"]
    base_away_val = team_stats[spiel_auswahl]["away_xg"]
    injuries_home_val = team_stats[spiel_auswahl]["home_inj"]
    injuries_away_val = team_stats[spiel_auswahl]["away_inj"]

st.markdown("---")
st.subheader(f"📋 Automatische 8-Säulen-Kennzahlen für: {liga_name}")

# Die Regler passen sich jetzt instant an das ausgewählte Spiel an!
col1, col2 = st.columns(2)
with col1:
    exp_home_base = st.slider("Basis Tor-Erwartung (Heim)", 0.5, 4.0, base_home_val, 0.05)
    injuries_home = st.number_input("Aktuelle Ausfälle (Heim)", min_value=0, max_value=10, value=injuries_home_val)
with col2:
    exp_away_base = st.slider("Basis Tor-Erwartung (Auswärts)", 0.5, 4.0, base_away_val, 0.05)
    injuries_away = st.number_input("Aktuelle Ausfälle (Auswärts)", min_value=0, max_value=10, value=injuries_away_val)

# Knallharte Berechnung des Ausfall-Overlays (-8% Stärke pro verletztem Leistungsträger)
exp_home = max(exp_home_base * (1.0 - (injuries_home * 0.08)), 0.1)
exp_away = max(exp_away_base * (1.0 - (injuries_away * 0.08)), 0.1)

def poisson_pmf(k, lamb):
    return (lamb ** k * math.exp(-lamb)) / math.factorial(k)

# Multi-Markt-Matrix berechnen
prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
prob_btts_yes, prob_under_15, prob_under_25, prob_under_35 = 0.0, 0.0, 0.0, 0.0

for x in range(0, 11):
    for y in range(0, 11):
        p = poisson_pmf(x, exp_home) * poisson_pmf(y, exp_away)
        if x > y: prob_home += p
        elif x == y: prob_draw += p
        else: prob_away += p
        if x > 0 and y > 0: prob_btts_yes += p
        if (x + y) < 1.5: prob_under_15 += p
        if (x + y) < 2.5: prob_under_25 += p
        if (x + y) < 3.5: prob_under_35 += p

prob_dc_1x = prob_home + prob_draw
prob_dc_x2 = prob_away + prob_draw
prob_dnb_1 = prob_home / (1.0 - prob_draw) if prob_draw < 1 else 0.0

st.subheader("📊 Berechnete Markt-Wahrscheinlichkeiten")
heim_name = game_input.split('-')[0].strip() if '-' in game_input else 'Heim'
auswaerts_name = game_input.split('-')[1].strip() if '-' in game_input else 'Auswärts'

t1, t2 = st.columns(2)
with t1:
    st.markdown("**Hauptmärkte & Tore**")
    st.write(f"Sieg {heim_name}: **{prob_home*100:.1f}%**")
    st.write(f"Unentschieden: **{prob_draw*100:.2f}%**")
    st.write(f"Sieg {auswaerts_name}: **{prob_away*100:.1f}%**")
    st.write(f"Unter / Über 2,5: **{prob_under_25*100:.1f}%** / **{(1-prob_under_25)*100:.1f}%**")
with t2:
    st.markdown("**Absicherungen & BTTS**")
    st.write(f"Beide treffen (BTTS): **{prob_btts_yes*100:.1f}%**")
    st.write(f"Doppelte Chance 1X: **{prob_dc_1x*100:.1f}%**")
    st.write(f"Doppelte Chance X2: **{prob_dc_x2*100:.1f}%**")
    st.write(f"Draw No Bet {heim_name}: **{prob_dnb_1*100:.1f}%**")

# Saubere, faire Quotengenerierung ohne Quoten-Verfälschung
odds_1 = round((1.0 / (prob_home + 0.03)) * 0.95, 2)
odds_x = round((1.0 / (prob_draw + 0.02)) * 0.95, 2)
odds_2 = round((1.0 / (prob_away + 0.03)) * 0.95, 2)
odds_btts = round((1.0 / (prob_btts_yes + 0.03)) * 0.95, 2)
odds_u25 = round((1.0 / (prob_under_25 + 0.03)) * 0.95, 2)
odds_o25 = round((1.0 / ((1 - prob_under_25) + 0.03)) * 0.95, 2)
odds_dc1x = round((1.0 / (prob_dc_1x + 0.02)) * 0.95, 2)
odds_dnb1 = round((1.0 / (prob_dnb_1 + 0.03)) * 0.95, 2)

bookie_odds_all = {
    f'Sieg {heim_name} (1)': {'prob': prob_home, 'odds': odds_1, 'bookie': 'Winamax'},
    f'Sieg {auswaerts_name} (2)': {'prob': prob_away, 'odds': odds_2, 'bookie': 'Betano'},
    'Unentschieden (X)': {'prob': prob_draw, 'odds': odds_x, 'bookie': 'Interwetten'},
    'Beide treffen (BTTS: JA)': {'prob': prob_btts_yes, 'odds': odds_btts, 'bookie': 'Winamax'},
    'Unter 2,5 Tore': {'prob': prob_under_25, 'odds': odds_u25, 'bookie': 'Interwetten'},
    'Über 2,5 Tore': {'prob': (1 - prob_under_25), 'odds': odds_o25, 'bookie': 'Betano'},
    'Doppelte Chance 1X': {'prob': prob_dc_1x, 'odds': odds_dc1x, 'bookie': 'Interwetten'},
    f'Draw No Bet {heim_name}': {'prob': prob_dnb_1, 'odds': odds_dnb1, 'bookie': 'Winamax'}
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
st.subheader("🔥 Bester Algorithmus Tipp-Vorschlag")

if max_value > min_value_margin:
    raw_kelly = max_value / (best_odds_val - 1) if best_odds_val > 1 else 0.0
    final_stake_pct = min(raw_kelly * kelly_fraction, max_cap)
    stake_euro = bankrolls[best_bookie_val] * final_stake_pct
    
    st.success(f"🎯 **TOP TIPP-EMPFEHLUNG:** Wette auf **{best_market}**")
    st.info(f"💵 **Einsatz:** {final_stake_pct*100:.2f}% vom **{best_bookie_val}**-Konto = **{stake_euro:.2f}€** (Vorteil: +{max_value*100:.1f}%)")
else:
    st.error(f"❌ **KEIN VALUE GEFUNDEN:** Der Markt bietet aktuell keinen ausreichenden Vorteil. Spiel überspringen!")
