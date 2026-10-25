import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* 1. 태블릿 브라우저 _arrow_right 겹침 방지 */
        [data-testid="stExpanderToggleIcon"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
        }
        [data-testid="stExpander"] summary {
            font-weight: 500 !important;
            padding: 8px 12px !important;
        }

        /* 2. 탭 바 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
        }

        /* ⚡ 3. st.data_editor 외곽 프레임과 100% 동일한 컨테이너 */
        .custom-grid-container {
            overflow-x: auto;
            margin-bottom: 1.2rem;
            display: block;
            width: 100%;
            border: 1px solid rgba(250, 250, 250, 0.12) !important; /* st.data_editor 테두리와 일치 */
            border-radius: 8px !important;
            background-color: #0e1117 !important;
        }

        .custom-grid-table {
            width: 100% !important;
            border-collapse: collapse !important;
            font-size: 0.83rem !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
            color: #fafafa !important;
            background-color: transparent !important;
        }

        /* ⚡ 4. st.data_editor 헤더와 100% 동일한 반투명 다크 톤 및 테두리 */
        .custom-grid-table th {
            background-color: rgba(255, 255, 255, 0.04) !important; /* data_editor 헤더 색상 */
            color: #a1a1aa !important;
            font-weight: 500 !important;
            padding: 8px 12px !important;
            border-bottom: 1px solid rgba(250, 250, 250, 0.12) !important;
            border-right: 1px solid rgba(250, 250, 250, 0.06) !important;
            text-align: center !important;
            white-space: nowrap !important;
            letter-spacing: -0.01em;
        }

        /* ⚡ 5. st.data_editor 본문 행과 100% 동일한 톤 */
        .custom-grid-table td {
            background-color: transparent !important;
            color: #f4f4f5 !important;
            padding: 7px 12px !important;
            border-bottom: 1px solid rgba(250, 250, 250, 0.06) !important;
            border-right: 1px solid rgba(250, 250, 250, 0.06) !important;
            white-space: nowrap !important;
            font-variant-numeric: tabular-nums;
        }

        /* 호버 시 행 하이라이트 */
        .custom-grid-table tr:hover td {
            background-color: rgba(255, 255, 255, 0.03) !important;
        }

        /* 네이버 링크 스타일 */
        .naver-stock-link {
            color: #60a5fa !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        .naver-stock-link:hover {
            text-decoration: underline !important;
            color: #93c5fd !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df, *args, **kwargs):
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        st.info("표시할 데이터가 없습니다.")
        return

    header_rows = kwargs.get("header_rows", None)
    if not header_rows and args and isinstance(args[0], list):
        header_rows = args[0]

    divider_indices = kwargs.get("divider_indices", None)
    if not divider_indices and len(args) >= 2 and isinstance(args[1], list):
        divider_indices = args[1]
    div_set = set(divider_indices) if divider_indices else set()

    # 1. 헤더 (st.data_editor 헤더 색상과 동기화)
    thead_parts = ["<thead>"]
    if header_rows:
        for row in header_rows:
            thead_parts.append("<tr>")
            for cell in row:
                r_span = f' rowspan="{cell.get("rowspan", 1)}"' if cell.get("rowspan", 1) > 1 else ""
                c_span = f' colspan="{cell.get("colspan", 1)}"' if cell.get("colspan", 1) > 1 else ""
                txt = cell.get("text", "")
                thead_parts.append(f'<th{r_span}{c_span}>{txt}</th>')
            thead_parts.append("</tr>")
    else:
        thead_parts.append("<tr>")
        for c in df.columns:
            thead_parts.append(f'<th>{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 (st.data_editor 데이터 행 스타일과 동기화)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            # 구분선 열인 경우 우측 테두리 강조
            border_r = ' style="border-right: 2px solid rgba(250, 250, 250, 0.22) !important;"' if col_idx in div_set else ""

            # 종목명: 좌측 정렬 + 네이버 PC 링크
            if "종목명" in col_name:
                pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                link_html = f'<a href="{pc_url}" target="_blank" class="naver-stock-link">{val}</a>'
                tbody_parts.append(
                    f'<td style="text-align: left !important; padding-left: 14px !important;{border_r[7:]}">{link_html}</td>'
                )
                continue

            # 수치 컬러링 (+ 빨강, - 파랑)
            align_css = "text-align: center !important;"
            color_css = ""
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa !important; font-weight: 500;"

            style_attr = f'style="{align_css} {color_css}'
            if col_idx in div_set:
                style_attr += ' border-right: 2px solid rgba(250, 250, 250, 0.22) !important;'
            style_attr += '"'

            tbody_parts.append(f'<td {style_attr}>{val}</td>')

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    html_code = f"""
    <div class="custom-grid-container">
        <table class="custom-grid-table">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
