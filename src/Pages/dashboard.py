import streamlit as st
import pandas as pd


def render_dashboard(teams_df, scores_df):
    """Render the Dashboard tab."""
    st.header("Dashboard")

    # League Standings Table
    st.subheader("Classificação da Liga")
    # Select and rename columns for display
    standings_df = teams_df[['seed', 'short_name', 'wins', 'avg', "last5", 'std', 'avgRank', 'avgOppRank']]\
        .sort_values(by="seed")\
        .rename(columns={
            'seed': 'Seed',
            'short_name': 'Time',
            'wins': 'Vitórias',
            'avg': 'Média',
            'std': 'Desvio Padrão',
            'last5': 'Últimos 5',
            'avgRank': 'Rank Médio',
            'avgOppRank': 'Rank Médio Adversário',
        })

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
            "Rank Médio": st.column_config.NumberColumn("Rank Médio", format="%.2f"),
            "Rank Médio Adversário": st.column_config.NumberColumn("Rank Médio Adversário", format="%.2f"),
        }
    )

    with st.expander("Legenda das colunas"):
        st.markdown("""
        - **Seed**: posição do time na classificação geral da liga.
        - **Time**: nome abreviado do time.
        - **Vitórias**: número de vitórias do time na temporada.
        - **Média**: pontuação média do time por semana.
        - **Últimos 5**: pontuação média do time nas últimas 5 semanas.
        - **Desvio Padrão**: variação da pontuação do time em relação à média (quanto menor, mais consistente).
        - **Rank Médio**: posição média do time no ranking semanal de pontuação (1 = melhor pontuação da semana).
        - **Rank Médio Adversário**: posição média do ranking semanal dos adversários enfrentados pelo time (mede a força do calendário).
        """)

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