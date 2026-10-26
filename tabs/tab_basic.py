import streamlit as st
import pandas as pd

def render_tab_basic(df_basic):
    if df_basic is None or df_basic.empty:
        st.info("표시할 현재 시세 데이터가 없습니다.")
        return None

    # ⚡ 표 바로 위에 깔끔한 전체 선택 체크박스 배치
    c_all, _ = st.columns([1.5, 8.5])
    with c_all:
        select_all = st.checkbox("전체 선택", value=False, key="chk_basic_select_all")

    df_display = df_basic.copy()
    
    # 전체 선택 체크 상태를 데이터프레임 초기값에 즉시 반영
    if select_all:
        df_display["선택"] = True

    disabled_cols = [c for c in df_display.columns if c != "선택"]

    edited_df = st.data_editor(
        df_display,
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "",
                help="삭제할 종목 선택",
                default=False,
                width=38
            ),
            "종목명": st.column_config.TextColumn("종목명", width=110),
            "종목코드": st.column_config.TextColumn("종목코드", width=75),
            "현재가": st.column_config.TextColumn("현재가", width=90),
            "시총": st.column_config.TextColumn("시총", width=105),
            "현재 PER": st.column_config.TextColumn("현재 PER", width=75),
            "현재 PBR": st.column_config.TextColumn("현재 PBR", width=75),
            "DPS(원)": st.column_config.TextColumn("DPS(원)", width=80),
            "배당수익률": st.column_config.TextColumn("배당수익률", width=85),
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key=f"basic_table_editor_{select_all}"
    )

    return edited_df
