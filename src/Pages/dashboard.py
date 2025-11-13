import streamlit as st
import pandas as pd


def render_dashboard(teams_df, scores_df):
    """Render the Dashboard tab."""
    st.header("Dashboard")

    # League Standings Table
    st.subheader("Classificação da Liga")
    # Select and rename columns for display
    standings_df = teams_df[['seed', 'short_name', 'wins', 'avg', 'std', 'expw']]\
        .sort_values(by="seed")\
        .rename(columns={
            'seed': 'Seed',
            'short_name': 'Time',
            'wins': 'Vitórias',
            'avg': 'Média',
            'std': 'Desvio Padrão',
            'expw': 'Expected Wins'
        })
    standings_df['Delta W'] =  standings_df['Vitórias'] - standings_df['Expected Wins']

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

    # Get unique weeks sorted from most recent to oldest
    weeks = sorted(scores_df['week'].unique(), reverse=True)

    # Create grid layout - 3 columns per row
    num_cols = 3

    for i in range(0, len(weeks), num_cols):
        cols = st.columns(num_cols)

        for col_idx, week in enumerate(weeks[i:i+num_cols]):
            with cols[col_idx]:
                st.markdown(f"**Semana {week}**")

                # Get top scorers for this week
                week_data = scores_df[scores_df['week'] == week]\
                    .sort_values(by='points', ascending=False)\
                    [['short_name', 'points']]\
                    .rename(columns={
                        'short_name': 'Time',
                        'points': 'Pontos'
                    })

                # Display all teams for this week
                week_data['Pontos'] = week_data['Pontos'].round(2)

                st.dataframe(
                    week_data,
                    hide_index=True,
                    use_container_width=True
                )