import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_perf(df_perf, most_prev_yr, most_latest_yr):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return

    # 1. 실제 app.py에서 넘어오는 정확한 컬럼 매핑
    cols = [
        "종목명",
        "매출_직전", "영업익_직전", "순익_직전",
        "매출_최근", "영업익_최근", "순익_최근",
        "매출_YoY", "영업익_YoY", "순익_YoY"
    ]
    
    # 존재하는 컬럼만 안전하게 추출
    exist_cols = [c for c in cols if c in df_perf.columns]
    df_disp = df_perf[exist_cols].copy()
    
    if "종목코드" in df_perf.columns:
        df_disp["종목코드"] = df_perf["종목코드"]

    # 2. 2단 복합 헤더 정의
    # 0: 종목명
    # 1~3: 직전년도 (매출, 영업익, 순익) -> 3번 끝에 선
    # 4~6: 최근년도 (매출, 영업익, 순익) -> 6번 끝에 선
    # 7~9: YoY (매출, 영업익, 순익)
    header_rows = [
        [
            {"text": "종목명", "rowspan": 2},
            {"text": f"{most_prev_yr}", "colspan": 3, "border_right": True},
            {"text": f"{most_latest_yr}", "colspan": 3, "border_right": True},
            {"text": "YoY 성장률", "colspan": 3}
        ],
        [
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익", "border_right": True},
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익", "border_right": True},
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익"}
        ]
    ]

    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[3, 6],
        tab_name="tab_perf"
    )
