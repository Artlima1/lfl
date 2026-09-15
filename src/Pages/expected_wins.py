import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from scipy.interpolate import make_interp_spline


def render_expected_wins(teams_df, prob_df):
    """Render the Expected Wins tab."""
    st.header("Expected Wins")

    # Expected Wins Chart
    st.subheader("Vitórias Reais vs Expected Wins")

    # Prepare data sorted by wins and exp_w
    expw_data = teams_df.sort_values(by=['wins', 'CEW']).reset_index(drop=True)

    # Reshape data for grouped bar chart
    expw_chart_data = pd.DataFrame({
        'Time': list(expw_data['short_name']) * 2,
        'Tipo': ['Wins'] * len(expw_data) + ['Expected Wins'] * len(expw_data),
        'Vitórias': list(expw_data['wins']) + list(expw_data['CEW'])
    })

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

    # Get unique divisions from teams_df
    divisions = teams_df.groupby('division')['short_name'].apply(list).to_dict()

    for division_name, team_names in divisions.items():
        st.markdown(f"**Divisão {division_name}**")
        cols = st.columns(4)

        for idx, team_name in enumerate(team_names):
            col_idx = idx % 4
            with cols[col_idx]:
                if st.checkbox(team_name, value=False, key=f"prob_{division_name}_{team_name}"):
                    selected_teams.append(team_name)

    st.markdown("---")

    if selected_teams:
        # Prepare data for probability chart
        prob_chart_data = []

        for short_name in selected_teams:
            # Get roster_id and wins for this team
            team_data = teams_df[teams_df['short_name'] == short_name]
            wins = team_data['wins'].values[0]
            prob_data = team_data["probNWins"].values[0]
            # Get probability data for this team
            x_original = list(range(1,len(prob_data)+1))

            # Create a smooth x range for interpolation
            x_smooth = np.linspace(min(x_original), max(x_original), 200)

            # Create a cubic spline interpolation
            spline = make_interp_spline(x_original, prob_data, k=2)
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