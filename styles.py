import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
        }
        
        .custom-scroll-table {
            overflow-x: auto;
            margin-bottom: 1rem;
            border-radius: 6px;
            border: 1px solid rgba(128, 128, 128, 0.25);
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df, *args, **kwargs):
    """
    tab_share 및 tab_perf의 다양한 인자 전달 방식을 모두 완벽 수용하는 안전 렌더러
    """
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        st.info("표시할 데이터가 없습니다.")
        return

    # 1. divider_indices 파싱
    divider_indices = kwargs.get("divider_indices", None)
    if not divider_indices and len(args) >= 2:
        divider_indices = args[1]
    div_set = set(divider_indices) if divider_indices else set()

    # 2. header 정보 파싱 (문자열 HTML 또는 리스트 형태 모두 지원)
    header_data = None
    if args:
        header_data = args[0]
    elif "header_html" in kwargs:
        header_data = kwargs["header_html"]
    elif "header_rows" in kwargs:
        header_data = kwargs["header_rows"]

    # 다크 테마 고정 팔레트
    bg_th = "#1e2129"
    bg_td = "#0e1117"
    border_color = "rgba(128, 128, 128, 0.25)"
    text_color = "#fafafa"

    # 헤더 HTML 조립
    thead_html = ""
    if isinstance(header_data, str) and header_data.strip():
        # 이미 <tr> 또는 <thead>로 완성된 HTML 문자열이 넘어온 경우
        clean_header = header_data.strip()
        if not clean_header.startswith("<thead"):
            clean_header = f"<thead>{clean_header}</thead>"
        thead_html = clean_header
    elif isinstance(header_data, list):
        # 셀 딕셔너리 리스트가 넘어온 경우
        thead_parts = ["<thead>"]
        for row in header_data:
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

    # 3. 본문 행 데이터 조립
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        td_parts = [f'<tr style="background-color: {bg_td}; color: {text_color};">']
        for col_idx, col_name in enumerate(df.columns):
            val = str(row[col_name])
            if val in ["nan", "None"]:
                val = "-"

            # 구분선 열인 경우 우측 테두리 강조
            border_r = "2px solid rgba(128, 128, 128, 0.55)" if col_idx in div_set else f"1px solid {border_color}"

            # 수치 색상 하이라이트
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

    # 4. 최종 마크다운 렌더링
    full_table_html = f"""
    <div class="custom-scroll-table">
        <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            {thead_html}
            {tbody_html}
        </table>
    </div>
    """
    st.markdown(full_table_html, unsafe_allow_html=True)
