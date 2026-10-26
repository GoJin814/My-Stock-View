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

        /* 1. 기본 레이아웃 및 브라우저 스크롤 개방 */
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

        /* 2. 필터 토글 스위치 및 컨테이너 */
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

        /* 4. 그리드 컨테이너 및 테이블 */
        .custom-grid-wrapper {
            overflow-x: auto !important;
            margin-bottom: 1.2rem;
            border-radius: 4px;
            border: 1px solid #334155;
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
            background-color: #161a22 !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            font-size: 0.81rem !important;
            padding: 8px 10px !important;
            border-bottom: 1px solid #334155 !important;
            border-right: 1px solid #262c36 !important;
            text-align: center !important;
            white-space: nowrap !important;
            user-select: none !important;
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

        /* 종목명 열 좌측 고정 (Sticky) */
        .custom-grid-table th.col-name-th {
            position: sticky !important;
            left: 0 !important;
            z-index: 5 !important;
            background-color: #161a22 !important;
            width: 120px !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: left !important;
            padding-left: 12px !important;
            border-right: none !important;
        }

        .custom-grid-table td.col-name {
            position: sticky !important;
            left: 0 !important;
            z-index: 4 !important;
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

        /* 종목명 오른쪽 붙박이 고정선 (3px 화이트) */
        .custom-grid-table th.col-name-th::after,
        .custom-grid-table td.col-name::after {
            content: "" !important;
            position: absolute !important;
            top: 0 !important;
            right: 0 !important;
            width: 3px !important;
            height: 100% !important;
            background-color: #ffffff !important;
            pointer-events: none !important;
            z-index: 6 !important;
        }

        /* ⚡ 핵심: 연도별 구분을 위한 3px 슈퍼 화이트 구분선 클래스 */
        .custom-grid-table th.year-divider,
        .custom-grid-table td.year-divider {
            border-right: 3px solid #ffffff !important;
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

    # 종목코드는 행 식별(data-code)용으로 보관하고 화면 출력에서는 분리
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

    # 1. 헤더 HTML 조립
    thead_parts = ["<thead>"]
    if header_rows:
        num_header_rows = len(header_rows)
        for r_idx, row in enumerate(header_rows):
            thead_parts.append("<tr>")
            col_seq = 0 if r_idx == 0 else (1 if not has_checkbox else 2)
            cur_col_pos = 0

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

                is_leaf = (r_idx + r_span_val == num_header_rows)
                if txt != "선택" and is_leaf:
                    th_classes.append("sortable-th")
                    th_attrs = f' data-col-idx="{col_seq}"'
                    col_seq += 1
                elif txt == "선택":
                    col_seq += 1

                # ⚡ 이 헤더 셀이 끝나는 열 위치가 구분선 컬럼에 포함되는지 검사
                end_col_idx = cur_col_pos + c_span_val - 1
                if end_col_idx in div_set or cell.get("border_right", False):
                    th_classes.append("year-divider")

                cur_col_pos += c_span_val

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
            if idx in div_set:
                th_classes.append("year-divider")

            class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
            thead_parts.append(f'<th{class_str}{th_attrs}>{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 데이터 행 HTML 조립
    tbody_parts = ["<tbody>"]
    for row_i, (_, row) in enumerate(df.iterrows()):
        code_val = ""
        if code_series is not None and row_i < len(code_series):
            code_val = code_series.iloc[row_i]
        elif "종목코드" in row:
            code_val = str(row["종목코드"]).strip().zfill(6)

        tbody_parts.append(f'<tr data-code="{code_val}">')

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val
            
            td_classes = []
            if col_idx in div_set:
                td_classes.append("year-divider")

            if col_name == "선택":
                class_str = f' class="{" ".join(td_classes)}"' if td_classes else ""
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
        <table id="{table_id}" class="custom-grid-table">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

def inject_client_sort_sync_engine():
    """웨일 스와이프 새로고침 + 무새로고침 정렬/동기화 엔진"""
    components.html("""
    <script>
    (function initEngine() {
        const doc = window.parent.document;
        const win = window.parent;
        if (!doc || !win) return;

        let ptrBox = doc.getElementById('native_ptr_box');
        if (!ptrBox) {
            ptrBox = doc.createElement('div');
            ptrBox.id = 'native_ptr_box';
            ptrBox.style.cssText = `
                position: fixed;
                top: -65px;
                left: 50%;
                transform: translateX(-50%);
                width: 42px;
                height: 42px;
                background: #ffffff;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.35);
                z-index: 99999999;
                transition: top 0.15s ease, opacity 0.15s ease;
                opacity: 0;
                pointer-events: none;
            `;
            ptrBox.innerHTML = `
                <svg id="ptr_svg" width="24" height="24" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="9" fill="none" stroke="#e2e8f0" stroke-width="2.5"/>
                    <path d="M12 3 A9 9 0 0 1 21 12" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
            `;
            doc.body.appendChild(ptrBox);
        }

        let touchStartY = 0;
        let touchStartX = 0;
        let canPull = false;

        function getRealScrollTop() {
            const docEl = doc.documentElement ? doc.documentElement.scrollTop : 0;
            const bodyEl = doc.body ? doc.body.scrollTop : 0;
            const winY = win.scrollY || win.pageYOffset || 0;
            
            const c1 = doc.querySelector('[data-testid="stAppViewContainer"]');
            const c2 = doc.querySelector('[data-testid="stMain"]');
            const c3 = doc.querySelector('section.main');
            const c4 = doc.querySelector('.main');

            const s1 = c1 ? c1.scrollTop : 0;
            const s2 = c2 ? c2.scrollTop : 0;
            const s3 = c3 ? c3.scrollTop : 0;
            const s4 = c4 ? c4.scrollTop : 0;

            return Math.max(winY, docEl, bodyEl, s1, s2, s3, s4);
        }

        win.ontouchstart = function(e) {
            if (e.touches.length === 1) {
                if (getRealScrollTop() <= 1) {
                    touchStartY = e.touches[0].clientY;
                    touchStartX = e.touches[0].clientX;
                    canPull = true;
                } else {
                    canPull = false;
                }
            } else {
                canPull = false;
            }
        };

        win.ontouchmove = function(e) {
            if (!canPull) return;

            if (getRealScrollTop() > 1) {
                canPull = false;
                ptrBox.style.top = '-65px';
                ptrBox.style.opacity = '0';
                return;
            }

            const currentY = e.touches[0].clientY;
            const currentX = e.touches[0].clientX;
            const distY = currentY - touchStartY;
            const distX = Math.abs(currentX - touchStartX);

            if (distY <= 0 || distX > distY) {
                ptrBox.style.top = '-65px';
                ptrBox.style.opacity = '0';
                return;
            }

            if (distY > 15) {
                const pullY = Math.min((distY - 15) * 0.45, 80);
                ptrBox.style.top = (pullY - 45) + 'px';
                ptrBox.style.opacity = Math.min((distY - 15) / 50, 1);
                const svg = ptrBox.querySelector('#ptr_svg');
                if (svg) svg.style.transform = 'rotate(' + (distY * 3.5) + 'deg)';
            }
        };

        win.ontouchend = function(e) {
            if (!canPull) return;
            canPull = false;
            const distY = e.changedTouches[0].clientY - touchStartY;

            if (distY >= 100 && getRealScrollTop() <= 1) {
                ptrBox.style.top = '20px';
                ptrBox.style.opacity = '1';
                const svg = ptrBox.querySelector('#ptr_svg');
                if (svg) {
                    svg.animate([
                        { transform: 'rotate(0deg)' },
                        { transform: 'rotate(360deg)' }
                    ], { duration: 600, iterations: Infinity });
                }
                setTimeout(function() {
                    win.location.reload();
                }, 120);
            } else {
                ptrBox.style.top = '-65px';
                ptrBox.style.opacity = '0';
            }
        };

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
            const saved = win.sessionStorage.getItem('stock_sync_order');
            if (!saved) return;
            try {
                const codeOrder = JSON.parse(saved);
                doc.querySelectorAll('table.custom-grid-table').forEach(tbl => {
                    sortTableByCodeList(tbl, codeOrder);
                });
            } catch (e) {}
        }

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

            const sortedCodes = rows.map(r => r.getAttribute('data-code')).filter(Boolean);
            win.sessionStorage.setItem('stock_sync_order', JSON.stringify(sortedCodes));

            doc.querySelectorAll('table.custom-grid-table').forEach(otherTable => {
                if (otherTable !== table) {
                    sortTableByCodeList(otherTable, sortedCodes);
                }
            });
        });

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
