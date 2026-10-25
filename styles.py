import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        /* 기본 여백 및 글꼴 */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        
        /* 탭 버튼 스타일 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
        }
        
        /* HTML 테이블 래퍼 */
        .custom-scroll-table {
            overflow-x: auto;
            margin-bottom: 1rem;
            border-radius: 6px;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df, header_rows=None, divider_indices=None):
    """
    tab_share 및 tab_perf 전용 다단 복합 헤더 테이블 렌더러
    모바일/PC 다크 테마 색상을 인라인으로 직접 적용하여 흰색 반전 방지
    """
    if df is None or df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    div_set = set(divider_indices) if divider_indices else set()

    # 다크 테마 색상 팔레트
    bg_th = "#1e2129"       # 헤더 배경
    bg_td = "#0e1117"       # 본문 행 배경
    border_color = "rgba(128, 128, 128, 0.25)"
    text_color = "#fafafa"

    # 헤더 생성
    thead_html = ""
    if header_rows:
        thead_parts = ["<thead>"]
        for row in header_rows:
            tr = [f'<tr style="background-color: {bg_th}; color: {text_color};">']
            for cell in row:
                r_span = f' rowspan="{cell.get("rowspan", 1)}"' if cell.get("rowspan", 1) > 1 else ""
                c_span = f' colspan="{cell.get("colspan", 1)}"' if cell.get("colspan", 1) > 1 else ""
                txt = cell.get("text", "")
                tr.append(f'<th{r_span}{c_span} style="border: 1px solid {border_color}; padding: 6px 8px; text-align: center; font-size: 0.82rem;">{txt}</th>')
            tr.append("</tr>")
            thead_parts.append("".join(tr))
        thead_parts.append("</thead>")
        thead_html = "".join(thead_parts)
    else:
        # 단일 헤더 fallback
        th_cells = "".join([f'<th style="border: 1px solid {border_color}; padding: 6px 8px; text-align: center; font-size: 0.82rem;">{c}</th>' for c in df.columns])
        thead_html = f'<thead><tr style="background-color: {bg_th}; color: {text_color};">{th_cells}</tr></thead>'

    # 데이터 본문 행 생성
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        td_parts = [f'<tr style="background-color: {bg_td}; color: {text_color};">']
        for col_idx, col_name in enumerate(df.columns):
            val = str(row[col_name])
            if val in ["nan", "None"]:
                val = "-"

            # 구분선(divider_indices) 열일 경우 우측 테두리 강조
            border_r = f"2px solid rgba(128, 128, 128, 0.45)" if col_idx in div_set else f"1px solid {border_color}"

            # 수치 색상 강조 (YoY 증감 등)
            color_style = f"color: {text_color};"
            if "%" in val and not val.startswith("-") and val != "-":
                if val.startswith("+"):
                    color_style = "color: #ff4b4b; font-weight: 500;"
            elif val.startswith("-") and "%" in val and val != "-":
                color_style = "color: #3182ce; font-weight: 500;"

            td_parts.append(
                f'<td style="border: 1px solid {border_color}; border-right: {border_r}; padding: 6px 8px; text-align: center; font-size: 0.82rem; {color_style}">{val}</td>'
            )
        td_parts.append("</tr>")
        tbody_parts.append("".join(td_parts))
    tbody_parts.append("</tbody>")
    tbody_html = "".join(tbody_parts)

    table_html = f"""
    <div class="custom-scroll-table">
        <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            {thead_html}
            {tbody_html}
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
