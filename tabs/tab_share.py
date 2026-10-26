import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_share(df_share, most_prev_yr, most_latest_yr):
    if df_share is None or df_share.empty:
        st.info("표시할 주당 가치 데이터가 없습니다.")
        return

    # 화면에 표시할 순수 컬럼 정의 (종목코드 제외)
    cols = [
        "종목명",
        "PER_직전", "PBR_직전", "ROE_직전", "EPS_직전", "BPS_직전",
        "PER_최근", "PBR_최근", "ROE_최근", "EPS_최근", "BPS_최근"
    ]
    df_disp = df_share[[c for c in cols if c in df_share.columns]].copy()
    
    # 행 식별(data-code)용으로만 종목코드 전달 (styles 내부에서 화면 출력 전 분리)
    if "종목코드" in df_share.columns:
        df_disp["종목코드"] = df_share["종목코드"]

    header_rows = [
        [
            {"text": "종목명", "rowspan": 2},
            {"text": f"{most_prev_yr}", "colspan": 5},
            {"text": f"{most_latest_yr}", "colspan": 5}
        ],
        [
            {"text": "PER"}, {"text": "PBR"}, {"text": "ROE"}, {"text": "EPS"}, {"text": "BPS"},
            {"text": "PER"}, {"text": "PBR"}, {"text": "ROE"}, {"text": "EPS"}, {"text": "BPS"}
        ]
    ]

    # ⚡ 0: 종목명 우측, 5: 직전년도 우측, 10: 당해년도 우측에 굵은 구분선
    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[0, 5, 10],
        tab_name="tab_share"
    )
