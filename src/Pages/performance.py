import streamlit as st
import pandas as pd
import altair as alt


def render_performance(league, league_df, scores_df):
    """Render the Gráficos de Desempenho tab."""
    st.header("Gráficos de Desempenho")

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
    boxplot_chart = alt.Chart(boxplot_df).mark_boxplot(
        size=15
    ).encode(
        x=alt.X('Time:N',
               sort=league_df['short_name'].tolist(),
               axis=alt.Axis(labelAngle=-45, labelLimit=100, labelOverlap=False)),
        y=alt.Y('Pontos:Q', scale=alt.Scale(zero=False)),
        color=alt.Color('Time:N', legend=None)
    ).properties(
        height=400
    ).configure_axisX(
        labelFontSize=9,
        labelAngle=-45
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
        x=alt.X('short_name:N',
               title='Time',
               sort=None,
               axis=alt.Axis(labelAngle=-45, labelLimit=100, labelOverlap=False)),
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
    ).configure_axisX(
        labelFontSize=9,
        labelAngle=-45
    )

    st.altair_chart(perf_chart, use_container_width=True)