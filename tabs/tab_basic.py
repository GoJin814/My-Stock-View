import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_basic(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("표시할 종목 데이터가 없습니다.")
        return df

    df_display = df.copy()

    # HTML 렌더링 (전체 탭 실시간 정렬 연동 + 네이버 링크 + 좌측 체크박스)
    render_multi_header_table(
        df_display,
        tab_name="tab_basic",
        has_naver_link=True,
        has_checkbox=True
    )

    return df_display
