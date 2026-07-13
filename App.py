import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# Seiteneinstellungen für mobile Geräte optimieren
st.set_page_config(
    page_title="Svens Value-Bet Finder",
    page_icon="⚽",
    layout="centered"
)

# --- DATEN-FUNKTIONEN ---
@st.cache_data
def get_and_prepare_data():
    # Saisondaten laden (Saison 25/26)
    url = "https://www.football-data.co.uk/mmz4281/2526/D1.csv"
    try:
        df = pd.read_csv(url)
    except Exception:
        # Fallback auf Vorsaison
        url = "https://www.football-data.co.uk/mmz4281/2425/D1.csv"
        df = pd.read_csv(url)
        
    df = df[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']].dropna()
    return df

def calculate_team_strengths(df):
    avg_home_goals = df['FTHG'].mean()
    avg_away_goals = df['FTAG'].mean()
    
    home_attack = df.groupby('HomeTeam')['FTHG'].mean() / avg_home_goals
    home_defence = df.groupby('HomeTeam')['FTAG'].mean() / avg_away_goals
    away_attack = df.groupby('AwayTeam')['FTAG'].mean() / avg_away_goals
    away_defence = df.groupby('AwayTeam')['FTHG'].mean() / avg_home_goals
    
    return {
        'avg_home_goals': avg_home_goals,
        'avg_away_goals': avg_away_goals,
        'home_attack': home_attack,
        'home_defence': home_defence,
        'away_attack': away_attack,
        'away_defence': away_defence,
        'teams': sorted(df['HomeTeam'].unique())
    }

def predict_match(home_team, away_team, stats):
    lambda_home = stats['home_attack'][home_team] * stats['away_defence'][away_team] * stats['avg_home_goals']
    lambda_away = stats['away_attack'][away_team] * stats['home_defence'][home_team] * stats['avg_away_goals']
    
    max_goals = 10
    score_matrix = np.zeros((max_goals, max_goals))
    for i in range(max_goals):
        for j in range(max_goals):
            score_matrix[i, j] = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
            
    prob_home_win = np.sum(np.tril(score_matrix, -1))
    prob_draw = np.sum(np.diag(score_matrix))
    prob_away_win = np.sum(np.triu(score_matrix, 1))
    
    quote_home = 1 / prob_home_win if prob_home_win > 0 else float('inf')
    quote_draw = 1 / prob_draw if prob_draw > 0 else float('inf')
    quote_away = 1 / prob_away_win if prob_away_win > 0 else float('inf')
    
    return {
        'prob_home': prob_home_win,
        'prob_draw': prob_draw,
        'prob_away': prob_away_win,
        'fair_quote_home': quote_home,
        'fair_quote_draw': quote_draw,
        'fair_quote_away': quote_away
    }

def calculate_kelly_stake(prob, bookie_quote, bankroll, divisor=10):
    if bookie_quote <= 1:
        return 0.0
    b = bookie_quote - 1
    q = 1 - prob
    kelly_fraction = (prob * b - q) / b
    if kelly_fraction <= 0:
        return 0.0
    return round((bankroll * kelly_fraction) / divisor, 2)

# --- APP-OBERFLÄCHE (UI) ---
st.title("⚽ Svens Value-Bet Finder")
st.write("Vergleiche mathematische Wahrscheinlichkeiten mit realen Buchmacher-Quoten.")

# Daten laden
try:
    df_matches = get_and_prepare_data()
    league_stats = calculate_team_strengths(df_matches)
except Exception as e:
    st.error(f"Fehler beim Laden der Spieldaten: {e}")
    st.stop()

# 1. Bankroll & Einstellungen im Sidebar
st.sidebar.header("⚙️ Einstellungen")
bankroll = st.sidebar.number_input("Dein Wettbudget (€)", min_value=10.0, value=500.0, step=10.0)
kelly_div = st.sidebar.slider("Risiko-Dämpfer (Kelly-Teiler)", min_value=1, max_value=20, value=10, 
                               help="10 = Zehntel-Kelly (sehr sicher), 1 = Volles Kelly (extrem riskant!)")

# 2. Spiel-Auswahl
st.subheader("1. Partie auswählen")
col_home, col_away = st.columns(2)
with col_home:
    heim = st.selectbox("Heimteam", league_stats['teams'], index=league_stats['teams'].index("Bayern Munich") if "Bayern Munich" in league_stats['teams'] else 0)
with col_away:
    auswaerts = st.selectbox("Auswärtsteam", [t for t in league_stats['teams'] if t != heim])

# Berechnung starten
pred = predict_match(heim, auswaerts, league_stats)

# Faire Quoten anzeigen
st.subheader("2. Mathematisch faire Quoten (Unser Modell)")
col_q1, col_qx, col_q2 = st.columns(3)
col_q1.metric(label=f"Sieg {heim} (1)", value=f"{pred['fair_quote_home']:.2f}", delta=f"{pred['prob_home']*100:.1f}%")
col_qx.metric(label="Unentschieden (X)", value=f"{pred['fair_quote_draw']:.2f}", delta=f"{pred['prob_draw']*100:.1f}%")
col_q2.metric(label=f"Sieg {auswaerts} (2)", value=f"{pred['fair_quote_away']:.2f}", delta=f"{pred['prob_away']*100:.1f}%")

# 3. Buchmacher Quoten eintragen
st.subheader("3. Reale Quoten eingeben")

# Bookie Tabs erstellen
tab_betano, tab_inter, tab_winamax = st.tabs(["Betano", "Interwetten", "Winamax"])

bookies = {}

with tab_betano:
    c1, cx, c2 = st.columns(3)
    b_1 = c1.number_input("Sieg 1 ", min_value=1.0, value=1.70, step=0.05, key="b1")
    b_x = cx.number_input("Remis ", min_value=1.0, value=4.20, step=0.05, key="bx")
    b_2 = c2.number_input("Sieg 2 ", min_value=1.0, value=4.50, step=0.05, key="b2")
    bookies['Betano'] = {'1': b_1, 'X': b_x, '2': b_2}

with tab_inter:
    i1, ix, i2 = st.columns(3)
    int_1 = i1.number_input("Sieg 1", min_value=1.0, value=1.55, step=0.05, key="i1")
    int_x = ix.number_input("Remis", min_value=1.0, value=4.50, step=0.05, key="ix")
    int_2 = i2.number_input("Sieg 2", min_value=1.0, value=5.20, step=0.05, key="i2")
    bookies['Interwetten'] = {'1': int_1, 'X': int_x, '2': int_2}

with tab_winamax:
    w1, wx, w2 = st.columns(3)
    win_1 = w1.number_input("Sieg 1  ", min_value=1.0, value=1.65, step=0.05, key="w1")
    win_x = wx.number_input("Remis  ", min_value=1.0, value=4.30, step=0.05, key="wx")
    win_2 = w2.number_input("Sieg 2  ", min_value=1.0, value=4.80, step=0.05, key="w2")
    bookies['Winamax'] = {'1': win_1, 'X': win_x, '2': win_2}

# 4. Value-Auswertung
st.subheader("🔥 Value-Wett-Empfehlungen")

value_found = False

for bookie, quotes in bookies.items():
    for outcome, b_quote in quotes.items():
        if outcome == '1':
            prob, fair_q, text = pred['prob_home'], pred['fair_quote_home'], f"Sieg {heim}"
        elif outcome == 'X':
            prob, fair_q, text = pred['prob_draw'], pred['fair_quote_draw'], "Unentschieden"
        else:
            prob, fair_q, text = pred['prob_away'], pred['fair_quote_away'], f"Sieg {auswaerts}"
            
        if b_quote > fair_q:
            value_found = True
            vorteil = (b_quote / fair_q - 1) * 100
            stake = calculate_kelly_stake(prob, b_quote, bankroll, divisor=kelly_div)
            
            if stake > 0:
                st.success(
                    f"**{bookie}** bietet Value auf **{text}**! \n\n"
                    f"• Quote beim Bookie: **{b_quote:.2f}** (Unsere faire Quote: {fair_q:.2f})\n\n"
                    f"• Vorteil: **+{vorteil:.1f}%**\n\n"
                    f"• Empfohlener Einsatz: **{stake:.2f} €**"
                )

if not value_found:
    st.info("Keine Value-Wette für dieses Spiel bei den eingegebenen Quoten gefunden. Finger weg!")
