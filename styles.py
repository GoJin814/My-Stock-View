import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 1. Expander 텍스트 깨짐(keyboard_arrow_right) 완전 삭제 및 한 줄 출력 고정 */
        [data-testid="stExpander"] summary {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            padding: 8px 12px !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
        }

        /* 아이콘 폰트 텍스트 찌꺼기가 위로 튀어나오는 것 원천 숨김 */
        [data-testid="stExpander"] summary span:first-child,
        [data-testid="stExpander"] summary .material-symbols-rounded,
        [data-testid="stExpander"] summary .material-icons {
            font-size: 0px !important;
            line-height: 0 !important;
            width: 0 !important;
            height: 0 !important;
            color: transparent !important;
            display: none !important;
            visibility: hidden !important;
        }

        /* 정상적인 SVG 화살표만 작게 표시 */
        [data-testid="stExpander"] summary svg {
            display: inline-block !important;
            visibility: visible !important;
            width: 1rem !important;
            height: 1rem !important;
            margin-right: 6px !important;
            flex-shrink: 0 !important;
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

    # ⚡ 기본 탭(st.data_editor) 실제 렌더링 색상 토큰과 100% 동일하게 일치
    bg_table = "#0e1117"
    bg_th = "rgba(255, 255, 255, 0.04)"       # 기본 탭 헤더의 미세한 4% 반투명 다크 톤
    color_th = "#9ca3af"                     # 기본 탭 헤더 글자색
    color_td = "#f3f4f6"                     # 기본 탭 본문 글자색
    border_outer = "rgba(255, 255, 255, 0.08)"
    border_th_b = "rgba(255, 255, 255, 0.12)" # 헤더 하단 라인
    border_cell = "rgba(255, 255, 255, 0.04)" # 셀 사이 세로/가로 구분선
    border_div = "rgba(255, 255, 255, 0.22)"  # 직전/최근 구분 세로선

    # 1. 2단 복합 헤더 조립
    thead_parts = ["<thead>"]
    if header_rows:
        for row in header_rows:
            thead_parts.append("<tr>")
            for cell in row:
                r_span = f' rowspan="{cell.get("rowspan", 1)}"' if cell.get("rowspan", 1) > 1 else ""
                c_span = f' colspan="{cell.get("colspan", 1)}"' if cell.get("colspan", 1) > 1 else ""
                txt = cell.get("text", "")
                thead_parts.append(
                    f'<th{r_span}{c_span} style="background-color: {bg_th}; color: {color_th}; font-weight: 500; font-size: 0.81rem; padding: 7px 10px; border-bottom: 1px solid {border_th_b}; border-right: 1px solid {border_cell}; text-align: center; white-space: nowrap;">{txt}</th>'
                )
            thead_parts.append("</tr>")
    else:
        thead_parts.append("<tr>")
        for c in df.columns:
            thead_parts.append(
                f'<th style="background-color: {bg_th}; color: {color_th}; font-weight: 500; font-size: 0.81rem; padding: 7px 10px; border-bottom: 1px solid {border_th_b}; border-right: 1px solid {border_cell}; text-align: center; white-space: nowrap;">{c}</th>'
            )
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 조립 (종목명 좌측 정렬 및 폭 최소화, 글자색 동기화)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        
        code_val = ""
        if "종목코드" in df.columns:
            code_val = str(row["종목코드"]).strip().zfill(6)
        elif len(df.columns) > 1:
            code_val = str(row.iloc[1]).strip().zfill(6)

        for col_idx in range(len(df.columns)):
            raw_val = str(row.iloc[col_idx])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            # 구분선 열인 경우 우측 테두리 강조
            border_r = f"border-right: 2px solid {border_div} !important;" if col_idx in div_set else f"border-right: 1px solid {border_cell};"
            border_b = f"border-bottom: 1px solid {border_cell};"

            # ⚡ 0번째 열(종목명): 무조건 좌측 정렬 + 글자 크기만큼만 폭 최소화 (width: 1%)
            if col_idx == 0:
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" style="color: #58a6ff; text-decoration: none; font-weight: 500;">{val}</a>'
                else:
                    content = val

                tbody_parts.append(
                    f'<td style="background-color: {bg_table}; text-align: left !important; padding: 6px 12px !important; white-space: nowrap !important; width: 1% !important; {border_b} {border_r}">{content}</td>'
                )
                continue

            # 나머지 열: 중앙 정렬
            align_css = "text-align: center !important;"
            color_css = f"color: {color_td};"
            
            # 수치 컬러링 (+ 빨강, - 파랑)
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa !important; font-weight: 500;"

            tbody_parts.append(
                f'<td style="background-color: {bg_table}; {align_css} {color_css} padding: 6px 10px !important; white-space: nowrap !important; font-variant-numeric: tabular-nums; {border_b} {border_r}">{val}</td>'
            )

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    # 3. 마크다운 렌더링 (st.data_editor와 동일한 외곽 테두리 및 둥근 모서리)
    html_code = f"""
    <div style="overflow-x: auto; margin-bottom: 1.2rem; border-radius: 6px; border: 1px solid {border_outer}; background-color: {bg_table}; width: 100%;">
        <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 0.82rem;">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
