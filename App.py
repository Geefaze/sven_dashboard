for match in matches:

   from api import get_today_matches


st.title("🔥 TEST VERSION 2 - API SCANNER AKTIV")

matches = get_today_matches()


if len(matches) == 0:
    st.warning("Keine Spiele für heute gefunden.")
    st.stop()


match_names = [
    f"{m['home']} - {m['away']} ({m['league']})"
    for m in matches
]


selected_match = st.selectbox(
    "⚽ Spiel auswählen:",
    match_names
)


selected_index = match_names.index(selected_match)

selected_game = matches[selected_index]


heim_team = selected_game["home"]

auswaerts_team = selected_game["away"]


game_input = f"{heim_team} - {auswaerts_team}"


st.success(
    f"Analyse geladen: {game_input}"
)
