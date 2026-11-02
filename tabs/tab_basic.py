import streamlit as st
import pandas as pd
from styles import render_multi_header_table

import streamlit as st
import pandas as pd

def render_tab_basic(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("표시할 종목 데이터가 없습니다.")
        return df

    # ★ 핵심: 전달받은 df의 순서 그대로 HTML 행(tr)을 조립
    rows_html = ""
    for idx, row in df.iterrows():
        code = str(row.get("종목코드", "")).strip().zfill(6)
        name = row.get("종목명", "-")
        curr_price = row.get("현재가", "-")
        market_cap = row.get("시총", "-")
        per_val = row.get("현재 PER", "-")
        pbr_val = row.get("현재 PBR", "-")
        dps_val = row.get("DPS(원)", "-")
        div_val = row.get("배당수익률", "-")

        rows_html += f"""
        <tr data-code="{code}">
            <td style="text-align: center;"><input type="checkbox" class="stock-checkbox" data-code="{code}"></td>
            <td style="font-weight: 600;">{name}</td>
            <td style="color: #94a3b8; font-family: monospace;">{code}</td>
            <td style="text-align: right; font-weight: 600;">{curr_price}</td>
            <td style="text-align: right;">{market_cap}</td>
            <td style="text-align: right;">{per_val}</td>
            <td style="text-align: right;">{pbr_val}</td>
            <td style="text-align: right;">{dps_val}</td>
            <td style="text-align: right;">{div_val}</td>
        </tr>
        """

    table_html = f"""
    <div class="custom-table-container">
        <table class="custom-grid-table" id="table_tab_basic">
            <thead>
                <tr>
                    <th style="width: 40px; text-align: center;"><input type="checkbox" class="header-select-all"></th>
                    <th class="sortable-th" data-col-idx="1">종목명</th>
                    <th class="sortable-th" data-col-idx="2">종목코드</th>
                    <th class="sortable-th" data-col-idx="3" style="text-align: right;">현재가</th>
                    <th class="sortable-th" data-col-idx="4" style="text-align: right;">시총</th>
                    <th class="sortable-th" data-col-idx="5" style="text-align: right;">현재 PER</th>
                    <th class="sortable-th" data-col-idx="6" style="text-align: right;">현재 PBR</th>
                    <th class="sortable-th" data-col-idx="7" style="text-align: right;">DPS(원)</th>
                    <th class="sortable-th" data-col-idx="8" style="text-align: right;">배당수익률</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """

    st.markdown(table_html, unsafe_allow_html=True)
    return df

    df_display = df_basic.copy()

    # HTML 렌더링 (전체 탭 실시간 정렬 연동 + 네이버 링크 + 좌측 체크박스)
    render_multi_header_table(
        df_display,
        tab_name="tab_basic",
        has_naver_link=True,
        has_checkbox=True
    )

    return df_display
