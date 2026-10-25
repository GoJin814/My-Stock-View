import streamlit as st
import pandas as pd

def render_tab_perf(df_perf: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return

    df_temp = df_perf.copy()
    df_temp["link"] = "https://finance.naver.com/item/main.naver?code=" + df_temp["종목코드"].astype(str).str.zfill(6)

    # 2단 복합 헤더 멀티인덱스
    cols = [
        ("종목정보", "종목명"),
        ("종목정보", "종목코드"),
        (f"{prev_yr}", "매출액"),
        (f"{prev_yr}", "영업이익"),
        (f"{prev_yr}", "당기순익"),
        (f"{latest_yr}", "매출액"),
        (f"{latest_yr}", "영업이익"),
        (f"{latest_yr}", "당기순익"),
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

    display_df = df_temp[source_cols].copy()
    display_df.columns = pd.MultiIndex.from_tuples(cols)
    display_df[("종목정보", "링크")] = df_temp["link"]

    st.dataframe(
        display_df,
        column_config={
            ("종목정보", "종목명"): st.column_config.LinkColumn(
                "종목명",
                display_text=r"https://finance\.naver\.com/item/main\.naver\?code=(\d+)",
                width="small"
            ),
            ("종목정보", "종목코드"): st.column_config.TextColumn("종목코드", width="small"),
            ("종목정보", "링크"): None,
        },
        hide_index=True,
        use_container_width=True
    )
