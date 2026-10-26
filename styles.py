import streamlit as st
import pandas as pd
import re

def apply_custom_styles():
    st.markdown("""
        <style>
        /* 1. 모바일 당겨서 새로고침 허용 */
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            overscroll-behavior-y: auto !important;
            touch-action: pan-y pinch-zoom !important;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* 2. Expander 글자 겹침 방지 */
        [data-testid="stExpander"] summary {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 6px !important;
            padding: 8px 12px !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            color: #fafafa !important;
            white-space: nowrap !important;
            overflow: hidden !important;
        }

        [data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"] {
            font-size: 0 !important;
            line-height: 0 !important;
            color: transparent !important;
            width: 1.1rem !important;
            height: 1.1rem !important;
            min-width: 1.1rem !important;
            overflow: hidden !important;
        }

        [data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"] svg {
            display: inline-block !important;
            width: 1.1rem !important;
            height: 1.1rem !important;
            fill: #fafafa !important;
            color: #fafafa !important;
        }

        /* 3. 탭 바 여백 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
            font-size: 0.92rem !important;
        }

        /* 4. 그리드 컨테이너 */
        .custom-grid-wrapper {
            overflow-x: auto !important;
            margin-bottom: 1.2rem;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background-color: #0e1117;
            width: 100%;
            -webkit-overflow-scrolling: touch;
        }

        .custom-grid-table {
            width: max-content !important;
            min-width: 100% !important;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            font-size: 0.82rem;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #f3f4f6;
            background-color: #0e1117;
        }

        .custom-grid-table th {
            background-color: rgba(255, 255, 255, 0.04) !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            font-size: 0.81rem !important;
            padding: 7px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
            text-align: center !important;
            white-space: nowrap !important;
            user-select: none !important;
        }

        /* ⚡ 정렬 헤더 링크 스타일 */
        .th-sort-link {
            color: #9ca3af !important;
            text-decoration: none !important;
            display: inline-block !important;
            width: 100% !important;
            cursor: pointer !important;
        }
        .th-sort-link:hover {
            color: #60a5fa !important;
        }
        .th-sort-active {
            color: #60a5fa !important;
            font-weight: 700 !important;
        }

        .custom-grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
            white-space: nowrap !important;
            text-align: center !important;
            font-variant-numeric: tabular-nums !important;
        }

        /* 5. 종목명 120px 좌측 고정 (Sticky) */
        .custom-grid-table th.col-name-th {
            position: sticky !important;
            left: 0 !important;
            z-index: 3 !important;
            background-color: #171b22 !important;
            width: 120px !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: left !important;
            padding-left: 12px !important;
            box-shadow: 2px 0 5px rgba(0, 0, 0, 0.4) !important;
        }

        .custom-grid-table td.col-name {
            position: sticky !important;
            left: 0 !important;
            z-index: 2 !important;
            background-color: #0e1117 !important;
            width: 120px !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: left !important;
            padding-left: 12px !important;
            padding-right: 8px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            box-shadow: 2px 0 5px rgba(0, 0, 0, 0.4) !important;
        }

        .custom-grid-table tr:hover td {
            background-color: rgba(255, 255, 255, 0.03) !important;
        }
        .custom-grid-table tr:hover td.col-name {
            background-color: #161a22 !important;
        }

        .naver-pc-link {
            color: #58a6ff !important;
            text-decoration: none !important;
            font-weight: 500 !important;
        }
        .naver-pc-link:hover {
            text-decoration: underline !important;
            color: #79b8ff !important;
        }
        </style>
    """, unsafe_allow_html=True)

def parse_val_to_num(v):
    """원, 배, %, 억, 조 단위 문자열을 정렬 가능한 실수(float)로 변환"""
    if pd.isna(v) or v in ["", "-", "N/A", "nan", "None"]:
        return -999999999999.0
    val_str = str(v).strip()
    clean = re.sub(r'[,%원배\s]', '', val_str)
    
    if '조' in clean:
        parts = clean.split('조')
        jo = float(re.sub(r'[^0-9.-]', '', parts[0])) if parts[0] else 0.0
        rest = float(re.sub(r'[^0-9.-]', '', parts[1].replace('억', ''))) if len(parts) > 1 and parts[1] else 0.0
        return (jo * 10000.0) + rest
    elif '억' in clean:
        clean = clean.replace('억', '')
        return float(re.sub(r'[^0-9.-]', '', clean)) if clean else 0.0
        
    try:
        return float(re.sub(r'[^0-9.-]', '', clean))
    except Exception:
        return -999999999999.0

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
    tab_name = kwargs.get("tab_name", "basic")

    # 1. 쿼리 파라미터에서 현재 정렬 상태 확인
    qp = st.query_params
    cur_sort_col = qp.get("sort_col", "")
    cur_sort_order = qp.get("sort_order", "desc")

    # 2. 2단 복합 헤더 조립
    thead_parts = ["<thead>"]
    if header_rows:
        for r_idx, row in enumerate(header_rows):
            thead_parts.append("<tr>")
            for cell in row:
                r_span_val = cell.get("rowspan", 1)
                c_span_val = cell.get("colspan", 1)
                r_span = f' rowspan="{r_span_val}"' if r_span_val > 1 else ""
                c_span = f' colspan="{c_span_val}"' if c_span_val > 1 else ""
                txt = cell.get("text", "")
                target_col = cell.get("col", None)

                th_class = ' class="col-name-th"' if (r_idx == 0 and txt == "종목명") else ""

                if target_col:
                    next_order = "desc" if (cur_sort_col == target_col and cur_sort_order == "asc") else "asc"
                    arrow = ""
                    active_cls = ""
                    if cur_sort_col == target_col:
                        arrow = " ▲" if cur_sort_order == "asc" else " ▼"
                        active_cls = " th-sort-active"

                    header_content = f'<a href="?sort_col={target_col}&sort_order={next_order}&tab={tab_name}" target="_self" class="th-sort-link{active_cls}">{txt}{arrow}</a>'
                else:
                    header_content = txt

                thead_parts.append(f'<th{r_span}{c_span}{th_class}>{header_content}</th>')
            thead_parts.append("</tr>")
    else:
        thead_parts.append("<tr>")
        for c in df.columns:
            th_class = ' class="col-name-th"' if c == "종목명" else ""
            thead_parts.append(f'<th{th_class}>{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 3. 본문 조립
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        code_val = str(row.get("종목코드", "")).strip().zfill(6)
        tbody_parts.append("<tr>")

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val

            border_r = "border-right: 2px solid rgba(255, 255, 255, 0.22) !important;" if col_idx in div_set else ""

            if col_idx == 0:
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" class="naver-pc-link">{val}</a>'
                else:
                    content = val

                style_attr = f'style="{border_r}"' if border_r else ""
                tbody_parts.append(f'<td class="col-name" {style_attr}>{content}</td>')
                continue

            color_css = ""
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa !important; font-weight: 500;"

            style_combined = f"{color_css} {border_r}".strip()
            style_attr = f'style="{style_combined}"' if style_combined else ""

            tbody_parts.append(f'<td {style_attr}>{val}</td>')

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    html_code = f"""
    <div class="custom-grid-wrapper">
        <table class="custom-grid-table">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
