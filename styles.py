import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
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
        
        /* 기본 탭(Glide Data Grid)과 완전 일치된 컨테이너 */
        .custom-grid-container {
            overflow-x: auto;
            margin-bottom: 1.2rem;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background-color: #0e1117;
        }

        .custom-grid-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.82rem;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #fafafa;
        }

        /* 기본 탭과 동일한 헤더 톤 */
        .custom-grid-table th {
            background-color: #1e2129 !important;
            color: #d1d5db !important;
            font-weight: 500 !important;
            padding: 8px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        .custom-grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 7px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        /* 행 마우스 오버 시 기본 탭과 동일한 하이라이트 */
        .custom-grid-table tr:hover td {
            background-color: #181c24 !important;
        }

        /* 네이버 링크 스타일 (기본 탭 링크 컬러와 동기화) */
        .naver-stock-link {
            color: #60a5fa !important;
            text-decoration: none !important;
            font-weight: 500;
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

    # 인자 추출
    header_rows = kwargs.get("header_rows", None)
    if not header_rows and args and isinstance(args[0], list):
        header_rows = args[0]

    divider_indices = kwargs.get("divider_indices", None)
    if not divider_indices and len(args) >= 2 and isinstance(args[1], list):
        divider_indices = args[1]
    div_set = set(divider_indices) if divider_indices else set()

    has_naver_link = kwargs.get("has_naver_link", True)

    # 1. 복합 헤더 렌더링
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

    # 2. 본문 행 렌더링
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            # 우측 구분선 강조 열 체크
            border_r = ' style="border-right: 2px solid rgba(255, 255, 255, 0.22) !important;"' if col_idx in div_set else ""

            # 종목명 컬럼인 경우 네이버 PC 웹 링크 연결
            if col_name == "종목명" and has_naver_link and code_val:
                pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                cell_content = f'<a href="{pc_url}" target="_blank" class="naver-stock-link">{val}</a>'
                tbody_parts.append(f'<td{border_r}>{cell_content}</td>')
                continue

            # YoY 수치 컬러링
            if "%" in val and not val.startswith("-") and val != "-":
                if val.startswith("+"):
                    cell_content = f'<span style="color: #f87171; font-weight: 500;">{val}</span>'
                else:
                    cell_content = val
            elif val.startswith("-") and "%" in val and val != "-":
                cell_content = f'<span style="color: #60a5fa; font-weight: 500;">{val}</span>'
            else:
                cell_content = val

            tbody_parts.append(f'<td{border_r}>{cell_content}</td>')

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
