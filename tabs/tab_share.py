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


def render_tab_share(df_share, most_prev_yr, most_latest_yr):
    if df_share is None or df_share.empty:
        st.info("표시할 주당 가치 데이터가 없습니다.")
        return

    prev_label = _year_label(most_prev_yr, -1)
    latest_label = _year_label(most_latest_yr, 0)

    req_cols = [
        "종목명",
        "PER_직전", "PBR_직전", "ROE_직전", "EPS_직전", "BPS_직전",
        "PER_최근", "PBR_최근", "ROE_최근", "EPS_최근", "BPS_최근",
    ]

    df_disp = pd.DataFrame(index=df_share.index)
    for col in req_cols:
        df_disp[col] = df_share[col] if col in df_share.columns else "-"

    if "종목코드" in df_share.columns:
        df_disp["종목코드"] = df_share["종목코드"]

    # 0: 종목명(고정)
    # 1~5: 직전년도 (PER, PBR, ROE, EPS, BPS) -> 5번 우측에만 굵은 선
    # 6~10: 최근년도 (PER, PBR, ROE, EPS, BPS) -> 맨 오른쪽은 기본 선 유지
    header_rows = [
        [
            {"text": "종목명", "rowspan": 2},
            {"text": prev_label, "colspan": 5, "border_right": True},
            {"text": latest_label, "colspan": 5},
        ],
        [
            {"text": "PER"}, {"text": "PBR"}, {"text": "ROE"}, {"text": "EPS"},
            {"text": "BPS", "border_right": True},
            {"text": "PER"}, {"text": "PBR"}, {"text": "ROE"}, {"text": "EPS"},
            {"text": "BPS"},
        ],
    ]

    render_multi_header_table(
        df_disp,
        header_rows=header_rows,
        divider_indices=[5],
        tab_name="tab_share",
    )
