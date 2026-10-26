import streamlit as st
import pandas as pd

def render_tab_basic(df_basic):
    if df_basic is None or df_basic.empty:
        st.info("표시할 현재 시세 데이터가 없습니다.")
        return None

    # 종목명/종목코드 링크 및 기본 표시 컬럼 정리
    df_display = df_basic.copy()
    
    # 선택 열을 제외한 컬럼들은 읽기 전용으로 보호
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
        key="basic_table_editor"
    )

    return edited_df
