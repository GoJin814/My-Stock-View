import streamlit as st
import pandas as pd
import re

def apply_custom_styles():
    st.markdown("""
        <style>
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            overscroll-behavior-y: auto !important;
            touch-action: pan-y pinch-zoom !important;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

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

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
        }

        .custom-grid-wrapper {
            overflow-x: auto;
            margin-bottom: 1.2rem;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background-color: #0e1117;
            width: 100%;
        }

        .custom-grid-table {
            width: 100%;
            border-collapse: collapse;
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
        }

        /* ⚡ 정렬 헤더 링크 스타일 */
        .th-sort-link {
            color: #9ca3af !important;
            text-decoration: none !important;
            display: block !important;
            width: 100% !important;
            height: 100% !important;
        }
        .th-sort-link:hover {
            color: #ffffff !important;
        }
        .th-sort-active {
            color: #60a5fa !important;
            font-weight: 600 !important;
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

        /* 종목명 120px 고정 */
        .custom-grid-table th.col-name-th,
        .custom-grid-table td.col-name {
            width: 120px !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: left !important;
            padding-left: 12px !important;
            padding-right: 8px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .custom-grid-table tr:hover td {
            background-color: rgba(255, 255, 255, 0.03) !important;
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

def parse_num_for_sort(val):
    if pd.isna(val) or val in ["", "-", "N/A", "nan", "None"]:
        return -999999999999.0
    val_str = str(val).strip()
    clean = re.sub(r'[,%원배\s]', '', val_str)
    
    # 조, 억 복합 수치 변환
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
    tab_key = kwargs.get("tab_key", "t")

    # 1. 쿼리 파라미터에서 현재 정렬 상태 읽기
    qp = st.query_params
    cur_sort = qp.get(f"{tab_key}_sort", "")
    cur_order = qp.get(f"{tab_key}_order", "desc")

    # 2. 데이터프레임 파이썬 직접 정렬
    sorted_df = df.copy()
    if cur_sort and cur_sort in sorted_df.columns:
        is_asc = (cur_order == "asc")
        # 숫자 정렬용 키 시리즈 생성
        num_series = sorted_df[cur_sort].apply(parse_num_for_sort)
        if (num_series != -999999999999.0).any():
            sorted_df["_sort_key"] = num_series
            sorted_df = sorted_df.sort_values(by="_sort_key", ascending=is_asc).drop(columns=["_sort_key"])
        else:
            sorted_df = sorted_df.sort_values(by=cur_sort, ascending=is_asc)

    # 3. 헤더 조립 (각 헤더 항목에 정렬 링크 생성)
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
                data_col = cell.get("col", None)

                th_class = ' class="col-name-th"' if (r_idx == 0 and txt == "종목명") else ""

                # 정렬 가능한 하단 세부 열이거나 단독 열
                if data_col and (r_span_val > 1 or c_span_val == 1):
                    next_order = "desc" if (cur_sort == data_col and cur_order == "asc") else "asc"
                    arrow = ""
                    active_class = ""
                    if cur_sort == data_col:
                        arrow = " ▲" if cur_order == "asc" else " ▼"
                        active_class = " th-sort-active"

                    header_content = f'<a href="?{tab_key}_sort={data_col}&{tab_key}_order={next_order}" target="_self" class="th-sort-link{active_class}">{txt}{arrow}</a>'
                else:
                    header_content = txt

                thead_parts.append(f'<th{r_span}{c_span}{th_class}>{header_content}</th>')
            thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 4. 본문 조립
    tbody_parts = ["<tbody>"]
    for _, row in sorted_df.iterrows():
        tbody_parts.append("<tr>")
        code_val = str(row.get("종목코드", "")).strip().zfill(6)

        for col_idx, col_name in enumerate(sorted_df.columns):
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
