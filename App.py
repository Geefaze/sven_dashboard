for match in matches:

    with st.expander(
        f"⚽ {match['home']} - {match['away']}"
    ):

        st.write(
            f"""
            🏆 Liga: {match['league']}
            
            🌍 Land: {match['country']}
            
            🕒 Zeit: {match['date']}
            """
        )
