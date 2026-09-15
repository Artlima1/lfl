import streamlit as st


def render_league_history(all_time_h2h_df):
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
