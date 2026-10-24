import streamlit as st
import pandas as pd

def render_tab_basic(df_basic: pd.DataFrame):
    if df_basic.empty:
        return df_basic

    # 세션 상태 키 초기화
    if "select_all_basic" not in st.session_state:
        st.session_state["select_all_basic"] = False

    # 1. 전체 선택 토글 체크박스
    c_all, _ = st.columns([2, 5])
    with c_all:
        select_all = st.checkbox("☑️ 전체 선택 / 해제", key="select_all_basic_checkbox")

    # 전체 선택 상태 변경 감지 시 반영
    if select_all != st.session_state["select_all_basic"]:
        st.session_state["select_all_basic"] = select_all
        df_basic["선택"] = select_all
    else:
        # 기존 전체 선택 상태 유지 반영
        if st.session_state["select_all_basic"]:
            df_basic["선택"] = True

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
        key=f"tab1_editor_{st.session_state['select_all_basic']}"  # 상태 변경 시 에디터 즉시 동기화
    )
    return edited_df
