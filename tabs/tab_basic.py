import streamlit as st
import pandas as pd

def render_tab_basic(df_basic: pd.DataFrame):
    disabled_cols = [c for c in df_basic.columns if c != "선택"]
    edited_df = st.data_editor(
        df_basic,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width="small", pinned=True),
            "종목명": st.column_config.TextColumn("종목명", pinned=True),
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key="tab1_editor"
    )
    return edited_df
