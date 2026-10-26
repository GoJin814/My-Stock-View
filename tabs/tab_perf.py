import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_perf(df_perf, most_prev_yr, most_latest_yr):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return

    cols = [
        "종목명",
        "매출_직전", "영업익_직전", "순익_직전",
        "매출_최근", "영업익_최근", "순익_최근",
        "매출_YoY", "영업익_YoY", "순익_YoY"
    ]
    df_disp = df_perf[[c for c in cols if c in df_perf.columns]].copy()
    
    if "종목코드" in df_perf.columns:
        df_disp["종목코드"] = df_perf["종목코드"]

    header_rows = [
        [
            {"text": "종목명", "rowspan": 2},
            {"text": f"{most_prev_yr}", "colspan": 3},
            {"text": f"{most_latest_yr}", "colspan": 3},
            {"text": "YoY 성장률", "colspan": 3}
        ],
        [
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익"},
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익"},
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익"}
        ]
    ]

    # ⚡ 3: 직전년도 끝(순익_직전), 6: 최근년도 끝(순익_최근)
    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[3, 6],
        tab_name="tab_perf"
    )
