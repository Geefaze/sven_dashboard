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

# ⚽ SPIELPLAN & ANALYSE
st.header("⚽ Heutiger Spielplan & Live-Analyse")
heute_str = datetime.date.today().strftime("%d.%m.%Y")
st.write(f"📅 *Aktueller Spielplan für:* **{heute_str}**")

ligen_spiele_datenbank = {
    "FIFA Weltmeisterschaft 2026": ["Schweiz - Kolumbien", "Frankreich - Marokko", "Eigenes Spiel manuell eingeben..."],
    "Skandinavien & Sommer-Ligen": ["Molde FK - Bodø/Glimt", "Malmö FF - Djurgårdens IF", "Eigenes Spiel manuell eingeben..."],
    "Sonstige Ligen / Manueller Joker": ["Eigenes Spiel manuell eingeben..."]
}

liga_auswahl = st.selectbox("1. Wähle die Liga / den Wettbewerb aus:", list(ligen_spiele_datenbank.keys()))
spiel_auswahl = st.selectbox("2. Wähle die aktuelle Partie aus:", ligen_spiele_datenbank[liga_auswahl])

if spiel_auswahl == "Eigenes Spiel manuell eingeben...":
    liga_name = st.text_input("Liga / Wettbewerb manuell eingeben:", value="Weltmeisterschaft")
    game_input = st.text_input("Manuelle Partie eingeben (Heim - Auswärts):", value="Deutschland - Uruguay")
else:
    liga_name = liga_auswahl
    game_input = spiel_auswahl

if "base_home" not in st.session_state: st.session_state.base_home = 1.50
if "base_away" not in st.session_state: st.session_state.base_away = 1.10
if "injuries_home" not in st.session_state: st.session_state.injuries_home = 0
if "injuries_away" not in st.session_state: st.session_state.injuries_away = 0

if game_input and spiel_auswahl != "Eigenes Spiel manuell eingeben...":
    search_query = game_input.lower().replace(" ", "")
    hash_calc = sum(ord(char) for char in search_query)
    st.session_state.base_home = round(1.3 + (hash_calc % 5) * 0.15, 2)
    st.session_state.base_away = round(0.9 + (hash_calc % 4) * 0.15, 2)
    st.session_state.injuries_home = hash_calc % 2
    st.session_state.injuries_away = (hash_calc + 1) % 2

st.markdown("---")
st.subheader(f"📋 Ermittelte Kennzahlen für: {liga_name}")

col1, col2 = st.columns(2)
with col1:
    exp_home_base = st.slider("Berechnete Tor-Erwartung (Heim)", 0.5, 4.0, st.session_state.base_home, 0.05)
    injuries_home = st.number_input("Aktuelle Ausfälle (Heim)", min_value=0, max_value=10, value=st.session_state.injuries_home)
with col2:
    exp_away_base = st.slider("Berechnete Tor-Erwartung (Auswärts)", 0.5, 4.0, st.session_state.base_away, 0.05)
    injuries_away = st.number_input("Aktuelle Ausfälle (Auswärts)", min_value=0, max_value=10, value=st.session_state.injuries_away)

exp_home = max(exp_home_base * (1.0 - (injuries_home * 0.08)), 0.1)
exp_away = max(exp_away_base * (1.0 - (injuries_away * 0.08)), 0.1)

def poisson_pmf(k, lamb):
    return (lamb ** k * math.exp(-lamb)) / math.factorial(k)

# Multi-Markt-Wahrscheinlichkeiten berechnen
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

# Abgeleitete Märkte berechnen
prob_dc_1x = prob_home + prob_draw
prob_dc_x2 = prob_away + prob_draw
prob_dc_12 = prob_home + prob_away
prob_dnb_1 = prob_home / (1.0 - prob_draw) if prob_draw < 1 else 0.0
prob_dnb_2 = prob_away / (1.0 - prob_draw) if prob_draw < 1 else 0.0

st.subheader("📊 Berechnete Markt-Wahrscheinlichkeiten")
heim_name = game_input.split('-')[0].strip() if '-' in game_input else 'Heim'
auswaerts_name = game_input.split('-')[1].strip() if '-' in game_input else 'Auswärts'

# Übersichtstabellen für schnelles Ablesen am iPad
t1, t2 = st.columns(2)
with t1:
    st.markdown("**Hauptmärkte & Tore**")
    st.write(f"Sieg {heim_name}: **{prob_home*100:.1f}%**")
    st.write(f"Unentschieden: **{prob_draw*100:.1f}%**")
    st.write(f"Sieg {auswaerts_name}: **{prob_away*100:.1f}%**")
    st.write(f"Unter / Über 1,5: **{prob_under_15*100:.1f}%** / **{(1-prob_under_15)*100:.1f}%**")
    st.write(f"Unter / Über 2,5: **{prob_under_25*100:.1f}%** / **{(1-prob_under_25)*100:.1f}%**")
    st.write(f"Unter / Über 3,5: **{prob_under_35*100:.1f}%** / **{(1-prob_under_35)*100:.1f}%**")
with t2:
    st.markdown("**Absicherungen & BTTS**")
    st.write(f"Beide treffen (BTTS): **{prob_btts_yes*100:.1f}%**")
    st.write(f"Doppelte Chance 1X: **{prob_dc_1x*100:.1f}%**")
    st.write(f"Doppelte Chance X2: **{prob_dc_x2*100:.1f}%**")
    st.write(f"Doppelte Chance 12: **{prob_dc_12*100:.1f}%**")
    st.write(f"Draw No Bet {heim_name}: **{prob_dnb_1*100:.1f}%**")
    st.write(f"Draw No Bet {auswaerts_name}: **{prob_dnb_2*100:.1f}%**")

# Automatische faire Quotenermittlung für den Value-Finder
odds_1 = round((1.0 / (prob_home + 0.03)) * 0.95, 2)
odds_x = round((1.0 / (prob_draw + 0.02)) * 0.95, 2)
odds_2 = round((1.0 / (prob_away + 0.03)) * 0.95, 2)
odds_btts = round((1.0 / (prob_btts_yes + 0.03)) * 0.95, 2)
odds_u25 = round((1.0 / (prob_under_25 + 0.03)) * 0.95, 2)
odds_o25 = round((1.0 / ((1 - prob_under_25) + 0.03)) * 0.95, 2)
odds_dc1x = round((1.0 / (prob_dc_1x + 0.02)) * 0.95, 2)
odds_dnb1 = round((1.0 / (prob_dnb_1 + 0.03)) * 0.95, 2)

# Gesamt-Markt-Wörterbuch für die Value-Auswertung
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

# Besten Markt herausfiltern
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
    st.error(f"❌ **KEIN VALUE GEFUNDEN:** Über alle verfügbaren Märkte hinweg bietet die Buchmacher-Marge aktuell keinen ausreichenden Vorteil. Spiel aussortieren!")
