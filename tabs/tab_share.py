import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_share(df_share, most_prev_yr, most_latest_yr):
    if df_share is None or df_share.empty:
        st.info("표시할 주당 가치 데이터가 없습니다.")
        return

    cols = [
        "종목명",
        "PER_직전", "PBR_직전", "ROE_직전", "EPS_직전", "BPS_직전",
        "PER_최근", "PBR_최근", "ROE_최근", "EPS_최근", "BPS_최근"
    ]
    df_disp = df_share[[c for c in cols if c in df_share.columns]].copy()
    
    if "종목코드" in df_share.columns:
        df_disp["종목코드"] = df_share["종목코드"]

    header_rows = [
        [
            {"text": "종목명", "rowspan": 2},
            {"text": f"{most_prev_yr}", "colspan": 5, "border_right": True},
            {"text": f"{most_latest_yr}", "colspan": 5, "border_right": True}
        ],
        [
            {"text": "PER"}, {"text": "PBR"}, {"text": "ROE"}, {"text": "EPS"}, {"text": "BPS", "border_right": True},
            {"text": "PER"}, {"text": "PBR"}, {"text": "ROE"}, {"text": "EPS"}, {"text": "BPS", "border_right": True}
        ]
    ]

    # ⚡ 5번(BPS_직전 우측)과 10번(BPS_최근 우측)에 세로 구분선 강제 지정
    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[5, 10],
        tab_name="tab_share"
    )
