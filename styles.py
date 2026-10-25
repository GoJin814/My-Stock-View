import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def apply_custom_styles():
    st.markdown("""
        <style>
        /* 1. 모바일(웨일/크롬) 아래로 당겨 새로고침 제스처 허용 */
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

        /* 4. 기본 탭과 통일된 외형 + 가로 스크롤 컨테이너 */
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

        .custom-grid-table th.sortable-th {
            cursor: pointer !important;
            transition: background-color 0.15s ease, color 0.15s ease;
        }
        .custom-grid-table th.sortable-th:hover {
            background-color: rgba(255, 255, 255, 0.09) !important;
            color: #60a5fa !important;
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

        /* 5. 종목명 열 좌측 고정 (120px) */
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

def render_multi_header_table(df, *args, **kwargs):
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        st.info("표시할 데이터가 없습니다.")
        return None

    header_rows = kwargs.get("header_rows", None)
    if not header_rows and args and isinstance(args[0], list):
        header_rows = args[0]

    divider_indices = kwargs.get("divider_indices", None)
    if not divider_indices and len(args) >= 2 and isinstance(args[1], list):
        divider_indices = args[1]
    div_set = set(divider_indices) if divider_indices else set()

    has_naver_link = kwargs.get("has_naver_link", True)
    tab_key = kwargs.get("tab_key", "tbl")
    table_id = tab_key + "_custom_grid"

    # 1. 2단 복합 헤더 조립
    thead_parts = ["<thead>"]
    if header_rows:
        for r_idx, row in enumerate(header_rows):
            thead_parts.append("<tr>")
            col_seq = 0 if r_idx == 0 else 2
            for cell in row:
                r_span_val = cell.get("rowspan", 1)
                c_span_val = cell.get("colspan", 1)
                r_span = f' rowspan="{r_span_val}"' if r_span_val > 1 else ""
                c_span = f' colspan="{c_span_val}"' if c_span_val > 1 else ""
                txt = cell.get("text", "")

                th_classes = []
                th_attrs = ""

                if r_idx == 0 and txt == "종목명":
                    th_classes.append("col-name-th")

                if r_span_val > 1 or c_span_val == 1:
                    th_classes.append("sortable-th")
                    th_attrs = f' data-col-idx="{col_seq}"'
                    col_seq += 1

                class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
                thead_parts.append(f'<th{r_span}{c_span}{class_str}{th_attrs}>{txt}</th>')
            thead_parts.append("</tr>")
    else:
        thead_parts.append("<tr>")
        for idx, c in enumerate(df.columns):
            th_classes = ["sortable-th"]
            if c == "종목명":
                th_classes.append("col-name-th")
            class_str = f' class="{" ".join(th_classes)}"'
            th_attrs = f' data-col-idx="{idx}"'
            thead_parts.append(f'<th{class_str}{th_attrs}>{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 행 조립 (각 행에 data-code 주입)
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        code_val = str(row.get("종목코드", "")).strip().zfill(6)
        tbody_parts.append(f'<tr data-code="{code_val}">')

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
        <table id="{table_id}" class="custom-grid-table">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

    # ⚡ 3. 브라우저 정렬 후 정렬된 종목 순서를 모든 탭 동기화 세션으로 전달하는 컴포넌트
    sorted_order = components.html(f"""
    <script>
    (function() {{
        const doc = window.parent.document;
        const table = doc.getElementById("{table_id}");
        if (!table) return;

        function parseFin(str) {{
            if (!str || str.trim() === '-' || str.trim() === '') return -999999999999;
            let clean = str.replace(/[,%원배\\s]/g, '');
            if (clean.includes('조')) {{
                let parts = clean.split('조');
                let jo = parseFloat(parts[0]) || 0;
                let rest = parseFloat(parts[1].replace(/억/g, '')) || 0;
                return (jo * 10000) + rest;
            }} else if (clean.includes('억')) {{
                clean = clean.replace(/억/g, '');
                return parseFloat(clean) || 0;
            }}
            let num = parseFloat(clean);
            return isNaN(num) ? str.trim() : num;
        }}

        const thList = table.querySelectorAll('th.sortable-th');
        thList.forEach(th => {{
            if (th.getAttribute('data-has-sync-listener') === 'true') return;
            th.setAttribute('data-has-sync-listener', 'true');

            th.addEventListener('click', function(e) {{
                e.preventDefault();
                const tbody = table.querySelector('tbody');
                const colIdx = parseInt(th.getAttribute('data-col-idx'), 10);
                const rows = Array.from(tbody.querySelectorAll('tr'));

                let isAsc = th.getAttribute('data-sort-asc') === 'true';
                let nextAsc = !isAsc;

                thList.forEach(otherTh => {{
                    otherTh.removeAttribute('data-sort-asc');
                    otherTh.innerHTML = otherTh.innerHTML.replace(/[ ▲▼]/g, '').trim();
                }});

                th.setAttribute('data-sort-asc', nextAsc);
                th.innerHTML = th.innerHTML.trim() + (nextAsc ? ' ▲' : ' ▼');

                rows.sort((a, b) => {{
                    let valA = a.children[colIdx] ? a.children[colIdx].innerText : '';
                    let valB = b.children[colIdx] ? b.children[colIdx].innerText : '';

                    let pA = parseFin(valA);
                    let pB = parseFin(valB);

                    if (typeof pA === 'number' && typeof pB === 'number') {{
                        return nextAsc ? (pA - pB) : (pB - pA);
                    }}
                    return nextAsc ? String(pA).localeCompare(String(pB)) : String(pB).localeCompare(String(pA));
                }});

                // DOM 재배치
                rows.forEach(r => tbody.appendChild(r));

                // ⚡ 정렬된 종목 순서 리스트 추출 및 Streamlit 이벤트 전송
                const orderedCodes = rows.map(r => r.getAttribute('data-code')).filter(Boolean);
                if (window.Streamlit) {{
                    window.Streamlit.setComponentValue(orderedCodes);
                }}
            }});
        }});
    }})();
    </script>
    """, height=0, width=0, key=f"comp_{table_id}")

    return sorted_order
