import streamlit as st

st.write("Test gestartet")

st.write(st.secrets["API_KEY"])import streamlit as st
from api import get_today_matches


st.set_page_config(
    page_title="Sven AI Betting Cockpit",
    layout="wide"
)


st.title("⚽ Sven's AI Betting Cockpit")


st.subheader("📅 Heutige Spiele")


try:

    matches = get_today_matches()


    if len(matches) == 0:

        st.warning(
            "Keine Spiele gefunden"
        )

    else:

        st.success(
            f"{len(matches)} Spiele gefunden"
        )


        for match in matches:

            st.write(
                f"⚽ {match['home']} - {match['away']} | {match['league']}"
            )


except Exception as e:

    st.error(e)
