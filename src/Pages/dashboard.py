import streamlit as st
import pandas as pd


def render_dashboard(teams_df, scores_df):
    """Render the Dashboard tab."""
    st.header("Dashboard")

    # League Standings Table
    st.subheader("Classificação da Liga")
    # Select and rename columns for display
    standings_df = teams_df[['seed', 'short_name', 'wins', 'avg', "last5", 'std', 'med', 'CEW', "SEW"]]\
        .sort_values(by="seed")\
        .rename(columns={
            'seed': 'Seed',
            'short_name': 'Time',
            'wins': 'Vitórias',
            'avg': 'Média',
            'med': 'Mediana',
            'std': 'Desvio Padrão',
            'CEW': 'Campaign-EW',
            'last5': 'Últimos 5',
        })
    standings_df['Delta W'] =  standings_df['Vitórias'] - standings_df['Campaign-EW']
    standings_df['SoS'] = standings_df['SEW'].rank(method='min').astype(int)
    standings_df = standings_df.drop('SEW', axis=1)

    # Round numeric columns for better display
    # standings_df['Média'] = standings_df['Média'].round(2)
    # standings_df['Desvio Padrão'] = standings_df['Desvio Padrão'].round(2)
    # standings_df['Campaign-EW'] = standings_df['Campaign-EW'].round(2)
    # standings_df['Delta W'] = standings_df['Delta W'].round(2)
    # standings_df['Delta W'] = standings_df['Delta W'].round(2)

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
            "Últimos 5": st.column_config.NumberColumn("Últimos 5", format="%.2f"),
            "Desvio Padrão": st.column_config.NumberColumn("Desvio Padrão", format="%.2f"),
            "Mediana": st.column_config.NumberColumn("Mediana", format="%.2f"),
            "Campaign-EW": st.column_config.NumberColumn("Campaign-EW", format="%.2f"),
            "Delta W": st.column_config.NumberColumn("Delta W", format="%.2f"),
            "SoS": st.column_config.NumberColumn("SoS", format="%d"),
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
                    [['short_name', 'points', "win"]]\
                    .rename(columns={
                        'short_name': 'Time',
                        'points': 'Pontos',
                        'win': 'Resultado'
                    })

                # Display all teams for this week
                week_data['Pontos'] = week_data['Pontos'].round(2)
                week_data['Resultado'] = week_data['Resultado'].map({True: 'W', False: 'L'})

                st.dataframe(
                    week_data,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        col: st.column_config.TextColumn(col, width="small") 
                        for col in week_data.columns[1:]
                    }
                )