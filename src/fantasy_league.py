from src.FantasyLeague import FantasyLeague
from src.Pages.dashboard import render_dashboard
from src.Pages.scoring import render_scoring
from src.Pages.performance import render_performance
from src.Pages.expected_wins import render_expected_wins
import streamlit as st
import pandas as pd

# ==================== Configuration ====================
CONFIG_FILE = 'league_config.json'

# ==================== Initialization Functions ====================

@st.cache_resource
def init_league():
    """Initialize the Fantasy League from JSON configuration."""
    league = FantasyLeague(from_json=CONFIG_FILE)
    return league

@st.cache_data
def load_league_data(_league):
    """Load and compile all league data. Cached to avoid repeated API calls."""
    _league.compile_league_data()
    return _league.get_league_df()

@st.cache_data
def get_scores_data(_league):
    """Get scores dataframe from the league."""
    return _league.scores_df

@st.cache_data
def get_probability_data(_league):
    """Get probability dataframe from the league."""
    return _league.prob_df

@st.cache_data
def get_current_week(_league):
    """Get the current week number."""
    return _league.current_week

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
        league = init_league()
        league_df = load_league_data(league)
        current_week = get_current_week(league)

    # Store data in session state for later use
    if 'league' not in st.session_state:
        st.session_state.league = league
    if 'league_df' not in st.session_state:
        st.session_state.league_df = league_df
    if 'current_week' not in st.session_state:
        st.session_state.current_week = current_week

    # Get data needed for all tabs
    scores_df = get_scores_data(league)
    prob_df = get_probability_data(league)

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "📈 Pontuação Semanal",
        "📉 Gráficos de Desempenho",
        "🎯 Expected Wins"
    ])

    with tab1:
        render_dashboard(league, league_df, scores_df)

    with tab2:
        render_scoring(league, league_df, scores_df)

    with tab3:
        render_performance(league, league_df, scores_df)

    with tab4:
        render_expected_wins(league, league_df, prob_df)

if __name__ == "__main__":
    main()
