import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 1. Expander 제목 복원 및 태블릿 _arrow_right 아이콘 텍스트 찌꺼기만 정밀 제거 */
        [data-testid="stExpander"] summary svg {
            display: inline-block !important;
            visibility: visible !important;
            min-width: 1.1rem !important;
            min-height: 1.1rem !important;
        }
        
        /* 폰트 깨짐으로 인한 문자열 누출만 투명화 */
        [data-testid="stExpander"] summary .material-symbols-rounded,
        [data-testid="stExpander"] summary .material-icons {
            font-size: 0px !important;
            letter-spacing: -999px !important;
            color: transparent !important;
        }

        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span {
            display: inline !important;
            visibility: visible !important;
            color: #fafafa !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
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
    bg_th = "rgba(255, 255, 255, 0.05)"  # 기본 탭 헤더 반투명 다크 톤
    border_color = "rgba(250, 250, 250, 0.08)" # 기본 탭 셀 구분선

    # 1. 헤더 조립
    thead_parts = ["<thead>"]
    if header_rows:
        for row in header_rows:
            thead_parts.append("<tr>")
            for cell in row:
                r_span = f' rowspan="{cell.get("rowspan", 1)}"' if cell.get("rowspan", 1) > 1 else ""
                c_span = f' colspan="{cell.get("colspan", 1)}"' if cell.get("colspan", 1) > 1 else ""
                txt = cell.get("text", "")
                thead_parts.append(
                    f'<th{r_span}{c_span} style="background-color: {bg_th}; color: #a1a1aa; font-weight: 500; font-size: 0.81rem; padding: 7px 10px; border-bottom: 1px solid {border_color}; border-right: 1px solid {border_color}; text-align: center; white-space: nowrap;">{txt}</th>'
                )
            thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 조립 (종목명 무조건 좌측 정렬 및 너비 최소화)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        tbody_parts.append("<tr>")
        
        # 종목코드 추출 (두 번째 컬럼 또는 '종목코드' 키)
        code_val = ""
        if "종목코드" in df.columns:
            code_val = str(row["종목코드"]).strip().zfill(6)
        elif len(df.columns) > 1:
            code_val = str(row.iloc[1]).strip().zfill(6)

        for col_idx in range(len(df.columns)):
            raw_val = str(row.iloc[col_idx])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            # 구분선 열인 경우 강조 테두리
            border_r = "border-right: 2px solid rgba(250, 250, 250, 0.22) !important;" if col_idx in div_set else f"border-right: 1px solid {border_color};"
            border_b = f"border-bottom: 1px solid {border_color};"

            # ⚡ 0번째 열(종목명): 무조건 좌측 정렬(text-align: left) + 폭 최소화(width: 1%)
            if col_idx == 0:
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" style="color: #60a5fa; text-decoration: none; font-weight: 500;">{val}</a>'
                else:
                    content = val

                tbody_parts.append(
                    f'<td style="background-color: #0e1117; text-align: left !important; padding: 6px 12px !important; white-space: nowrap !important; width: 1% !important; {border_b} {border_r}">{content}</td>'
                )
                continue

            # 나머지 열: 중앙 정렬
            align_css = "text-align: center !important;"
            color_css = "color: #f4f4f5;"
            
            # 수치 컬러링 (+ 빨강, - 파랑)
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa !important; font-weight: 500;"

            tbody_parts.append(
                f'<td style="background-color: #0e1117; {align_css} {color_css} padding: 6px 10px !important; white-space: nowrap !important; font-variant-numeric: tabular-nums; {border_b} {border_r}">{val}</td>'
            )

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    # 3. 마크다운 렌더링 (st.data_editor와 완전히 동일한 외곽 테두리 및 레이아웃)
    html_code = f"""
    <div style="overflow-x: auto; margin-bottom: 1.2rem; border-radius: 6px; border: 1px solid {border_color}; background-color: #0e1117; width: 100%;">
        <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 0.82rem;">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
