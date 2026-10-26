import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_share(df_share: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_share is None or df_share.empty:
        st.info("표시할 주당 가치 데이터가 없습니다.")
        return

    header_rows = [
        [
            {"text": "종목명", "rowspan": 2, "col": "종목명"},
            {"text": "종목코드", "rowspan": 2, "col": "종목코드"},
            {"text": f"{prev_yr}", "colspan": 5},
            {"text": f"{latest_yr}", "colspan": 5}
        ],
        [
            {"text": "PER", "col": "PER_직전"},
            {"text": "PBR", "col": "PBR_직전"},
            {"text": "ROE", "col": "ROE_직전"},
            {"text": "EPS", "col": "EPS_직전"},
            {"text": "BPS", "col": "BPS_직전"},
            {"text": "PER", "col": "PER_최근"},
            {"text": "PBR", "col": "PBR_최근"},
            {"text": "ROE", "col": "ROE_최근"},
            {"text": "EPS", "col": "EPS_최근"},
            {"text": "BPS", "col": "BPS_최근"}
        ]
    ]

    source_cols = [
        "종목명", "종목코드",
        "PER_직전", "PBR_직전", "ROE_직전", "EPS_직전", "BPS_직전",
        "PER_최근", "PBR_최근", "ROE_최근", "EPS_최근", "BPS_최근"
    ]

    display_df = df_share[[c for c in source_cols if c in df_share.columns]].copy()

    render_multi_header_table(
        display_df,
        header_rows=header_rows,
        divider_indices=[1, 6],
        has_naver_link=True,
        tab_name="share"  # ⚡ 탭 고정 식별자
    )
