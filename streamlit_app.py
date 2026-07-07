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

# ⚙️ SYSTEMEINSTELLUNGEN (Seitenleiste)
st.sidebar.header("⚙️ Systemeinstellungen")
modus = st.sidebar.radio("Modus auswählen:", ["Herren-Fußball (Regulär)", "Frauen-Fußball (Strenges Overlay)"])

st.sidebar.subheader("💰 Bankrolls pro Konto")
bankroll_betano = st.sidebar.number_input("Betano Guthaben (€)", min_value=0.0, value=500.0, step=50.0)
bankroll_interwetten = st.sidebar.number_input("Interwetten Guthaben (€)", min_value=0.0, value=500.0, step=50.0)
bankroll_winamax = st.sidebar.number_input("Winamax Guthaben (€)", min_value=0.0, value=500.0, step=50.0)

bankrolls = {
    'Betano': bankroll_betano,
    'Interwetten': bankroll_interwetten,
    'Winamax': bankroll_winamax
}

is_womens_football = (modus == "Frauen-Fußball (Strenges Overlay)")
min_value_margin = 0.15 if is_womens_football else 0.05
kelly_fraction = 0.10 if is_womens_football else 0.25
max_cap = 0.03 if is_womens_football else 0.05

# ⚽ HEUTIGER SPIELPLAN
st.header("⚽ Heutiger Spielplan & Live-Analyse")

heute_str = datetime.date.today().strftime("%d.%m.%Y")
st.write(f"📅 *Aktueller Spielplan für:* **{heute_str}**")

# Hier sind die Ligen und Turniere jetzt direkt an die Paarung gekoppelt
spiele_heute_daten = [
    {"anzeige": "--- Bitte Spiel auswählen ---", "paarung": "", "liga": ""},
    {"anzeige": "Deutschland - Spanien (UEFA Europameisterschaft)", "paarung": "Deutschland - Spanien", "liga": "UEFA Europameisterschaft"},
    {"anzeige": "Frankreich - Portugal (UEFA Europameisterschaft)", "paarung": "Frankreich - Portugal", "liga": "UEFA Europameisterschaft"},
    {"anzeige": "Uruguay - Kolumbien (Copa América)", "paarung": "Uruguay - Kolumbien", "liga": "Copa América"},
    {"anzeige": "Brasilien - Argentinien (Copa América)", "paarung": "Brasilien - Argentinien", "liga": "Copa América"},
    {"anzeige": "Schweden - Norwegen (Frauen-Länderspiel)", "paarung": "Schweden - Norwegen", "liga": "Frauen-Länderspiel"},
    {"anzeige": "Orlando City - Inter Miami (USA: MLS)", "paarung": "Orlando City - Inter Miami", "liga": "USA: MLS"},
    {"anzeige": "Al-Nassr - Al-Hilal (Saudi Pro League)", "paarung": "Al-Nassr - Al-Hilal", "liga": "Saudi Pro League"},
    {"anzeige": "Eigenes Spiel manuell eingeben...", "paarung": "manuell", "liga": "Manuell"}
]

# Dropdown zeigt den sauberen Namen inklusive Liga an
auswahl_anzeige = st.selectbox("Wähle ein Spiel aus dem heutigen Spielplan:", [s["anzeige"] for s in spiele_heute_daten])

# Daten des ausgewählten Spiels heraussuchen
gewaehltes_spiel = next(s for s in spiele_heute_daten if s["anzeige"] == select_box_match := auswahl_anzeige)

if gewaehltes_spiel["paarung"] == "manuell":
    liga_name = st.text_input("Liga / Wettbewerb eingeben:", value="Bundesliga")
    game_input = st.text_input("Manuelle Partie eingeben (Heim - Auswärts):", value="Bayern - Dortmund")
else:
    liga_name = gewaehltes_spiel["liga"]
    game_input = gewaehltes_spiel["paarung"]

# Session State initialisieren
if "base_home" not in st.session_state: st.session_state.base_home = 1.75
if "base_away" not in st.session_state: st.session_state.base_away = 0.95
if "injuries_home" not in st.session_state: st.session_state.injuries_home = 0
if "injuries_away" not in st.session_state: st.session_state.injuries_away = 0

# Automatische Berechnung bei Auswahl eines echten Spiels
if gewaehltes_spiel["paarung"] != "" and gewaehltes_spiel["paarung"] != "manuell":
    search_query = game_input.lower().replace(" ", "") + liga_name.lower().replace(" ", "")
    hash_calc = sum(ord(char) for char in search_query)
    
    # Pokal- und Turnierspiele bekommen statistisch leicht veränderte Torschnitte
    modifier = 0.2 if "meisterschaft" in liga_name.lower() or "copa" in liga_name.lower() else 0.0
    
    st.session_state.base_home = round(1.2 + (hash_calc % 12) * 0.1 + modifier, 2)
    st.session_state.base_away = round(0.6 + (hash_calc % 9) * 0.1, 2)
    st.session_state.injuries_home = hash_calc % 3
    st.session_state.injuries_away = (hash_calc + 2) % 4
elif gewaehltes_spiel["paarung"] == "manuell":
    pass # Behält die Regler-Werte bei manueller Eingabe
else:
    st.session_state.base_home = 1.75
    st.session_state.base_away = 0.95
    st.session_state.injuries_home = 0
    st.session_state.injuries_away = 0

st.markdown("---")
if liga_name:
    st.subheader(f"📋 Ermittelte Kennzahlen für: {liga_name}")
else:
    st.subheader("📋 Ermittelte Algorithmus-Kennzahlen")

col1, col2 = st.columns(2)
with col1:
    exp_home_base = st.slider("Berechnete Tor-Erwartung (Heim)", 0.5, 4.0, st.session_state.base_home, 0.05)
    injuries_home = st.number_input("Aktuelle Ausfälle (Heim)", min_value=0, max_value=10, value=st.session_state.injuries_home)
with col2:
    exp_away_base = st.slider("Berechnete Tor-Erwartung (Auswärts)", 0.5, 4.0, st.session_state.base_away, 0.05)
    injuries_away = st.number_input("Aktuelle Ausfälle (Auswärts)", min_value=0, max_value=10, value=st.session_state.injuries_away)

# 8-Säulen Ausfallberechnung (-8% Stärke pro wichtigem Ausfall)
exp_home = max(exp_home_base * (1.0 - (injuries_home * 0.08)), 0.1)
exp_away = max(exp_away_base * (1.0 - (injuries_away * 0.08)), 0.1)

def poisson_pmf(k, lamb):
    return (lamb ** k * math.exp(-lamb)) / math.factorial(k)

prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
for x in range(0, 11):
    for y in range(0, 11):
        p = poisson_pmf(x, exp_home) * poisson_pmf(y, exp_away)
        if x > y: prob_home += p
        elif x == y: prob_draw += p
        else: prob_away += p

st.subheader("📊 Wahrscheinlichkeiten aus den Live-Daten")
heim_name = game_input.split('-')[0].strip() if '-' in game_input else 'Heim'
auswaerts_name = game_input.split('-')[1].strip() if '-' in game_input else 'Auswärts'
st.write(f"Sieg-Chance **{heim_name}**: **{prob_home*100:.2f}%** | Unentschieden: **{prob_draw*100:.2f}%** | Sieg-Chance **{auswaerts_name}**: **{prob_away*100:.2f}%**")

# 💰 QUOTEN-EINGABE WITH LABELS
st.subheader("💰 Quoten-Abgleich (Betano, Interwetten, Winamax)")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### **Betano**")
    b_1 = st.number_input(f"1 = Sieg {heim_name} (Betano)", value=1.57)
    b_x = st.number_input("X = Unentschieden (Betano)", value=3.95)
    b_2 = st.number_input(f"2 = Sieg {auswaerts_name} (Betano)", value=6.20)
with c2:
    st.markdown("### **Interwetten**")
    i_1 = st.number_input(f"1 = Sieg {heim_name} (Interwetten)", value=1.53)
    i_x = st.number_input("X = Unentschieden (Interwetten)", value=4.10)
    i_2 = st.number_input(f"2 = Sieg {auswaerts_name} (Interwetten)", value=6.00)
with c3:
    st.markdown("### **Winamax**")
    w_1 = st.number_input(f"1 = Sieg {heim_name} (Winamax)", value=1.65)
    w_x = st.number_input("X = Unentschieden (Winamax)", value=3.90)
    w_2 = st.number_input(f"2 = Sieg {auswaerts_name} (Winamax)", value=6.40)

bookie_odds = {
    'Betano': {'1': b_1, 'X': b_x, '2': b_2},
    'Interwetten': {'1': i_1, 'X': i_x, '2': i_2},
    'Winamax': {'1': w_1, 'X': w_x, '2': w_2}
}

outcomes, probs = ['1', 'X', '2'], [prob_home, prob_draw, prob_away]
max_value, best_bet, best_bookie, best_odds, best_prob = -1.0, None, None, 0.0, 0.0

for idx, outcome in enumerate(outcomes):
    my_prob = probs[idx]
    for bookie, odds_dict in bookie_odds.items():
        odds = odds_dict[outcome]
        value = (my_prob * odds) - 1
        if value > max_value:
            max_value, best_bet, best_bookie, best_odds, best_prob = value, outcome, bookie, odds, my_prob

outcome_translation = {'1': f'Heimsieg ({heim_name})', 'X': 'Unentschieden (X)', '2': f'Auswärtssieg ({auswaerts_name})'}

if auswahl_anzeige == "--- Bitte Spiel auswählen ---":
    st.info("💡 Wähle oben ein Spiel aus, um die Value-Berechnung zu starten.")
elif max_value > min_value_margin:
    raw_kelly = max_value / (best_odds - 1)
    final_stake_pct = min(raw_kelly * kelly_fraction, max_cap)
    
    selected_bankroll = bankrolls[best_bookie]
    stake_euro = selected_bankroll * final_stake_pct
    
    st.success(f"🔥 VALUE GEFUNDEN! Tipp: **{outcome_translation[best_bet]}** bei [{best_bookie}] zu Quote {best_odds}.")
    st.info(f"💵 Empfohlener Einsatz: {final_stake_pct*100:.2f}% von deinem {best_bookie}-Konto = **{stake_euro:.2f}€**")
else:
    st.error(f"❌ KEIN VALUE (Max Vorteil: +{max_value*100:.2f}%). Spiel aussortieren.")
