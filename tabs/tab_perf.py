import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_perf(df_perf: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_perf.empty:
        st.info("표시할 종목 데이터가 없습니다.")
        return

    desired_cols = [
        "종목명", "종목코드",
        "매출_직전", "영업익_직전", "순익_직전",
        "매출_최근", "영업익_최근", "순익_최근",
        "매출_YoY", "영업익_YoY", "순익_YoY"
    ]
    display_df = df_perf[[c for c in desired_cols if c in df_perf.columns]]

    top_headers_perf = [
        ("종목명", 1, False),
        (prev_yr, 3, True),
        (latest_yr, 3, True),
        ("성장률(YoY)", 3, False)
    ]
    sub_headers_perf = [
        "매출액", "영업이익", "당기순익",
        "매출액", "영업이익", "당기순익",
        "매출", "영업익", "순익"
    ]

    render_multi_header_table(
        display_df,
        top_headers=top_headers_perf,
        sub_headers=sub_headers_perf,
        divider_indices=[2, 5]
    )
