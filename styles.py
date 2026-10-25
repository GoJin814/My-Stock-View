import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 1. 태블릿 브라우저 '_arrow_right' 텍스트 겹침 버그 강제 소멸 */
        details summary svg,
        details summary span:first-child,
        [data-testid="stExpander"] summary svg,
        [data-testid="stExpander"] summary span:first-child {
            display: none !important;
            visibility: hidden !important;
            font-size: 0 !important;
            width: 0 !important;
            height: 0 !important;
            line-height: 0 !important;
        }

        /* Expander 타이틀 여백 및 정돈 */
        [data-testid="stExpander"] summary {
            padding: 10px 14px !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            border-radius: 6px !important;
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

        /* ⚡ 2. 기본 탭(st.data_editor)과 100% 동일한 컨테이너 및 테이블 */
        .custom-grid-container {
            overflow-x: auto;
            margin-bottom: 1.2rem;
            border-radius: 4px;
            border: 1px solid rgba(250, 250, 250, 0.12);
            background-color: #0e1117;
            display: block;
            width: 100%;
        }

        .custom-grid-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #fafafa;
            background-color: #0e1117;
        }

        /* 기본 탭과 완전히 동일한 헤더 서식 */
        .custom-grid-table th {
            background-color: #14171f !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            padding: 8px 10px !important;
            border-bottom: 1px solid rgba(250, 250, 250, 0.15) !important;
            border-right: 1px solid rgba(250, 250, 250, 0.08) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        /* 기본 탭과 완전히 동일한 데이터 행 서식 */
        .custom-grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 7px 10px !important;
            border-bottom: 1px solid rgba(250, 250, 250, 0.06) !important;
            border-right: 1px solid rgba(250, 250, 250, 0.06) !important;
            white-space: nowrap !important;
            text-align: center;
        }

        .custom-grid-table tr:hover td {
            background-color: #1a1e27 !important;
        }

        /* 네이버 PC 링크 스타일 */
        .naver-stock-link {
            color: #58a6ff !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        .naver-stock-link:hover {
            text-decoration: underline !important;
            color: #79b8ff !important;
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

    has_naver_link = kwargs.get("has_naver_link", True)

    # 1. 2단 복합 헤더 생성
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

    # 2. 본문 생성 (종목명 좌측 정렬 & PC 링크)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            border_r = "border-right: 2px solid rgba(250, 250, 250, 0.22) !important;" if col_idx in div_set else ""

            # 종목명 열 좌측 정렬 및 링크 연결
            if "종목명" in col_name:
                pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                link_html = f'<a href="{pc_url}" target="_blank" class="naver-stock-link">{val}</a>' if has_naver_link and code_val else val
                tbody_parts.append(f'<td style="text-align: left !important; padding-left: 14px !important; {border_r}">{link_html}</td>')
                continue

            # 수치 컬러링 (+ 빨강, - 파랑)
            color_style = ""
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_style = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_style = "color: #60a5fa !important; font-weight: 500;"

            tbody_parts.append(f'<td style="{color_style} {border_r}">{val}</td>')

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
