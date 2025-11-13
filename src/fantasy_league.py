from Classes.FantasyLeague import FantasyLeague
from Pages.dashboard import render_dashboard
from Pages.scoring import render_scoring
from Pages.performance import render_performance
from Pages.expected_wins import render_expected_wins
import streamlit as st
import pandas as pd

# ==================== Configuration ====================
CONFIG_FILE = './league_config.json'

# ==================== Initialization Functions ====================

@st.cache_resource
def init_league():
    """Initialize the Fantasy League from JSON configuration."""
    league = FantasyLeague(from_json=CONFIG_FILE)
    return (league, league.getTeamsDf(), league.getScoringDf())

# ==================== Page Configuration ====================

st.set_page_config(
    page_title="LFL",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Main Application ====================

def main():
    # Title and Header with Logo
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image("LFL_Logo.jpg", width=80)
    with col2:
        st.title("LFL")
    st.markdown("---")

    # Initialize league and load data
    with st.spinner("Loading league data..."):
        (league, teams_df, scoring_df) = init_league()

    # Store data in session state for later use
    if 'league' not in st.session_state:
        st.session_state.league = league
    if 'teams_df' not in st.session_state:
        st.session_state.teams_df = teams_df
    if 'scoring_df' not in st.session_state:
        st.session_state.scoring_df = scoring_df

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "📈 Pontuação Semanal",
        "📉 Gráficos de Desempenho",
        "🎯 Expected Wins"
    ])

    with tab1:
        render_dashboard(teams_df, scoring_df)

    with tab2:
        render_scoring(teams_df, scoring_df)

    with tab3:
        render_performance(teams_df, scoring_df)

    with tab4:
        render_expected_wins(teams_df, scoring_df)

if __name__ == "__main__":
    main()
