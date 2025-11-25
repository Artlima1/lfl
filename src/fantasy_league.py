import streamlit as st
import pandas as pd
import sys

# Add module paths before importing custom modules
sys.path.append('./src/Classes')
sys.path.append('./src/Pages')

from FantasyLeague import FantasyLeague
from dashboard import render_dashboard
from scoring import render_scoring
from performance import render_performance
from expected_wins import render_expected_wins
from seeding import render_seeding

# ==================== Configuration ====================
CONFIG_FILE = './league_config.json'

# ==================== Initialization Functions ====================

@st.cache_resource
def init_league():
    """Initialize the Fantasy League from JSON configuration."""
    league = FantasyLeague(from_json=CONFIG_FILE)
    return (league, league.getTeamsDf(), league.getScoringDf(), league.getH2hDf())

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
        (league, teams_df, scoring_df, h2h_df) = init_league()

    # Store data in session state for later use
    if 'league' not in st.session_state:
        st.session_state.league = league
    if 'teams_df' not in st.session_state:
        st.session_state.teams_df = teams_df
    if 'scoring_df' not in st.session_state:
        st.session_state.scoring_df = scoring_df
    if 'h2h_df' not in st.session_state:
        st.session_state.h2h_df = h2h_df
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "🔢 Seeding",
        "📈 Pontuação Semanal",
        "📉 Gráficos de Desempenho",
        "🎯 Expected Wins"
    ])

    with tab1:
        render_dashboard(teams_df, scoring_df)

    with tab2:
        render_seeding(teams_df, h2h_df)

    with tab3:
        render_scoring(teams_df, scoring_df)

    with tab4:
        render_performance(teams_df, scoring_df)

    with tab5:
        render_expected_wins(teams_df, scoring_df)

if __name__ == "__main__":
    main()
