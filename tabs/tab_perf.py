import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_perf(df_perf, most_prev_yr, most_latest_yr):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return

    # 화면에 표시할 순수 컬럼 정의 (종목코드 제외)
    cols = [
        "종목명",
        "매출_직전", "영업익_직전", "순익_직전",
        "매출_최근", "영업익_최근", "순익_최근",
        "매출_YoY", "영업익_YoY", "순익_YoY"
    ]
    df_disp = df_perf[[c for c in cols if c in df_perf.columns]].copy()
    
    # 행 식별(data-code)용으로만 종목코드 전달
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

    # ⚡ 0: 종목명 우측, 3: 직전년도 우측, 6: 당해년도 우측에 굵은 구분선
    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[0, 3, 6],
        tab_name="tab_perf"
    )
