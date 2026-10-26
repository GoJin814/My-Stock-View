import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def apply_custom_styles():
    st.markdown("""
        <meta name="color-scheme" content="dark">
        <meta name="supported-color-schemes" content="dark">

        <style>
        :root {
            color-scheme: dark !important;
        }

        html, body {
            color-scheme: dark !important;
            background-color: #0e1117 !important;
            overscroll-behavior-y: auto !important;
            touch-action: pan-x pan-y pinch-zoom !important;
            height: auto !important;
            min-height: 100% !important;
        }

        .stApp, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stMain"],
        section.main {
            background-color: #0e1117 !important;
            overscroll-behavior-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 100% !important;
        }

        div[data-testid="stToggle"] {
            margin-bottom: 0.5rem !important;
        }

        div[data-testid="stToggle"] label p {
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            color: #fafafa !important;
        }

        .filter-container-box {
            background-color: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            padding: 12px 14px !important;
            margin-bottom: 1.2rem !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
            font-size: 0.92rem !important;
        }

        .custom-grid-wrapper {
            overflow-x: auto !important;
            overflow-y: auto !important;
            max-height: 70vh !important;
            margin-bottom: 1.2rem;
            border-radius: 4px;
            border: 1px solid #334155;
            background-color: #0e1117;
            width: 100%;
            -webkit-overflow-scrolling: touch;
            position: relative;
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

        .custom-grid-table thead {
            position: sticky !important;
            top: 0 !important;
            z-index: 10 !important;
        }

        .custom-grid-table th {
            background-color: #161a22 !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            font-size: 0.81rem !important;
            padding: 6px 10px !important;
            border-bottom: 1px solid #334155 !important;
            border-right: 1px solid #262c36 !important;
            text-align: center !important;
            white-space: normal !important;
            word-break: keep-all !important;
            line-height: 1.2 !important;
            user-select: none !important;
            box-sizing: border-box !important;
            vertical-align: middle !important;
        }

        .custom-grid-table thead tr:first-child th {
            top: 0 !important;
            z-index: 10 !important;
        }

        .custom-grid-table thead tr:nth-child(2) th {
            top: 2.15rem !important;
            z-index: 10 !important;
        }

        .custom-grid-table th.col-chk-th,
        .custom-grid-table td.col-chk {
            position: sticky !important;
            left: 0 !important;
            width: 40px !important;
            min-width: 40px !important;
            max-width: 40px !important;
            text-align: center !important;
            background-color: #161a22 !important;
            border-right: 1px solid #262c36 !important;
            padding: 6px 0 !important;
        }
        .custom-grid-table th.col-chk-th {
            top: 0 !important;
            z-index: 100 !important;
        }
        .custom-grid-table td.col-chk {
            z-index: 5 !important;
            background-color: #0e1117 !important;
        }

        .custom-grid-table th.col-name-th {
            position: sticky !important;
            top: 0 !important;
            z-index: 100 !important;
            background-color: #161a22 !important;
            width: 120px !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: left !important;
            padding-left: 12px !important;
            border-right: none !important;
            vertical-align: middle !important;
        }

        .custom-grid-table td.col-name {
            position: sticky !important;
            z-index: 5 !important;
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
            border-right: none !important;
        }

        .table-has-chk th.col-name-th,
        .table-has-chk td.col-name {
            left: 40px !important;
        }
        .table-no-chk th.col-name-th,
        .table-no-chk td.col-name {
            left: 0 !important;
        }

        .custom-grid-table th.col-name-th::after,
        .custom-grid-table td.col-name::after {
            content: "" !important;
            position: absolute !important;
            top: 0 !important;
            right: 0 !important;
            width: 2.5px !important;
            height: 100% !important;
            background-color: #ffffff !important;
            pointer-events: none !important;
            z-index: 101 !important;
        }

        .custom-grid-table th.year-divider,
        .custom-grid-table td.year-divider {
            border-right: 2.5px solid #ffffff !important;
        }

        .custom-grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 7px 10px !important;
            border-bottom: 1px solid #1e242c !important;
            border-right: 1px solid #1e242c !important;
            white-space: nowrap !important;
            text-align: center !important;
            font-variant-numeric: tabular-nums !important;
            position: relative;
        }

        .custom-grid-table th.sortable-th {
            cursor: pointer !important;
            transition: background-color 0.15s ease, color 0.15s ease;
        }
        .custom-grid-table th.sortable-th:hover {
            background-color: #1f242e !important;
            color: #60a5fa !important;
        }

        .sort-indicator {
            display: inline-block;
            margin-left: 2px;
            font-size: 0.72rem;
            color: #60a5fa;
            vertical-align: middle;
        }

        .custom-grid-table tr:hover td {
            background-color: rgba(255, 255, 255, 0.03) !important;
        }
        .custom-grid-table tr:hover td.col-name,
        .custom-grid-table tr:hover td.col-chk {
            background-color: #161a22 !important;
        }

        .naver-pc-link {
            color: #58a6ff !important;
            text-decoration: none !important;
        }
        .naver-pc-link:hover {
            text-decoration: underline !important;
            color: #79b8ff !important;
        }

        .stock-checkbox,
        .header-select-all {
            cursor: pointer;
            width: 16px;
            height: 16px;
            accent-color: #3b82f6;
            vertical-align: middle;
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df, *args, **kwargs):
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        st.info("표시할 데이터가 없습니다.")
        return

    code_series = None
    if "종목코드" in df.columns:
        code_series = df["종목코드"].astype(str).str.strip().str.zfill(6)
        tab_name = kwargs.get("tab_name", "tab")
        if tab_name != "tab_basic":
            df = df.drop(columns=["종목코드"])

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

    table_chk_class = "table-has-chk" if has_checkbox else "table-no-chk"
    chk_header_html = '<input type="checkbox" class="header-select-all" title="전체 선택">'

    thead_parts = ["<thead>"]
    if header_rows:
        num_header_rows = len(header_rows)
        for r_idx, row in enumerate(header_rows):
            thead_parts.append("<tr>")
            cur_col_pos = 0
            multi_leaf_idx = 1 if not has_checkbox else 2

            for c_cell_idx, cell in enumerate(row):
                r_span_val = cell.get("rowspan", 1)
                c_span_val = cell.get("colspan", 1)
                r_span = f' rowspan="{r_span_val}"' if r_span_val > 1 else ""
                c_span = f' colspan="{c_span_val}"' if c_span_val > 1 else ""
                txt = cell.get("text", "")

                th_classes = []
                th_attrs = ""

                if txt == "선택":
                    th_classes.append("col-chk-th")
                    display_txt = chk_header_html
                elif txt == "종목명":
                    th_classes.append("col-name-th")
                    display_txt = txt
                else:
                    display_txt = txt

                is_leaf = (r_idx + r_span_val == num_header_rows)
                if txt != "선택" and is_leaf:
                    th_classes.append("sortable-th")
                    if num_header_rows == 1:
                        assigned_idx = c_cell_idx
                    elif txt == "종목명":
                        assigned_idx = 0 if not has_checkbox else 1
                    else:
                        assigned_idx = multi_leaf_idx
                        multi_leaf_idx += 1
                    th_attrs = f' data-col-idx="{assigned_idx}"'

                is_divider = False
                if r_idx == 0:
                    end_col = cur_col_pos + c_span_val - 1
                    if (end_col in div_set and end_col != len(df.columns) - 1) or cell.get("border_right", False):
                        is_divider = True
                    cur_col_pos += c_span_val
                else:
                    target_div_idx = multi_leaf_idx - 1
                    if target_div_idx in div_set or cell.get("border_right", False):
                        is_divider = True

                if is_divider:
                    th_classes.append("year-divider")

                class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
                thead_parts.append(f'<th{r_span}{c_span}{class_str}{th_attrs}>{display_txt}</th>')
            thead_parts.append("</tr>")
    else:
        thead_parts.append("<tr>")
        for idx, c in enumerate(df.columns):
            th_classes = []
            th_attrs = ""
            display_txt = c
            if c == "선택":
                th_classes.append("col-chk-th")
                display_txt = chk_header_html
            elif c == "종목명":
                th_classes.append("col-name-th")

            if c != "선택":
                th_classes.append("sortable-th")
                th_attrs = f' data-col-idx="{idx}"'
            if idx in div_set and idx != len(df.columns) - 1:
                th_classes.append("year-divider")

            class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
            thead_parts.append(f'<th{class_str}{th_attrs}>{display_txt}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    tbody_parts = ["<tbody>"]
    for row_i, (_, row) in enumerate(df.iterrows()):
        code_val = ""
        if code_series is not None and row_i < len(code_series):
            code_val = code_series.iloc[row_i]
        elif "종목코드" in row:
            code_val = str(row["종목코드"]).strip().zfill(6)

        if not code_val and "일시" in row:
            code_val = str(row["일시"]).replace("/", "-").strip()

        tbody_parts.append(f'<tr data-code="{code_val}">')

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val
            
            td_classes = []
            if col_idx in div_set and col_idx != len(df.columns) - 1:
                td_classes.append("year-divider")

            if col_name == "선택":
                td_classes.append("col-chk")
                class_str = f' class="{" ".join(td_classes)}"'
                tbody_parts.append(f'<td{class_str}><input type="checkbox" class="stock-checkbox" data-code="{code_val}"></td>')
                continue

            if col_name == "종목명":
                td_classes.append("col-name")
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" class="naver-pc-link">{val}</a>'
                else:
                    content = val

                class_str = f' class="{" ".join(td_classes)}"'
                tbody_parts.append(f'<td{class_str}>{content}</td>')
                continue

            color_css = ""
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa !important; font-weight: 500;"

            style_attr = f' style="{color_css}"' if color_css else ""
            class_str = f' class="{" ".join(td_classes)}"' if td_classes else ""

            tbody_parts.append(f'<td{class_str}{style_attr}>{val}</td>')

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    html_code = f"""
    <div class="custom-grid-wrapper">
        <table id="{table_id}" class="custom-grid-table {table_chk_class}">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

def inject_client_sort_sync_engine():
    components.html("""
    <script>
    (function initEngine() {
        const doc = window.parent.document;
        const win = window.parent;
        if (!doc || !win) return;

        // ⚡ 체크박스 상태를 브라우저 URL 파라미터에 실시간 강제 동기화하는 함수
        function updateDelParam() {
            const checkedCodes = [];
            doc.querySelectorAll('#table_tab_basic .stock-checkbox:checked').forEach(cb => {
                const c = cb.getAttribute('data-code');
                if (c && c.length === 6) checkedCodes.push(c);
            });
            try {
                const url = new URL(win.location.href);
                if (checkedCodes.length > 0) {
                    url.searchParams.set('del_codes', checkedCodes.join(','));
                } else {
                    url.searchParams.delete('del_codes');
                }
                win.history.replaceState(null, '', url.toString());
            } catch(e) {}
        }

        // 전체 선택 및 개별 체크박스 변경 시 즉시 URL 갱신
        doc.addEventListener('change', function(e) {
            if (e.target && e.target.classList.contains('header-select-all')) {
                const isChecked = e.target.checked;
                const tbl = e.target.closest('table');
                if (tbl) {
                    tbl.querySelectorAll('.stock-checkbox').forEach(cb => {
                        cb.checked = isChecked;
                    });
                }
                updateDelParam();
            } else if (e.target && e.target.classList.contains('stock-checkbox')) {
                updateDelParam();
            }
        });

        // 🗑️ 삭제 버튼 클릭 순간에도 최신 체크 상태 다시 한번 확정
        doc.addEventListener('click', function(e) {
            const btn = e.target.closest('button');
            if (btn && btn.innerText.includes('선택 종목 삭제')) {
                updateDelParam();
            }
        }, true);

        function parseFin(str) {
            if (!str || str.trim() === '-' || str.trim() === '') return -999999999999;
            let clean = str.replace(/[,%원배\\s]/g, '').trim();

            if (/^\\d{4}[\\/\\-]\\d{1,2}[\\/\\-]\\d{1,2}$/.test(clean)) {
                let parts = clean.split(/[\\/\\-]/);
                let y = parts[0];
                let m = parts[1].padStart(2, '0');
                let d = parts[2].padStart(2, '0');
                return parseInt(y + m + d, 10);
            }

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

        function getActiveCodeOrder() {
            const urlParams = new URLSearchParams(win.location.search);
            const urlCodes = urlParams.get('sort_codes');
            if (urlCodes) return urlCodes.split(',');
            const saved = win.sessionStorage.getItem('stock_sync_order');
            return saved ? JSON.parse(saved) : null;
        }

        function applySavedOrderToAll() {
            const codeOrder = getActiveCodeOrder();
            if (!codeOrder) return;
            doc.querySelectorAll('table.custom-grid-table:not(#table_tab_market)').forEach(tbl => {
                sortTableByCodeList(tbl, codeOrder);
            });
        }

        // ⚡ 어느 탭(현재 시세, 주당 가치, 실적)에서 헤더를 클릭하든 모든 탭 동기화
        doc.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('header-select-all')) return;

            const th = e.target.closest('th.sortable-th');
            if (!th) return;

            const table = th.closest('table.custom-grid-table');
            if (!table) return;

            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            const colIdx = parseInt(th.getAttribute('data-col-idx'), 10);
            if (isNaN(colIdx)) return;

            const rows = Array.from(tbody.querySelectorAll('tr'));
            let isAsc = th.getAttribute('data-sort-asc') === 'true';
            let nextAsc = !isAsc;

            table.querySelectorAll('th.sortable-th').forEach(otherTh => {
                otherTh.removeAttribute('data-sort-asc');
                const ind = otherTh.querySelector('.sort-indicator');
                if (ind) ind.remove();
            });

            th.setAttribute('data-sort-asc', nextAsc);
            const indicator = doc.createElement('span');
            indicator.className = 'sort-indicator';
            indicator.textContent = nextAsc ? ' ▲' : ' ▼';
            th.appendChild(indicator);

            rows.sort((a, b) => {
                let cellA = a.children[colIdx];
                let cellB = b.children[colIdx];
                let valA = cellA ? cellA.innerText.trim() : '';
                let valB = cellB ? cellB.innerText.trim() : '';

                let pA = parseFin(valA);
                let pB = parseFin(valB);

                if (typeof pA === 'number' && typeof pB === 'number') {
                    return nextAsc ? (pA - pB) : (pB - pA);
                }
                return nextAsc ? String(pA).localeCompare(String(pB)) : String(pB).localeCompare(String(pA));
            });

            rows.forEach(r => tbody.appendChild(r));

            if (table.id !== 'table_tab_market') {
                const sortedCodes = rows.map(r => r.getAttribute('data-code')).filter(Boolean);
                win.sessionStorage.setItem('stock_sync_order', JSON.stringify(sortedCodes));

                try {
                    const url = new URL(win.location.href);
                    url.searchParams.set('sort_codes', sortedCodes.join(','));
                    win.history.replaceState(null, '', url.toString());
                } catch (err) {}

                // 다른 모든 탭 테이블 순서 즉시 동기화
                doc.querySelectorAll('table.custom-grid-table:not(#table_tab_market)').forEach(otherTable => {
                    if (otherTable !== table) {
                        sortTableByCodeList(otherTable, sortedCodes);
                    }
                });
            }
        });

        // 탭 전환 감지 시 정렬 순서 즉시 복원
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
