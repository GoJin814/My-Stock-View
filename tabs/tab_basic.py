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

    # 전체 선택 상태 동기화
    if select_all != st.session_state["select_all_basic"]:
        st.session_state["select_all_basic"] = select_all
        df_basic["선택"] = select_all
    else:
        if st.session_state["select_all_basic"]:
            df_basic["선택"] = True

    # 2. 종목 링크 URL 컬럼 생성
    display_df = df_basic.copy()
    display_df["link"] = display_df["종목코드"].apply(
        lambda c: f"https://stock.naver.com/domestic/stock/{c}/info/company"
    )

    disabled_cols = [c for c in display_df.columns if c != "선택"]

    edited_df = st.data_editor(
        display_df,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width="small", pinned=True),
            "종목명": st.column_config.LinkColumn(
                "종목명",
                help="클릭 시 네이버 증권 기업정보 페이지로 이동합니다.",
                validate=r"^https://.*",
                max_chars=100,
                display_text=r".*", # 원래 종목명이 그대로 표시됨
                pinned=True
            ),
            "link": None, # 링크용 원본 URL 컬럼은 화면에서 숨김
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key=f"tab1_editor_{st.session_state['select_all_basic']}"
    )

    # 링크 컬럼을 제외하고 반환
    return edited_df.drop(columns=["link"], errors="ignore")
