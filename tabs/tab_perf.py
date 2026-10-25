import streamlit as st
import pandas as pd

def render_tab_perf(df_perf: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return

    # 1. 2단 복합 헤더 멀티인덱스 튜플 정의
    multi_cols = [
        ("종목정보", "종목명"),
        ("종목정보", "종목코드"),
        (f"{prev_yr}년", "매출액"),
        (f"{prev_yr}년", "영업이익"),
        (f"{prev_yr}년", "당기순익"),
        (f"{latest_yr}년", "매출액"),
        (f"{latest_yr}년", "영업이익"),
        (f"{latest_yr}년", "당기순익"),
        ("YoY 성장률", "매출"),
        ("YoY 성장률", "영업익"),
        ("YoY 성장률", "순익"),
    ]

    source_cols = [
        "종목명", "종목코드",
        "매출_직전", "영업익_직전", "순익_직전",
        "매출_최근", "영업익_최근", "순익_최근",
        "매출_YoY", "영업익_YoY", "순익_YoY"
    ]

    display_df = df_perf[[c for c in source_cols if c in df_perf.columns]].copy()
    display_df.columns = pd.MultiIndex.from_tuples(multi_cols[:len(display_df.columns)])

    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True
    )
