import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_share(df_share: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_share.empty:
        st.info("표시할 종목 데이터가 없습니다.")
        return

    # 컬럼 순서 재배치 (PER -> PBR -> ROE -> EPS -> BPS) + 종목코드 포함
    desired_cols = [
        "종목명", "종목코드",
        "PER_직전", "PBR_직전", "ROE_직전", "EPS_직전", "BPS_직전",
        "PER_최근", "PBR_최근", "ROE_최근", "EPS_최근", "BPS_최근"
    ]
    display_df = df_share[[c for c in desired_cols if c in df_share.columns]]

    top_headers_share = [
        ("종목명", 1, False),
        (prev_yr, 5, True),
        (latest_yr, 5, False)
    ]
    sub_headers_share = [
        "PER", "PBR", "ROE", "EPS", "BPS",
        "PER", "PBR", "ROE", "EPS", "BPS"
    ]

    render_multi_header_table(
        display_df,
        top_headers=top_headers_share,
        sub_headers=sub_headers_share,
        divider_indices=[4]
    )

    st.caption("※ **순현금성자산** = 현금및현금성자산 + 단기금융상품 (단위: 억원)")
    st.caption("※ **순차입금** = 총차입금(단기차입금 + 유동성장기부채 + 사채 + 장기차입금) - 순현금성자산 (단위: 억원)")
