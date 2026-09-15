import streamlit as st
import pandas as pd


def render_league_history(all_time_h2h_df, league_history, teams_df):
    """Render the League History tab."""
    st.header("Histórico da Liga")
    st.subheader("Head-to-Head All-Time")

    st.dataframe(
        all_time_h2h_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            col: st.column_config.TextColumn(col, width="small")
            for col in all_time_h2h_df.columns[1:]
        }
    )

    st.markdown("---")

    st.subheader("Confronto Direto")

    teams = teams_df[['owner_id', 'short_name']].sort_values('short_name')
    team_options = dict(zip(teams['short_name'], teams['owner_id']))
    names = list(team_options.keys())

    col1, col2 = st.columns(2)
    with col1:
        team_a_name = st.selectbox("Time A", names, index=0, key="h2h_team_a")
    with col2:
        default_b_index = 1 if len(names) > 1 else 0
        team_b_name = st.selectbox("Time B", names, index=default_b_index, key="h2h_team_b")

    # st.tabs does not support conditional rendering (per its own docs) —
    # branching between different element types (e.g. st.info vs st.dataframe)
    # inside a tab can make it lose the active tab selection on rerun. So this
    # section always renders the same two elements (a caption + a dataframe),
    # only their content/row-count varies.
    if team_a_name == team_b_name:
        matches = []
        message = "Selecione dois times diferentes para ver os confrontos."
    else:
        owner_a = team_options[team_a_name]
        owner_b = team_options[team_b_name]
        matches = league_history.getMatchesBetween(owner_a, owner_b)
        message = (
            f"{team_a_name} e {team_b_name} nunca se enfrentaram."
            if not matches
            else f"{len(matches)} confronto(s) entre {team_a_name} e {team_b_name}."
        )

    st.caption(message)

    matches_df = pd.DataFrame(
        [
            {
                "Temporada": m["year"],
                "Semana": m["week"],
                team_a_name: round(m["points_a"], 2),
                team_b_name: round(m["points_b"], 2),
                "Playoff": "🏆" if m["playoff"] else "",
                "Vencedor": team_a_name if m["points_a"] > m["points_b"] else team_b_name,
            }
            for m in matches
        ],
        columns=["Temporada", "Semana", team_a_name, team_b_name, "Playoff", "Vencedor"]
    )

    st.dataframe(
        matches_df,
        use_container_width=True,
        hide_index=True
    )
