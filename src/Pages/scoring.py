import streamlit as st
import pandas as pd


def render_scoring(teams_df, scores_df):
    """Render the Pontuação Semanal tab."""
    st.header("Pontuação Semanal")

    # Create team selection checkboxes
    st.subheader("Selecione os Times")

    # Get unique teams sorted by name
    teams = sorted(teams_df['short_name'].unique())

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
        filtered_scores = scores_df[
            scores_df['short_name'].isin(selected_teams)
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
        st.warning("Selecione pelo menos um time para visualizar o gráfico.")