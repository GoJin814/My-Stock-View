import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* 1. 상단 expander 접기 아이콘 텍스트 겹침 버그(_arrow_right) 수정 */
        [data-testid="stExpander"] summary span {
            display: inline-flex !important;
            align-items: center !important;
        }
        [data-testid="stExpander"] summary svg {
            margin-right: 8px !important;
        }
        [data-testid="stExpanderToggleIcon"] {
            user-select: none !important;
        }

        /* 2. 탭 바 여백 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
        }

        /* 3. 기본 탭과 100% 일치된 컴팩트 다크 그리드 컨테이너 */
        .custom-grid-container {
            overflow-x: auto;
            margin-bottom: 1.2rem;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.09);
            background-color: #0e1117;
            display: inline-block;
            max-width: 100%;
        }

        .custom-grid-table {
            width: max-content; /* 테이블 폭 최소화 (데이터 길이에 맞춤) */
            min-width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.82rem;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #fafafa;
            background-color: #0e1117;
        }

        /* 4. 기본 탭과 완벽히 동일한 헤더 배경 및 라인 */
        .custom-grid-table th {
            background-color: #12151c !important; /* 기본 탭과 일치된 톤 */
            color: #9ca3af !important;
            font-weight: 500 !important;
            padding: 7px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        .custom-grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        /* 마우스 호버 효과 */
        .custom-grid-table tr:hover td {
            background-color: #1a1e27 !important;
        }

        /* 네이버 링크 스타일 */
        .naver-stock-link {
            color: #58a6ff !important;
            text-decoration: none !important;
            font-weight: 500;
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

    # 2. 본문 행 생성 (종목명 좌측 정렬 및 폭 최소화)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            # 우측 구분선
            border_r = "border-right: 2px solid rgba(255, 255, 255, 0.22) !important;" if col_idx in div_set else ""

            # 종목명 컬럼은 좌측 정렬(text-align: left) 및 네이버 PC 링크 연결
            if col_name == "종목명":
                align_style = "text-align: left !important; padding-left: 14px !important;"
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" class="naver-stock-link">{val}</a>'
                else:
                    content = val
                tbody_parts.append(f'<td style="{align_style} {border_r}">{content}</td>')
                continue

            # 증감률 컬러링
            align_style = "text-align: center !important;"
            if "%" in val and not val.startswith("-") and val != "-":
                if val.startswith("+"):
                    content = f'<span style="color: #f87171; font-weight: 500;">{val}</span>'
                else:
                    content = val
            elif val.startswith("-") and "%" in val and val != "-":
                content = f'<span style="color: #60a5fa; font-weight: 500;">{val}</span>'
            else:
                content = val

            tbody_parts.append(f'<td style="{align_style} {border_r}">{content}</td>')

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
