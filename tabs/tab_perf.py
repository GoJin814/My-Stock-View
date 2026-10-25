import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_perf(df_perf: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return

    header_rows = [
        [
            {"text": "종목명", "rowspan": 2, "col": "종목명"},
            {"text": "종목코드", "rowspan": 2, "col": "종목코드"},
            {"text": f"{prev_yr}", "colspan": 3},
            {"text": f"{latest_yr}", "colspan": 3},
            {"text": "YoY 성장률", "colspan": 3}
        ],
        [
            {"text": "매출액", "col": "매출_직전"},
            {"text": "영업이익", "col": "영업익_직전"},
            {"text": "당기순익", "col": "순익_직전"},
            {"text": "매출액", "col": "매출_최근"},
            {"text": "영업이익", "col": "영업익_최근"},
            {"text": "당기순익", "col": "순익_최근"},
            {"text": "매출", "col": "매출_YoY"},
            {"text": "영업익", "col": "영업익_YoY"},
            {"text": "순익", "col": "순익_YoY"}
        ]
    ]

    source_cols = [
        "종목명", "종목코드",
        "매출_직전", "영업익_직전", "순익_직전",
        "매출_최근", "영업익_최근", "순익_최근",
        "매출_YoY", "영업익_YoY", "순익_YoY"
    ]

    display_df = df_perf[[c for c in source_cols if c in df_perf.columns]].copy()

    render_multi_header_table(
        display_df,
        header_rows=header_rows,
        divider_indices=[1, 4, 7],
        has_naver_link=True,
        tab_name="perf"
    )
