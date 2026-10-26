import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_basic(df_basic):
    if df_basic is None or df_basic.empty:
        st.info("표시할 현재 시세 데이터가 없습니다.")
        return None

    df_display = df_basic.copy()
    if "선택" in df_display.columns:
        df_display = df_display.drop(columns=["선택"])

    # HTML 그리드 렌더링 (전 탭 실시간 정렬 연동 + 네이버 증권 링크 지원)
    render_multi_header_table(
        df_display,
        tab_name="tab_basic",
        has_naver_link=True,
        has_checkbox=False
    )

    return df_display
