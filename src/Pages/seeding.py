import streamlit as st
import pandas as pd


def render_seeding(teams_df, h2h_df):
    """Render the Seeding tab."""
    st.header("Seeding")

    # League Standings Table
    st.subheader("Classificação da Liga")
    # Select and rename columns for display
    standings_df = teams_df[['seed', 'short_name', 'record', 'division', 'division_seed', 'division_record', 'avgRank']]\
        .sort_values(by="seed")\
        .rename(columns={
            'seed': 'Seed',
            'short_name': 'Time',
            'record': 'Campanha',
            'division': 'Divisão',
            'division_seed': 'Seed na Divisão',
            'division_record': 'Campanha na Divisão',
            'avgRank': 'Rank Médio',
        })


    # Display the table
    st.dataframe(
        standings_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Seed": st.column_config.NumberColumn("Seed", format="%d"),
            "Time": st.column_config.TextColumn("Time"),
            "Campanha": st.column_config.TextColumn("Campanha"),
            "Divisão": st.column_config.TextColumn("Divisão"),
            "Seed na Divisão": st.column_config.NumberColumn("Seed na Divisão"),
            "Campanha na Divisão": st.column_config.TextColumn("Campanha na Divisão"),
            "Rank Médio": st.column_config.NumberColumn("Rank Médio", format="%.2f"),
        }
    )

    with st.expander("Como funciona o critério de desempate"):
        st.markdown("""
        **Seed de Divisão** (ordem de desempate entre times da mesma divisão):
        1. Vitórias
        2. Confronto direto entre os times empatados
        3. Campanha na divisão
        4. Rank médio semanal (menor é melhor)
        
        O ranking divisional é calculado ANTES do ranking da liga!

        **Seed da Liga** (líderes de divisão sempre na frente dos demais times):
        1. Vitórias
        2. Confronto direto entre os times empatados
        3. Rank médio semanal (menor é melhor)

        Os não-líderes são encaixados comparando, a cada rodada, o melhor time
        ainda não encaixado de cada divisão pelos mesmos critérios acima.
        """)

    st.markdown("---")
    # Head-to-Head Records
    st.subheader("Registros Head-to-Head") 
    # Format H2H records with colored indicators
    def format_h2h_cell(val):
        if val == -1:
            return ""
        elif val > 0.5:
            return "🟢"
        elif val == 0.5:
            return "🟡"
        elif 0 <= val < 0.5:
            return "🔴"
        return val
        
    h2h_df = h2h_df.apply(lambda col: col.map(format_h2h_cell) if col.name != "Team" else col)

    st.dataframe(
        h2h_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            col: st.column_config.TextColumn(col, width="small") 
            for col in h2h_df.columns[1:]
        }
    )