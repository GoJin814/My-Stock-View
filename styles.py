import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

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

        /* 체크박스 스타일 */
        .stock-checkbox {
            cursor: pointer;
            width: 15px;
            height: 15px;
            accent-color: #3b82f6;
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
    tab_name = kwargs.get("tab_name", "tab")
    table_id = f"table_{tab_name}"
    has_checkbox = kwargs.get("has_checkbox", False)

    # 1. 헤더 조립
    thead_parts = ["<thead>"]
    if header_rows:
        for r_idx, row in enumerate(header_rows):
            thead_parts.append("<tr>")
            # 2층 헤더가 있는 경우 col_seq 보정
            col_seq = 0 if r_idx == 0 else (3 if has_checkbox else 2)
            for cell in row:
                r_span_val = cell.get("rowspan", 1)
                c_span_val = cell.get("colspan", 1)
                r_span = f' rowspan="{r_span_val}"' if r_span_val > 1 else ""
                c_span = f' colspan="{c_span_val}"' if c_span_val > 1 else ""
                txt = cell.get("text", "")

                th_classes = []
                th_attrs = ""

                if txt == "종목명":
                    th_classes.append("col-name-th")

                # 선택 열을 제외한 모든 항목 정렬 허용
                if txt != "선택" and (r_span_val > 1 or c_span_val == 1):
                    th_classes.append("sortable-th")
                    th_attrs = f' data-col-idx="{col_seq}"'
                    col_seq += 1
                elif txt == "선택":
                    col_seq += 1

                class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
                thead_parts.append(f'<th{r_span}{c_span}{class_str}{th_attrs}>{txt}</th>')
            thead_parts.append("</tr>")
    else:
        thead_parts.append("<tr>")
        for idx, c in enumerate(df.columns):
            th_classes = []
            th_attrs = ""
            if c == "종목명":
                th_classes.append("col-name-th")
            if c != "선택":
                th_classes.append("sortable-th")
                th_attrs = f' data-col-idx="{idx}"'
            class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
            thead_parts.append(f'<th{class_str}{th_attrs}>{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 조립
    tbody_parts = ["<tbody>"]
    for _, row in df.iterrows():
        code_val = str(row.get("종목코드", "")).strip().zfill(6)
        tbody_parts.append(f'<tr data-code="{code_val}">')

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val
            border_r = "border-right: 2px solid rgba(255, 255, 255, 0.22) !important;" if col_idx in div_set else ""

            # 체크박스 열
            if col_name == "선택":
                tbody_parts.append(f'<td style="{border_r}"><input type="checkbox" class="stock-checkbox" data-code="{code_val}"></td>')
                continue

            # 종목명 열: 120px 고정 + 링크
            if col_name == "종목명":
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" class="naver-pc-link">{val}</a>'
                else:
                    content = val

                style_attr = f'style="{border_r}"' if border_r else ""
                tbody_parts.append(f'<td class="col-name" {style_attr}>{content}</td>')
                continue

            # 수치 컬러링
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

def inject_client_sort_sync_engine():
    """모든 탭(현재 시세, 주당 가치, 실적) 간 무새로고침 순서 동기화 엔진"""
    components.html("""
    <script>
    (function initEngine() {
        const doc = window.parent.document;
        if (!doc) return;

        function parseFin(str) {
            if (!str || str.trim() === '-' || str.trim() === '') return -999999999999;
            let clean = str.replace(/[,%원배\\s]/g, '');
            if (clean.includes('조')) {
                let parts = clean.split('조');
                let jo = parseFloat(parts[0]) || 0;
                let rest = parseFloat(parts[1].replace(/억/g, '')) || 0;
                return (jo * 10000) + rest;
            } else if (clean.includes('억')) {
                clean = clean.replace(/억/g, '');
                return parseFloat(clean) || 0;
            }
            let num = parseFloat(clean);
            return isNaN(num) ? str.trim() : num;
        }

        function sortTableByCodeList(table, codeOrder) {
            if (!table || !codeOrder || codeOrder.length === 0) return;
            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            const rows = Array.from(tbody.querySelectorAll('tr'));
            rows.sort((a, b) => {
                let cA = a.getAttribute('data-code');
                let cB = b.getAttribute('data-code');
                let iA = codeOrder.indexOf(cA);
                let iB = codeOrder.indexOf(cB);
                if (iA === -1) iA = 9999;
                if (iB === -1) iB = 9999;
                return iA - iB;
            });
            rows.forEach(r => tbody.appendChild(r));
        }

        function applySavedOrderToAll() {
            const saved = window.parent.sessionStorage.getItem('stock_sync_order');
            if (!saved) return;
            try {
                const codeOrder = JSON.parse(saved);
                doc.querySelectorAll('table.custom-grid-table').forEach(tbl => {
                    sortTableByCodeList(tbl, codeOrder);
                });
            } catch (e) {}
        }

        // 1. 헤더 클릭 정렬 이벤트
        doc.addEventListener('click', function(e) {
            const th = e.target.closest('th.sortable-th');
            if (!th) return;

            const table = th.closest('table.custom-grid-table');
            if (!table) return;

            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            const colIdx = parseInt(th.getAttribute('data-col-idx'), 10);
            const rows = Array.from(tbody.querySelectorAll('tr'));

            let isAsc = th.getAttribute('data-sort-asc') === 'true';
            let nextAsc = !isAsc;

            table.querySelectorAll('th.sortable-th').forEach(otherTh => {
                otherTh.removeAttribute('data-sort-asc');
                otherTh.textContent = otherTh.textContent.replace(/[ ▲▼]/g, '').trim();
            });

            th.setAttribute('data-sort-asc', nextAsc);
            th.textContent = th.textContent.trim() + (nextAsc ? ' ▲' : ' ▼');

            rows.sort((a, b) => {
                let valA = a.children[colIdx] ? a.children[colIdx].innerText : '';
                let valB = b.children[colIdx] ? b.children[colIdx].innerText : '';

                let pA = parseFin(valA);
                let pB = parseFin(valB);

                if (typeof pA === 'number' && typeof pB === 'number') {
                    return nextAsc ? (pA - pB) : (pB - pA);
                }
                return nextAsc ? String(pA).localeCompare(String(pB)) : String(pB).localeCompare(String(pA));
            });

            rows.forEach(r => tbody.appendChild(r));

            // 정렬된 종목 순서를 세션에 저장하고 다른 탭 테이블들에도 즉시 동기화
            const sortedCodes = rows.map(r => r.getAttribute('data-code')).filter(Boolean);
            window.parent.sessionStorage.setItem('stock_sync_order', JSON.stringify(sortedCodes));

            doc.querySelectorAll('table.custom-grid-table').forEach(otherTable => {
                if (otherTable !== table) {
                    sortTableByCodeList(otherTable, sortedCodes);
                }
            });
        });

        // 2. 탭 전환 시 보관된 순서 동기화
        doc.addEventListener('click', function(e) {
            const tabBtn = e.target.closest('.stTabs [data-baseweb="tab"]');
            if (tabBtn) {
                setTimeout(applySavedOrderToAll, 40);
            }
        });

        setTimeout(applySavedOrderToAll, 80);
    })();
    </script>
    """, height=0, width=0)
