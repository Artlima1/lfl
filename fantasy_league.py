from FantasyLeague import FantasyLeague
import streamlit as st
import pandas as pd
import numpy as np
import json
from scipy.interpolate import make_interp_spline

# ==================== Configuration ====================

# Load league configuration from JSON file
def load_league_config(filename='league_config.json'):
    """Load league configuration from JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

CONFIG = load_league_config()
LEAGUE_ID = CONFIG['league_id']
SEEDING = CONFIG['seeding']
DIVISIONS = CONFIG['divisions']

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

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "📈 Pontuação Semanal",
        "📉 Gráficos de Desempenho",
        "🎯 Expected Wins"
    ])

    with tab1:
        st.header("Dashboard")

        # League Standings Table
        st.subheader("Classificação da Liga")

        # Select and rename columns for display
        standings_df = league_df[['seed', 'short_name', 'wins', 'avg', 'std', 'exp_w', 'delta_w']].copy()
        standings_df.columns = ['Seed', 'Time', 'Vitórias', 'Média', 'Desvio Padrão', 'Expected Wins', 'Delta W']

        # Round numeric columns for better display
        standings_df['Média'] = standings_df['Média'].round(2)
        standings_df['Desvio Padrão'] = standings_df['Desvio Padrão'].round(2)
        standings_df['Expected Wins'] = standings_df['Expected Wins'].round(2)
        standings_df['Delta W'] = standings_df['Delta W'].round(2)

        # Display the table
        st.dataframe(
            standings_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Seed": st.column_config.NumberColumn("Seed", format="%d"),
                "Time": st.column_config.TextColumn("Time"),
                "Vitórias": st.column_config.NumberColumn("Vitórias", format="%d"),
                "Média": st.column_config.NumberColumn("Média", format="%.2f"),
                "Desvio Padrão": st.column_config.NumberColumn("Desvio Padrão", format="%.2f"),
                "Expected Wins": st.column_config.NumberColumn("Expected Wins", format="%.2f"),
                "Delta W": st.column_config.NumberColumn("Delta W", format="%.2f"),
            }
        )

        st.markdown("---")

        # Weekly Score Leaderboards
        st.subheader("Leaderboard Semanal")

        # Get scores data
        scores_df = get_scores_data(league)

        # Merge with team names
        scores_with_names = scores_df.merge(
            league_df[['roster_id', 'short_name']],
            on='roster_id'
        )

        # Get unique weeks sorted from most recent to oldest
        weeks = sorted(scores_with_names['week'].unique(), reverse=True)

        # Create grid layout - 3 columns per row
        num_cols = 3

        for i in range(0, len(weeks), num_cols):
            cols = st.columns(num_cols)

            for col_idx, week in enumerate(weeks[i:i+num_cols]):
                with cols[col_idx]:
                    st.markdown(f"**Semana {week}**")

                    # Get top scorers for this week
                    week_data = scores_with_names[scores_with_names['week'] == week].copy()
                    week_data = week_data.sort_values(by='points', ascending=False)

                    # Display all teams for this week
                    leaderboard = week_data[['rank', 'short_name', 'points']].copy()
                    leaderboard.columns = ['#', 'Time', 'Pontos']
                    leaderboard['Pontos'] = leaderboard['Pontos'].round(2)

                    st.dataframe(
                        leaderboard,
                        hide_index=True,
                        use_container_width=True
                    )

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
            size=15
        ).encode(
            x=alt.X('Time:N', sort=league_df['short_name'].tolist(), axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Pontos:Q', scale=alt.Scale(zero=False)),
            color=alt.Color('Time:N', legend=None)
        ).properties(
            height=400
        ).configure_view(
            strokeWidth=0
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
        )

        perf_chart = (bars + error_bars).properties(
            height=600,
            padding={"left": 10, "top": 10, "right": 10, "bottom": 50}
        )

        st.altair_chart(perf_chart, use_container_width=True)

    with tab4:
        st.header("Expected Wins")

        # Get probability data
        prob_df = get_probability_data(league)

        # Expected Wins Chart
        st.subheader("Vitórias Reais vs Expected Wins")

        # Prepare data sorted by wins and exp_w
        expw_data = league_df.sort_values(by=['wins', 'exp_w']).reset_index(drop=True)

        # Reshape data for grouped bar chart
        expw_chart_data = pd.DataFrame({
            'Time': list(expw_data['short_name']) * 2,
            'Tipo': ['Wins'] * len(expw_data) + ['Expected Wins'] * len(expw_data),
            'Vitórias': list(expw_data['wins']) + list(expw_data['exp_w'])
        })

        import altair as alt

        expw_chart = alt.Chart(expw_chart_data).mark_bar().encode(
            x=alt.X('Time:N', sort=None, title='Time'),
            y=alt.Y('Vitórias:Q', title='Número de Vitórias'),
            color=alt.Color('Tipo:N',
                          scale=alt.Scale(domain=['Wins', 'Expected Wins'], range=['#1f77b4', '#17becf']),
                          legend=alt.Legend(title='Tipo', orient='top')),
            xOffset='Tipo:N'
        ).properties(
            height=500
        )

        st.altair_chart(expw_chart, use_container_width=True)

        st.markdown("---")

        # Probability Chart with teams organized by division
        st.subheader("Curvas de Probabilidade")

        st.write("Selecione os times para visualizar suas curvas de probabilidade:")

        # Create checkboxes organized by division
        selected_teams = []

        for division in DIVISIONS:
            st.markdown(f"**Divisão {division['name']}**")
            cols = st.columns(4)

            for idx, team_name in enumerate(division['team_names']):
                col_idx = idx % 4
                with cols[col_idx]:
                    if st.checkbox(team_name, value=False, key=f"prob_{division['name']}_{team_name}"):
                        selected_teams.append(team_name)

        st.markdown("---")

        if selected_teams:
            # Prepare data for probability chart
            prob_chart_data = []

            for short_name in selected_teams:
                # Get roster_id and wins for this team
                team_data = league_df[league_df['short_name'] == short_name]
                roster_id = team_data['roster_id'].values[0]
                wins = team_data['wins'].values[0]

                # Get probability data for this team
                team_prob = prob_df[prob_df['roster_id'] == roster_id].sort_values('n_wins')
                x_original = team_prob['n_wins'].values
                data = team_prob['prob'].values

                # Create a smooth x range for interpolation
                x_smooth = np.linspace(x_original.min(), x_original.max(), 200)

                # Create a cubic spline interpolation
                spline = make_interp_spline(x_original, data, k=2)
                y_smooth = spline(x_smooth)

                # Add smoothed curve data
                for x, y in zip(x_smooth, y_smooth):
                    prob_chart_data.append({
                        'Time': short_name,
                        'Vitórias': x,
                        'Probabilidade': y,
                        'Marker': None
                    })

                # Add marker at actual wins
                y_wins = spline(wins)
                prob_chart_data.append({
                    'Time': short_name,
                    'Vitórias': wins,
                    'Probabilidade': y_wins,
                    'Marker': 'Vitórias Reais'
                })

            prob_chart_df = pd.DataFrame(prob_chart_data)

            # Create line chart
            lines = alt.Chart(prob_chart_df[prob_chart_df['Marker'].isna()]).mark_line(strokeWidth=2).encode(
                x=alt.X('Vitórias:Q', title='Número de Vitórias'),
                y=alt.Y('Probabilidade:Q', title='Probabilidade'),
                color=alt.Color('Time:N', legend=alt.Legend(title='Time', orient='top'))
            )

            # Create markers for actual wins
            markers = alt.Chart(prob_chart_df[prob_chart_df['Marker'].notna()]).mark_circle(size=100).encode(
                x=alt.X('Vitórias:Q'),
                y=alt.Y('Probabilidade:Q'),
                color=alt.Color('Time:N', legend=None),
                tooltip=['Time:N', 'Vitórias:Q', 'Probabilidade:Q']
            )

            prob_chart = (lines + markers).properties(height=500)

            st.altair_chart(prob_chart, use_container_width=True)
        else:
            st.info("Selecione pelo menos um time para visualizar as curvas de probabilidade.")

if __name__ == "__main__":
    main()
