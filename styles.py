import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 1. 상단 expander의 '_arrow_right' 텍스트 겹침 버그 완전 제거 */
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

        /* 2. 탭 바 여백 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
        }

        /* ⚡ 3. 기본 탭과 100% 동일한 다크 그리드 (폭 최소화 & 배경 완전 일치) */
        .custom-grid-container {
            overflow-x: auto;
            margin-bottom: 1.2rem;
            display: block;
            width: 100%;
        }

        .custom-grid-table {
            width: auto !important; /* 화면 100% 강제 확장을 막고 데이터 폭에 딱 맞춤 */
            border-collapse: separate !important;
            border-spacing: 0 !important;
            font-size: 0.82rem !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            background-color: #0e1117 !important;
            color: #fafafa !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 4px !important;
        }

        /* ⚡ 기본 탭 헤더와 100% 똑같은 칠흑색 헤더 */
        .custom-grid-table th {
            background-color: #0e1117 !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        .custom-grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            white-space: nowrap !important;
        }

        /* 행 마우스 오버 효과 */
        .custom-grid-table tr:hover td {
            background-color: #161a22 !important;
        }

        /* 네이버 PC 링크 스타일 (기본 탭 링크색과 동기화) */
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

    # 인자 추출
    header_rows = kwargs.get("header_rows", None)
    if not header_rows and args and isinstance(args[0], list):
        header_rows = args[0]

    divider_indices = kwargs.get("divider_indices", None)
    if not divider_indices and len(args) >= 2 and isinstance(args[1], list):
        divider_indices = args[1]
    div_set = set(divider_indices) if divider_indices else set()

    # 1. 2단 복합 헤더 조립 (배경색 완전 일치)
    thead_parts = ["<thead>"]
    if header_rows:
        for row in header_rows:
            thead_parts.append('<tr style="background-color: #0e1117;">')
            for cell in row:
                r_span = f' rowspan="{cell.get("rowspan", 1)}"' if cell.get("rowspan", 1) > 1 else ""
                c_span = f' colspan="{cell.get("colspan", 1)}"' if cell.get("colspan", 1) > 1 else ""
                txt = cell.get("text", "")
                thead_parts.append(
                    f'<th{r_span}{c_span} style="background-color: #0e1117; color: #9ca3af; border: 1px solid rgba(255,255,255,0.1); padding: 6px 10px; text-align: center;">{txt}</th>'
                )
            thead_parts.append("</tr>")
    else:
        thead_parts.append('<tr style="background-color: #0e1117;">')
        for c in df.columns:
            thead_parts.append(f'<th style="background-color: #0e1117; color: #9ca3af; border: 1px solid rgba(255,255,255,0.1); padding: 6px 10px; text-align: center;">{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 조립 (종목명 좌측 정렬 & PC 링크 & 컴팩트 여백 강제 적용)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            # 우측 구분선(BPS/순익 뒤 강조)
            border_r = "border-right: 2px solid rgba(255, 255, 255, 0.25) !important;" if col_idx in div_set else "border-right: 1px solid rgba(255, 255, 255, 0.06);"
            border_b = "border-bottom: 1px solid rgba(255, 255, 255, 0.06);"

            # ⚡ 종목명 열: 왼쪽 정렬 (text-align: left) + 네이버 PC 웹 링크
            if "종목명" in col_name:
                pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                link_html = f'<a href="{pc_url}" target="_blank" class="naver-stock-link">{val}</a>'
                tbody_parts.append(
                    f'<td style="background-color: #0e1117; text-align: left !important; padding: 6px 12px !important; {border_b} {border_r}">{link_html}</td>'
                )
                continue

            # 나머지 수치 열: 중앙 정렬
            align_css = "text-align: center !important;"
            color_css = "color: #f3f4f6;"
            
            # 수치 색상 강조 (+ 빨강, - 파랑)
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171; font-weight: 500;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa; font-weight: 500;"

            tbody_parts.append(
                f'<td style="background-color: #0e1117; {align_css} {color_css} padding: 6px 10px !important; {border_b} {border_r}">{val}</td>'
            )

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    # 3. HTML 마크다운 렌더링
    html_code = f"""
    <div class="custom-grid-container">
        <table class="custom-grid-table">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
