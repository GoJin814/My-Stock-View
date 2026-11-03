from datetime import datetime

import streamlit as st

from styles import render_multi_header_table


def _year_label(v, offset):
    """'2027', '2027년' -> '2027년'. 값이 없으면 현재 연도 + offset으로 계산."""
    s = str(v).strip() if v is not None else ""
    if len(s) >= 4 and s[:4].isdigit():
        return f"{s[:4]}년"
    return f"{datetime.now().year + offset}년"


def render_tab_perf(df_perf, most_prev_yr, most_latest_yr):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return

    prev_label = _year_label(most_prev_yr, -1)
    latest_label = _year_label(most_latest_yr, 0)

    cols = [
        "종목명",
        "매출_직전", "영업익_직전", "순익_직전",
        "매출_최근", "영업익_최근", "순익_최근",
        "매출_YoY", "영업익_YoY", "순익_YoY",
    ]
    exist_cols = [c for c in cols if c in df_perf.columns]
    df_disp = df_perf[exist_cols].copy()

    if "종목코드" in df_perf.columns:
        df_disp["종목코드"] = df_perf["종목코드"]

    render_multi_header_table(
        df_disp,
        prev_yr=prev_label,
        latest_yr=latest_label,
        tab_name="tab_perf",
    )
