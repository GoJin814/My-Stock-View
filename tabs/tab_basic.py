import streamlit as st
import pandas as pd
from styles import render_multi_header_table

def render_tab_basic(df_basic: pd.DataFrame):
    """현재 시세 탭 렌더링 함수"""
    if df_basic is None or df_basic.empty:
        st.info("표시할 시세 데이터가 없습니다.")
        return None

    header_rows = [
        [
            {"text": "선택", "rowspan": 1},
            {"text": "종목명", "rowspan": 1},
            {"text": "종목코드", "rowspan": 1},
            {"text": "현재가", "rowspan": 1},
            {"text": "시총", "rowspan": 1},
            {"text": "현재 PER", "rowspan": 1},
            {"text": "현재 PBR", "rowspan": 1},
            {"text": "DPS(원)", "rowspan": 1},
            {"text": "배당수익률", "rowspan": 1}
        ]
    ]

    source_cols = [
        "선택", "종목명", "종목코드", "현재가", "시총",
        "현재 PER", "현재 PBR", "DPS(원)", "배당수익률"
    ]

    display_df = df_basic[[c for c in source_cols if c in df_basic.columns]].copy()

    # ⚡ divider_indices를 비워 종목명 오른쪽에 선이 2중으로 겹치는 현상 제거
    render_multi_header_table(
        display_df,
        header_rows=header_rows,
        divider_indices=[],
        tab_name="tab_basic",
        has_checkbox=True
    )

    return display_df
