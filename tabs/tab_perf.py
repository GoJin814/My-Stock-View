from datetime import datetime

import pandas as pd
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

    # 0: 종목명
    # 1~3: 직전년도 -> 3번 끝에 선
    # 4~6: 최근년도 -> 6번 끝에 선
    # 7~9: YoY
    header_rows = [
        [
            {"text": "종목명", "rowspan": 2},
            {"text": prev_label, "colspan": 3, "border_right": True},
            {"text": latest_label, "colspan": 3, "border_right": True},
            {"text": "YoY 성장률", "colspan": 3},
        ],
        [
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익", "border_right": True},
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익", "border_right": True},
            {"text": "매출액"}, {"text": "영업이익"}, {"text": "당기순익"},
        ],
    ]

    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[3, 6],
        tab_name="tab_perf",
    )
