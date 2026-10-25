import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 1. 태블릿 브라우저 Material Symbols 텍스트 깨짐(_arrow_right) 원천 차단 */
        [data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"],
        [data-testid="stExpander"] summary span:has(svg),
        [data-testid="stExpander"] summary .material-symbols-rounded,
        [data-testid="stExpander"] summary .material-icons,
        [data-testid="stExpander"] summary span[translate="no"] {
            font-size: 0px !important;
            line-height: 0 !important;
            letter-spacing: -9999px !important;
            color: transparent !important;
            user-select: none !important;
        }
        
        /* Expander 화살표 SVG는 정상 표시되도록 크기 복구 */
        [data-testid="stExpander"] summary svg {
            font-size: 1.2rem !important;
            letter-spacing: normal !important;
            color: inherit !important;
            width: 1.2rem !important;
            height: 1.2rem !important;
            display: inline-block !important;
        }

        [data-testid="stExpander"] summary {
            font-weight: 500 !important;
            padding: 8px 12px !important;
            display: flex !important;
            align-items: center !important;
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

        /* ⚡ 3. 기본 탭과 100% 동일한 다크 그리드 (태블릿 다크모드 강제 덮어쓰기) */
        .custom-grid-container {
            overflow-x: auto;
            margin-bottom: 1.2rem;
            display: block;
            width: 100%;
            background-color: #0e1117 !important;
        }

        .custom-grid-table {
            width: auto !important;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            font-size: 0.82rem !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            background-color: #0e1117 !important;
            color: #fafafa !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 4px !important;
        }

        /* ⚡ 기본 탭 헤더와 동일하게 칠흑색(#0e1117) 강제 */
        .custom-grid-table thead,
        .custom-grid-table thead tr,
        .custom-grid-table th {
            background: #0e1117 !important;
            background-color: #0e1117 !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        .custom-grid-table tbody,
        .custom-grid-table tbody tr,
        .custom-grid-table td {
            background: #0e1117 !important;
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            white-space: nowrap !important;
        }

        .custom-grid-table tr:hover td {
            background-color: #161a22 !important;
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

    # 1. 헤더 조립 (인라인 스타일에도 순수 검정 배경 명시)
    thead_parts = ['<thead style="background-color: #0e1117 !important;">']
    if header_rows:
        for row in header_rows:
            thead_parts.append('<tr style="background-color: #0e1117 !important;">')
            for cell in row:
                r_span = f' rowspan="{cell.get("rowspan", 1)}"' if cell.get("rowspan", 1) > 1 else ""
                c_span = f' colspan="{cell.get("colspan", 1)}"' if cell.get("colspan", 1) > 1 else ""
                txt = cell.get("text", "")
                thead_parts.append(
                    f'<th{r_span}{c_span} style="background-color: #0e1117 !important; color: #9ca3af !important; border: 1px solid rgba(255,255,255,0.1) !important; padding: 6px 10px !important; text-align: center !important;">{txt}</th>'
                )
            thead_parts.append("</tr>")
    else:
        thead_parts.append('<tr style="background-color: #0e1117 !important;">')
        for c in df.columns:
            thead_parts.append(f'<th style="background-color: #0e1117 !important; color: #9ca3af !important; border: 1px solid rgba(255,255,255,0.1) !important; padding: 6px 10px !important; text-align: center !important;">{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 조립
    tbody_parts = ['<tbody style="background-color: #0e1117 !important;">']
    for _, row in df.iterrows():
        tbody_parts.append('<tr style="background-color: #0e1117 !important;">')
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            border_r = "border-right: 2px solid rgba(255, 255, 255, 0.25) !important;" if col_idx in div_set else "border-right: 1px solid rgba(255, 255, 255, 0.06) !important;"
            border_b = "border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;"

            # 종목명: 좌측 정렬 + 네이버 PC 링크
            if "종목명" in col_name:
                pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                link_html = f'<a href="{pc_url}" target="_blank" class="naver-stock-link">{val}</a>'
                tbody_parts.append(
                    f'<td style="background-color: #0e1117 !important; text-align: left !important; padding: 6px 12px !important; {border_b} {border_r}">{link_html}</td>'
                )
                continue

            align_css = "text-align: center !important;"
            color_css = "color: #f3f4f6 !important;"
            
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171 !important; font-weight: 500 !important;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa !important; font-weight: 500 !important;"

            tbody_parts.append(
                f'<td style="background-color: #0e1117 !important; {align_css} {color_css} padding: 6px 10px !important; {border_b} {border_r}">{val}</td>'
            )

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
