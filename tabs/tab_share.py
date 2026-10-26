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
    exist_cols = [c for c in cols if c in df_share.columns]
    df_disp = df_share[exist_cols].copy()
    
    if "종목코드" in df_share.columns:
        df_disp["종목코드"] = df_share["종목코드"]

    # 0: 종목명
    # 1~5: 직전년도 (PER, PBR, ROE, EPS, BPS) -> 5번 끝에 선
    # 6~10: 최근년도 (PER, PBR, ROE, EPS, BPS) -> 10번 끝에 선
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

    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[5, 10],
        tab_name="tab_share"
    )
