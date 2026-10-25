import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        /* ⚡ 1. 모바일(웨일/크롬) 아래로 스와이프 당겨서 새로고침(Pull-to-refresh) 강제 허용 */
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            overscroll-behavior-y: auto !important;
            touch-action: pan-y pinch-zoom !important;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 2. Expander 제목 복원 & keyboard_arrow_right 문자열 찌꺼기 원천 차단 */
        [data-testid="stExpander"] summary {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            padding: 8px 12px !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            color: #fafafa !important;
            cursor: pointer !important;
        }

        /* 머티리얼 심볼 폰트 깨짐 텍스트만 안 보이게 격리 */
        [data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"] span,
        [data-testid="stExpander"] summary .material-symbols-rounded,
        [data-testid="stExpander"] summary .material-icons {
            font-size: 0px !important;
            color: transparent !important;
            letter-spacing: -9999px !important;
            display: none !important;
        }

        [data-testid="stExpander"] summary svg {
            display: inline-block !important;
            width: 1rem !important;
            height: 1rem !important;
            min-width: 1rem !important;
            margin-right: 8px !important;
            fill: #fafafa !important;
        }

        /* Expander 본문 텍스트 강제 표시 */
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary div,
        [data-testid="stExpander"] summary > span:last-child {
            display: inline-block !important;
            visibility: visible !important;
            color: #fafafa !important;
            font-size: 0.92rem !important;
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

        /* ⚡ 3. 기본 탭(st.data_editor)과 100% 동일한 그리드 서식 강제 고정 */
        .grid-wrapper {
            width: 100% !important;
            overflow-x: auto !important;
            margin-bottom: 1.2rem !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 4px !important;
            background-color: #0e1117 !important;
        }

        table.grid-table {
            width: max-content !important; /* 화면 억지 확장 방지 */
            min-width: 100% !important;
            border-collapse: collapse !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 0.82rem !important;
            background-color: #0e1117 !important;
        }

        /* 기본 탭 헤더: 미세한 4% 반투명 다크 톤 */
        table.grid-table th {
            background-color: rgba(255, 255, 255, 0.04) !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            font-size: 0.81rem !important;
            padding: 7px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
            text-align: center !important;
            white-space: nowrap !important;
        }

        /* 기본 탭 데이터 셀 */
        table.grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
            white-space: nowrap !important;
            text-align: center !important;
            font-variant-numeric: tabular-nums !important;
        }

        /* ⚡ 종목명 열: 무조건 왼쪽 정렬 + 폭 최소화 */
        table.grid-table td.col-stock-name {
            text-align: left !important;
            padding-left: 14px !important;
            padding-right: 14px !important;
            width: 1% !important;
            white-space: nowrap !important;
        }

        table.grid-table tr:hover td {
            background-color: rgba(255, 255, 255, 0.03) !important;
        }

        /* 네이버 링크 스타일 */
        .naver-link {
            color: #58a6ff !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        .naver-link:hover {
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

    # 1. 2단 헤더 구성
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

    # 2. 본문 행 구성 (클래스 기반 강제 스타일 바인딩)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            # 우측 구분선 클래스/스타일
            extra_style = "border-right: 2px solid rgba(255, 255, 255, 0.22) !important;" if col_idx in div_set else ""

            # ⚡ 0번째 열(종목명): col-stock-name 클래스 부여로 왼쪽 정렬 및 폭 최소화
            if col_idx == 0:
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" class="naver-link">{val}</a>'
                else:
                    content = val

                style_attr = f'style="{extra_style}"' if extra_style else ""
                tbody_parts.append(f'<td class="col-stock-name" {style_attr}>{content}</td>')
                continue

            # 수치 컬러링 (+ 빨강, - 파랑)
            color_style = ""
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_style = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_style = "color: #60a5fa !important; font-weight: 500;"

            style_combined = f"{color_style} {extra_style}".strip()
            style_attr = f'style="{style_combined}"' if style_combined else ""

            tbody_parts.append(f'<td {style_attr}>{val}</td>')

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    # 3. HTML 렌더링
    html_code = f"""
    <div class="grid-wrapper">
        <table class="grid-table">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
