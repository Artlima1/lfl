import streamlit as st
import pandas as pd
import sys

# Add module paths before importing custom modules
sys.path.append('./src/Classes')
sys.path.append('./src/Pages')

from FantasyLeague import FantasyLeague
from LeagueHistory import LeagueHistory
from dashboard import render_dashboard
from scoring import render_scoring
from performance import render_performance
from expected_wins import render_expected_wins
from seeding import render_seeding
from league_history import render_league_history

# ==================== Configuration ====================
CONFIG_FILE = './league_config.json'

# ==================== Initialization Functions ====================

@st.cache_resource
def init_league():
    """Initialize the Fantasy League from JSON configuration."""
    league = FantasyLeague(from_json=CONFIG_FILE)
    return (league, league.getTeamsDf(), league.getScoringDf(), league.getH2hDf())

@st.cache_resource
def init_league_history():
    """Initialize League History from historical Sleeper seasons + current season data."""
    league, teams_df, scoring_df, h2h_df = init_league()
    history = LeagueHistory(
        from_json=CONFIG_FILE,
        current_season_games=league.getMatchRecords(),
    )
    return (history, history.getAllTimeH2hDf(teams_df))

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

    with st.spinner("Carregando histórico da liga..."):
        (league_history, all_time_h2h_df) = init_league_history()

    # Store data in session state for later use
    if 'league' not in st.session_state:
        st.session_state.league = league
    if 'teams_df' not in st.session_state:
        st.session_state.teams_df = teams_df
    if 'scoring_df' not in st.session_state:
        st.session_state.scoring_df = scoring_df
    if 'h2h_df' not in st.session_state:
        st.session_state.h2h_df = h2h_df
    # Navigation — using st.segmented_control (not st.tabs) because its
    # selection is tracked in st.session_state and survives reruns triggered
    # by widgets inside a section. st.tabs' active tab lives only in the
    # frontend and can reset to the first tab when a widget inside a
    # non-first tab triggers a rerun (a known Streamlit limitation).
    section_labels = [
        "📊 Dashboard",
        "🔢 Seeding",
        "📈 Pontuação Semanal",
        "📉 Gráficos de Desempenho",
        "🎯 Expected Wins",
        "🏆 Histórico da Liga"
    ]
    selected_section = st.segmented_control(
        "Navegação",
        section_labels,
        default=section_labels[0],
        key="active_section",
        label_visibility="collapsed"
    )
    if selected_section is None:
        selected_section = section_labels[0]

    st.markdown("---")

    if selected_section == "📊 Dashboard":
        render_dashboard(teams_df, scoring_df)

    elif selected_section == "🔢 Seeding":
        render_seeding(teams_df, h2h_df)

    elif selected_section == "📈 Pontuação Semanal":
        render_scoring(teams_df, scoring_df)

    elif selected_section == "📉 Gráficos de Desempenho":
        render_performance(teams_df, scoring_df)

    elif selected_section == "🎯 Expected Wins":
        render_expected_wins(teams_df, scoring_df)

    elif selected_section == "🏆 Histórico da Liga":
        render_league_history(all_time_h2h_df, league_history, teams_df)

if __name__ == "__main__":
    main()
