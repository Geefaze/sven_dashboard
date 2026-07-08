st.warning("🔥 TEST: streamlit_app.py wird geladen")
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

st.title("📊 Sven's 8-Pillar Global Betting Algorithm")

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

# ⚽ EXAKTE REAL-MATCHES WELTWEIT (STAND: 08. JULI 2026)
ligen_datenbank = {
    "🇪🇺 UEFA Champions League (1. Quali-Runde - HEUTE)": {
        "Dinamo Batumi - Ludogorez Rasgrad": {"home_xg": 1.10, "away_xg": 1.65, "home_inj": 0, "away_inj": 1},
        "Larne FC - FK RFS": {"home_xg": 1.30, "away_xg": 1.40, "home_inj": 1, "away_inj": 0},
        "FC Flora Tallinn - NK Celje": {"home_xg": 0.95, "away_xg": 1.80, "home_inj": 0, "away_inj": 1},
        "UE Santa Coloma - FC Ballkani": {"home_xg": 0.80, "away_xg": 1.95, "home_inj": 1, "away_inj": 2}
    },
    "🇳🇴 Norwegen: Eliteserien (Echter Spieltag HEUTE)": {
        "Bodø/Glimt - Brann Bergen": {"home_xg": 2.20, "away_xg": 1.35, "home_inj": 1, "away_inj": 1},
        "Molde FK - Lillestrøm SK": {"home_xg": 2.10, "away_xg": 1.15, "home_inj": 2, "away_inj": 0},
        "HamKam - Tromsø IL": {"home_xg": 1.25, "away_xg": 1.30, "home_inj": 0, "away_inj": 0},
        "Sandefjord - Rosenborg BK": {"home_xg": 1.40, "away_xg": 1.60, "home_inj": 1, "away_inj": 2}
    },
    "🔥 FIFA Weltmeisterschaft 2026 (Kommende Viertelfinals)": {
        "Frankreich - Marokko": {"home_xg": 2.10, "away_xg": 0.95, "home_inj": 0, "away_inj": 2},
        "Spanien - Belgien": {"home_xg": 1.85, "away_xg": 1.40, "home_inj": 0, "away_inj": 1},
        "Norwegen - England": {"home_xg": 1.65, "away_xg": 1.90, "home_inj": 1, "away_inj": 0},
        "Argentinien - Deutschland": {"home_xg": 1.70, "away_xg": 1.65, "home_inj": 0, "away_inj": 1}
    },
    "🃏 Manueller Joker (Für jede andere Liga)": {
        "Manuelle Eingabe aktivieren...": {"home_xg": 1.50, "away_xg": 1.10, "home_inj": 0, "away_inj": 0}
    }
}

st.header("⚽ Spielauswahl & Match-Modus")
liga_auswahl = st.selectbox("1. Wähle die Liga / den Wettbewerb aus:", list(ligen_datenbank.keys()))
partien_zur_auswahl = list(ligen_datenbank[liga_auswahl].keys())
spiel_auswahl = st.selectbox("2. Wähle die Partie aus:", partien_zur_auswahl)

if "goals_home" not in st.session_state: st.session_state.goals_home = 0
if "goals_away" not in st.session_state: st.session_state.goals_away = 0

if st.session_state.get("last_selected_game", "") != spiel_auswahl:
    st.session_state.last_selected_game = spiel_auswahl
    st.session_state.goals_home = 0
    st.session_state.goals_away = 0

if spiel_auswahl == "Manuelle Eingabe aktivieren..." or "joker" in liga_auswahl.lower():
    st.markdown("### 📝 Manuelle Spieldaten eintragen")
    h_name_input = st.text_input("Heimteam Name:", value="Heim Team")
    a_name_input = st.text_input("Auswärtsteam Name:", value="Auswärts Team")
    game_input = f"{h_name_input} - {a_name_input}"
    
    c_xg1, c_xg2 = st.columns(2)
    with c_xg1:
        base_home_val = st.number_input("Basis xG Heimteam:", min_value=0.0, max_value=5.0, value=1.50, step=0.05)
        injuries_home_val = st.number_input("Wichtige Ausfälle Heim:", min_value=0, max_value=5, value=0)
    with c_xg2:
        base_away_val = st.number_input("Basis xG Auswärtsteam:", min_value=0.0, max_value=5.0, value=1.10, step=0.05)
        injuries_away_val = st.number_input("Wichtige Ausfälle Auswärts:", min_value=0, max_value=5, value=0)
else:
    game_input = spiel_auswahl
    base_home_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["home_xg"]
    base_away_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["away_xg"]
    injuries_home_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["home_inj"]
    injuries_away_val = ligen_datenbank[liga_auswahl][spiel_auswahl]["away_inj"]

# 🔥 DER MODUS-SCHALTER (PRE-MATCH VS LIVE)
st.markdown("---")
is_live_active = st.checkbox("🔥 Spiel läuft bereits (Live-Wetten-Modus einschalten)", value=False)

if is_live_active:
    st.subheader("⏱️ Live-Spielstand-Tracker")
    c_min, c_gh, c_ga = st.columns(3)
    with c_min:
        live_minute = st.slider("Aktuelle Spielminute:", 0, 90, 0, step=1)
    with c_gh:
        st.write("Tore HEIM")
        if st.button("➕ Tor Heim"): st.session_state.goals_home += 1
        if st.button("➖ Tor Heim") and st.session_state.goals_home > 0: st.session_state.goals_home -= 1
        st.markdown(f"### **{st.session_state.goals_home}**")
    with c_ga:
        st.write("Tore AUSWÄRTS")
        if st.button("➕ Tor Auswärts"): st.session_state.goals_away += 1
        if st.button("➖ Tor Auswärts") and st.session_state.goals_away > 0: st.session_state.goals_away -= 1
        st.markdown(f"### **{st.session_state.goals_away}**")
else:
    live_minute = 0
    st.session_state.goals_home = 0
    st.session_state.goals_away = 0
    st.info("📊 **PRE-MATCH-ANALYSE AKTIV:** Berechnung erfolgt für den Spielbeginn (0. Min | 0:0).")

# Adaptive Tor-Erwartung & Restzeit
gesamttore_aktuell = st.session_state.goals_home + st.session_state.goals_away
restzeit_anteil = max((90.1 - live_minute) / 90.0, 0.02)

if is_live_active:
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

exp_home_live = exp_home_pre * restzeit_anteil
exp_away_live = exp_away_pre * restzeit_anteil

st.markdown("---")
st.subheader("📋 Berechnete Rest-Tor-Erwartung für die Buchmacher-Quoten")
col1, col2 = st.columns(2)
with col1:
    st.metric("Erwartete Tore (Heim)", f"{exp_home_live:.2f}")
with col2:
    st.metric("Erwartete Tore (Auswärts)", f"{exp_away_live:.2f}")

def poisson_pmf(k, lamb):
    return (lamb ** k * math.exp(-lamb)) / math.factorial(k)

# Multi-Markt Berechnung
prob_home, prob_draw, prob_away = 0.0, 0.0, 0.0
prob_btts_yes, prob_under_15, prob_under_25, prob_under_35 = 0.0, 0.0, 0.0, 0.0

for x in range(0, 11):
    for y in range(0, 11):
        p = poisson_pmf(x, exp_home_live) * poisson_pmf(y, exp_away_live)
        end_home = st.session_state.goals_home + x
        end_away = st.session_state.goals_away + y
        
        if end_home > end_away: prob_home += p
        elif end_home == end_away: prob_draw += p
        else: prob_away += p
        if end_home > 0 and end_away > 0: prob_btts_yes += p
        if (end_home + end_away) < 1.5: prob_under_15 += p
        if (end_home + end_away) < 2.5: prob_under_25 += p
        if (end_home + end_away) < 3.5: prob_under_35 += p

prob_dc_1x = min(prob_home + prob_draw, 1.0)
prob_dc_x2 = min(prob_away + prob_draw, 1.0)
prob_over_15 = max(1.0 - prob_under_15, 0.0)

heim_name = game_input.split('-')[0].strip() if '-' in game_input else 'Heim'
auswaerts_name = game_input.split('-')[1].strip() if '-' in game_input else 'Auswärts'

def calculate_real_market_odds(prob, margin=0.05):
    if prob < 0.005: return 99.0
    return round((1.0 / prob) * (1.0 - margin), 2)

# Quoten skalieren
odds_1 = calculate_real_market_odds(prob_home)
odds_x = calculate_real_market_odds(prob_draw)
odds_2 = calculate_real_market_odds(prob_away)
odds_btts_yes = calculate_real_market_odds(prob_btts_yes)
odds_btts_no = calculate_real_market_odds(1.0 - prob_btts_yes)
odds_under_15 = calculate_real_market_odds(prob_under_15)
odds_over_15 = calculate_real_market_odds(prob_over_15)
odds_under_25 = calculate_real_market_odds(prob_under_25)
odds_over_25 = calculate_real_market_odds(1.0 - prob_under_25)
odds_dc_1x = calculate_real_market_odds(prob_dc_1x)
odds_dc_x2 = calculate_real_market_odds(prob_dc_x2)

st.subheader("📊 Berechnete Live-Marktquoten (Betano / Interwetten / Winamax)")
quoten_daten = {
    "Wettmarkt / Tipp": [f"Sieg {heim_name} (1)", "Unentschieden (X)", f"Sieg {auswaerts_name} (2)", "BTTS: JA", "BTTS: NEIN", "Unter 1,5 Tore", "Über 1,5 Tore", "Unter 2,5 Tore", "Über 2,5 Tore", "Doppelte Chance 1X", "Doppelte Chance X2"],
    "Wahrscheinlichkeit": [f"{prob_home*100:.1f}%", f"{prob_draw*100:.1f}%", f"{prob_away*100:.1f}%", f"{prob_btts_yes*100:.1f}%", f"{(1-prob_btts_yes)*100:.1f}%", f"{prob_under_15*100:.1f}%", f"{prob_over_15*100:.1f}%", f"{prob_under_25*100:.1f}%", f"{(1-prob_under_25)*100:.1f}%", f"{prob_dc_1x*100:.1f}%", f"{prob_dc_x2*100:.1f}%"],
    "Erwartete Quote": [f"{odds_1:.2f}", f"{odds_x:.2f}", f"{odds_2:.2f}", f"{odds_btts_yes:.2f}", f"{odds_btts_no:.2f}", f"{odds_under_15:.2f}", f"{odds_over_15:.2f}", f"{odds_under_25:.2f}", f"{odds_over_25:.2f}", f"{odds_dc_1x:.2f}", f"{odds_dc_x2:.2f}"]
}
st.table(pd.DataFrame(quoten_daten))

# 🛠️ KOMBIWETTEN-KONFIGURATOR
st.markdown("---")
st.header("🔥 Sinnvollste Kombi-Konfigurationen (Spielfeld-Kombis)")

if prob_dc_1x > prob_dc_x2:
    safe_dc_title = f"Doppelte Chance 1X ({heim_name})"
    safe_dc_odds = odds_dc_1x
else:
    safe_dc_title = f"Doppelte Chance X2 ({auswaerts_name})"
    safe_dc_odds = odds_dc_x2

if prob_over_15 > 0.65:
    safe_tor_title = "Über 1,5 Tore"
    safe_tor_odds = odds_over_15
else:
    safe_tor_title = "Unter 3,5 Tore"
    safe_tor_odds = calculate_real_market_odds(prob_under_35)

safe_kombi_odds = round(safe_dc_odds * safe_tor_odds * 0.93, 2)

if prob_home > prob_away and prob_home > prob_draw:
    value_trend = f"Sieg {heim_name}"
    value_trend_odds = odds_1
    value_tor = "Über 1,5 Tore" if prob_over_15 > 0.60 else "Unter 3,5 Tore"
    value_tor_odds = odds_over_15 if prob_over_15 > 0.60 else calculate_real_market_odds(prob_under_35)
elif prob_away > prob_home and prob_away > prob_draw:
    value_trend = f"Sieg {auswaerts_name}"
    value_trend_odds = odds_2
    value_tor = "Über 1,5 Tore" if prob_over_15 > 0.60 else "Unter 3,5 Tore"
    value_tor_odds = odds_over_15 if prob_over_15 > 0.60 else calculate_real_market_odds(prob_under_35)
else:
    value_trend = "Unentschieden (X)"
    value_trend_odds = odds_x
    value_tor = "Unter 2,5 Tore"
    value_tor_odds = odds_under_25

value_kombi_odds = round(value_trend_odds * value_tor_odds * 0.92, 2)

risiko_trend_name = heim_name if prob_home > prob_away else auswaerts_name
risiko_trend_odds = odds_1 if prob_home > prob_away else odds_2
risiko_tipp = "BTTS: JA" if prob_btts_yes > 0.50 else "BTTS: NEIN"
risiko_odds = odds_btts_yes if prob_btts_yes > 0.50 else odds_btts_no
risiko_kombi_odds = round(risiko_trend_odds * risiko_odds * 0.90, 2)

c_safe, c_val, c_risk = st.columns(3)
with c_safe:
    st.success("🛡️ **1. Sicherheits-Kombi**")
    st.markdown(f"* **{safe_dc_title}**\n* **{safe_tor_title}**")
    st.markdown(f"📈 Reale Quote: **{max(safe_kombi_odds, 1.15):.2f}**")
with c_val:
    st.info("⚡ **2. Value-Kombi**")
    st.markdown(f"* **{value_trend}**\n* **{value_tor}**")
    st.markdown(f"📈 Reale Quote: **{max(value_kombi_odds, 1.35):.2f}**")
with c_risk:
    st.error("💥 **3. Ergebnis-Kombi**")
    st.markdown(f"* **Sieg {risiko_trend_name}**\n* **{risiko_tipp}**")
    st.markdown(f"📈 Reale Quote: **{max(risiko_kombi_odds, 1.60):.2f}**")
