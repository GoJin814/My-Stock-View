import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_safety(df_safety: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_safety.empty:
        st.info("표시할 종목 데이터가 없습니다.")
        return

    desired_cols = [
        "종목명",
        "부채비율_직전", "당좌비율_직전", "유보율_직전", "영업현금_직전",
        "부채비율_최근", "당좌비율_최근", "유보율_최근", "영업현금_최근"
    ]
    display_df = df_safety[[c for c in desired_cols if c in df_safety.columns]]

    top_headers_safety = [
        ("종목명", 1, False),
        (prev_yr, 4, True),
        (latest_yr, 4, False)
    ]
    sub_headers_safety = [
        "부채비율", "당좌비율", "유보율", "영업현금흐름",
        "부채비율", "당좌비율", "유보율", "영업현금흐름"
    ]

    render_multi_header_table(
        display_df,
        top_headers=top_headers_safety,
        sub_headers=sub_headers_safety,
        divider_indices=[4]
    )

    # 표 하단 참고 수식 표기 유지
    st.caption("※ **순현금성자산** = 현금및현금성자산 + 단기금융상품 (단위: 억원)")
    st.caption("※ **순차입금** = 총차입금(단기차입금 + 유동성장기부채 + 사채 + 장기차입금) - 순현금성자산 (단위: 억원)")
