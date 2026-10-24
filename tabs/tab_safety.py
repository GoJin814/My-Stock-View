import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_safety(df_safety: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_safety.empty:
        st.info("표시할 종목 데이터가 없습니다.")
        return

    desired_cols = [
        "종목명",
        "부채비율_직전", "순현금_직전", "FCF_직전",
        "부채비율_최근", "순현금_최근", "FCF_최근"
    ]
    display_df = df_safety[[c for c in desired_cols if c in df_safety.columns]]

    top_headers_safety = [
        ("종목명", 1, False),
        (prev_yr, 3, True),
        (latest_yr, 3, False)
    ]
    sub_headers_safety = [
        "부채비율", "순현금성자산", "FCF",
        "부채비율", "순현금성자산", "FCF"
    ]

    render_multi_header_table(
        display_df,
        top_headers=top_headers_safety,
        sub_headers=sub_headers_safety,
        divider_indices=[3]
    )
