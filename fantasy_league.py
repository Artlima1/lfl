from FantasyLeague import FantasyLeague
import streamlit as st
import pandas as pd

# ==================== Configuration ====================
LEAGUE_ID = 1238157874098618368

SEEDING = [
    {"short_name": "Roludos", "seed": 1},
    {"short_name": "Flyers", "seed": 2},
    {"short_name": "SuperBowlers", "seed": 3},
    {"short_name": "JetEagles", "seed": 4},
    {"short_name": "Gamblers", "seed": 5},
    {"short_name": "Farmers", "seed": 6},
    {"short_name": "Pombos", "seed": 7},
    {"short_name": "Quasars", "seed": 8},
    {"short_name": "Vetter's", "seed": 9},
    {"short_name": "Spartans", "seed": 10},
    {"short_name": "CottonPickers", "seed": 11},
    {"short_name": "Foxes", "seed": 12}
]

DIVISIONS = [
    {
        "name": "COMI",
        "team_names": ["Quasars", "Spartans", "Gamblers", "Flyers"]
    },
    {
        "name": "SEU",
        "team_names": ["JetEagles", "Roludos", "Vetter's", "Foxes"]
    },
    {
        "name": "PAI",
        "team_names": ["SuperBowlers", "CottonPickers", "Pombos", "Farmers"]
    },
]

# ==================== Initialization Functions ====================

@st.cache_resource
def init_league():
    """Initialize the Fantasy League with custom seeding and divisions."""
    league = FantasyLeague(
        LEAGUE_ID,
        custom_seeding=SEEDING,
        custom_divisions=DIVISIONS
    )
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
    page_title="Fantasy League Dashboard",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Main Application ====================

def main():
    # Title and Header
    st.title("🏈 Fantasy Football League Dashboard")
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

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "📈 Pontuação Semanal",
        "📉 Gráficos de Desempenho",
        "🎯 Expected Wins"
    ])

    with tab1:
        st.header("Dashboard")
        st.info("Dashboard content will be added here...")
        # TODO: Add league standings, key metrics, overview

    with tab2:
        st.header("Pontuação Semanal")

        # Get scores data
        scores_df = get_scores_data(league)

        # Merge with team names
        scores_with_names = scores_df.merge(
            league_df[['roster_id', 'short_name']],
            on='roster_id'
        )

        # Create team selection checkboxes
        st.subheader("Selecione os Times")

        # Get unique teams sorted by name
        teams = sorted(league_df['short_name'].unique())

        # Create columns for checkboxes (3 columns layout)
        cols = st.columns(4)
        selected_teams = []

        for idx, team in enumerate(teams):
            col_idx = idx % 4
            with cols[col_idx]:
                if st.checkbox(team, value=False, key=f"team_{team}"):
                    selected_teams.append(team)

        st.markdown("---")

        # Filter data based on selected teams
        if selected_teams:
            filtered_scores = scores_with_names[
                scores_with_names['short_name'].isin(selected_teams)
            ]

            # Create points line chart
            st.subheader("Pontuação por Semana")

            # Pivot data for better chart formatting
            points_chart_data = filtered_scores.pivot(
                index='week',
                columns='short_name',
                values='points'
            )

            st.line_chart(points_chart_data, height=500)

            # Create rank line chart
            st.subheader("Ranking Semanal")

            # Pivot rank data
            rank_chart_data = filtered_scores.pivot(
                index='week',
                columns='short_name',
                values='rank'
            )

            st.line_chart(rank_chart_data, height=500)
        else:
            st.warning("⚠️ Selecione pelo menos um time para visualizar o gráfico.")

    with tab3:
        st.header("Gráficos de Desempenho")

        # Get scores data
        scores_df = get_scores_data(league)

        # Merge with team names
        scores_with_names = scores_df.merge(
            league_df[['roster_id', 'short_name']],
            on='roster_id'
        )

        # Boxplot using Streamlit
        st.subheader("Boxplot de Pontuação por Time")

        # Prepare data for boxplot - need to reshape for proper display
        boxplot_data = []
        for _, team in league_df.iterrows():
            team_scores = scores_df[scores_df['roster_id'] == team['roster_id']]['points'].values
            for score in team_scores:
                boxplot_data.append({
                    'Time': team['short_name'],
                    'Pontos': score
                })

        boxplot_df = pd.DataFrame(boxplot_data)

        # Use Altair through Streamlit for interactive boxplot
        import altair as alt

        boxplot_chart = alt.Chart(boxplot_df).mark_boxplot(
            size=30
        ).encode(
            x=alt.X('Time:N', sort=league_df['short_name'].tolist()),
            y=alt.Y('Pontos:Q', scale=alt.Scale(zero=False)),
            color=alt.Color('Time:N', legend=None)
        ).properties(
            height=400
        )

        st.altair_chart(boxplot_chart, use_container_width=True)

        st.markdown("---")

        # Performance chart
        st.subheader("Performance Média com Desvio Padrão")

        # Sort by average for better visualization
        perf_data = league_df.sort_values(by=['avg']).reset_index(drop=True)

        # Create error bars data
        perf_chart_data = perf_data[['short_name', 'avg', 'std']].copy()
        perf_chart_data['lower'] = perf_chart_data['avg'] - perf_chart_data['std']
        perf_chart_data['upper'] = perf_chart_data['avg'] + perf_chart_data['std']

        # Create bar chart with error bars
        base = alt.Chart(perf_chart_data).encode(
            x=alt.X('short_name:N', title='Time', sort=None, axis=alt.Axis(labelAngle=-45)),
        )

        bars = base.mark_bar().encode(
            y=alt.Y('avg:Q', title='Pontuação Média', scale=alt.Scale(domain=[80, 165], clamp=True)),
            color=alt.Color('short_name:N', legend=None)
        )

        error_bars = base.mark_errorbar(thickness=3).encode(
            y=alt.Y('lower:Q', scale=alt.Scale(domain=[80, 165])),
            y2=alt.Y2('upper:Q'),
            color=alt.value('white')
        )

        perf_chart = (bars + error_bars).properties(
            height=600,
            padding={"left": 10, "top": 10, "right": 10, "bottom": 50}
        )

        st.altair_chart(perf_chart, use_container_width=True)

    with tab4:
        st.header("Expected Wins")
        st.info("Expected wins analysis will be added here...")
        # TODO: Add expected wins chart, probability charts, win analysis

if __name__ == "__main__":
    main()
