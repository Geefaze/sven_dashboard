import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats

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
st.sidebar.header("⚙️ Systemeinstellungen")
bankroll = st.sidebar.number_input("Aktuelle Bankroll (€)", min_value=10.0, value=1500.0, step=50.0)
modus = st.sidebar.radio("Modus auswählen:", ["Herren-Fußball (Regulär)", "Frauen-Fußball (Strenges Overlay)"])

is_womens_football = (modus == "Frauen-Fußball (Strenges Overlay)")
min_value_margin = 0.15 if is_womens_football else 0.05
kelly_fraction = 0.10 if is_womens_football else 0.25
max_cap = 0.03 if is_womens_football else 0.05

st.header("⚽ Spiel-Analyse & Value-Finder")
col1, col2 = st.columns(2)
with col1:
    home_team = st.text_input("Heimteam", value="Frankreich")
    exp_home_base = st.slider("Basis Tor-Erwartung (Heim)", 0.5, 4.0, 1.75, 0.05)
    injuries_home = st.number_input("Ausfälle (Heim)", min_value=0, max_value=5, value=0)
with col2:
    away_team = st.text_input("Auswärtsteam", value="Marokko")
    exp_away_base = st.slider("Basis Tor-Erwartung (Auswärts)", 0.5, 4.0, 0.95, 0.05)
    injuries_away = st.number_input("Ausfälle (Auswärts)", min_value=0, max_value=5, value=2)

exp_home = max(exp_home_base * (1.0 - (injuries_home * 0.08)), 0.1)
exp_away = max(exp_away_base * (1.0 - (injuries_away * 0.08)), 0.1)

prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
for x in range(0, 11):
    for y in range(0, 11):
        p = stats.poisson.pmf(x, exp_home) * stats.poisson.pmf(y, exp_away)
        if x > y: prob_home += p
        elif x == y: prob_draw += p
        else: prob_away += p

st.subheader("📊 Berechnete Wahrscheinlichkeiten")
st.write(f"Sieg {home_team}: {prob_home*100:.2f}% | Unentschieden: {prob_draw*100:.2f}% | Sieg {away_team}: {prob_away*100:.2f}%")

st.subheader("💰 Quoten-Eingabe (Betano, Interwetten, Winamax)")
b_1 = st.number_input("Betano Quote 1", value=1.57)
i_x = st.number_input("Interwetten Quote X", value=4.10)
w_2 = st.number_input("Winamax Quote 2", value=6.40)

bookie_odds = {'Betano': {'1': b_1, 'X': 3.95, '2': 6.20}, 'Interwetten': {'1': 1.53, 'X': i_x, '2': 6.00}, 'Winamax': {'1': 1.65, 'X': 3.90, '2': w_2}}
outcomes, probs = ['1', 'X', '2'], [prob_home, prob_draw, prob_away]
max_value, best_bet, best_bookie, best_odds, best_prob = -1.0, None, None, 0.0, 0.0

for idx, outcome in enumerate(outcomes):
    my_prob = probs[idx]
    for bookie, odds_dict in bookie_odds.items():
        odds = odds_dict[outcome]
        value = (my_prob * odds) - 1
        if value > max_value:
            max_value, best_bet, best_bookie, best_odds, best_prob = value, outcome, bookie, odds, my_prob

if max_value > min_value_margin:
    raw_kelly = max_value / (best_odds - 1)
    final_stake_pct = min(raw_kelly * kelly_fraction, max_cap)
    st.success(f"🔥 VALUE GEFUNDEN! Tipp: {best_bet} bei [{best_bookie}] zu Quote {best_odds}. Einsatz: {final_stake_pct*100:.2f}% ({bankroll * final_stake_pct:.2f}€)")
else:
    st.error(f"❌ KEIN VALUE (Max Vorteil: +{max_value*100:.2f}%). Spiel aussortieren.")
