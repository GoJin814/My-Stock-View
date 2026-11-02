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
            padding-top: 3.2rem !important; /* 헤더 툴바 직하단에 밀착 */
            padding-bottom: 2.0rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
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

        /* 필터 컨테이너 초슬림 패딩 */
        .filter-container-box {
            background-color: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 6px !important;
            padding: 6px 10px !important;
            margin-bottom: 0.4rem !important;
        }

        /* 슬라이더 라벨 높이 제거 및 마진 축소 */
        .filter-container-box div[data-testid="stSlider"] {
            margin-top: -6px !important;
            margin-bottom: 0 !important;
        }

        .filter-container-box div[data-testid="stCheckbox"] {
            margin-top: 4px !important;
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
            border-bottom: 2px solid #334155 !important;
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
            padding: 8px 10px !important;
            border-bottom: 1px solid #1e242c !important; /* 기본 행은 얇은 선 */
            border-right: 1px solid #1e242c !important;
            white-space: nowrap !important;
            text-align: center !important;
            font-variant-numeric: tabular-nums !important;
            position: relative;
        }

        /* 💡 종목별로 묶이는 2줄마다(짝수 번째 행) 굵은 구분선 적용 */
        #table_tab_watchlist tr:nth-child(even) td {
            border-bottom: 2px solid #64748b !important;
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
        /* ========================================================= */
        /* ★ 탭 메뉴 무조건 1줄 강제 고정 & 부드러운 가로 스크롤 */
        /* ========================================================= */

        /* 1. 라디오 컨테이너가 화면 너비를 넘지 못하게 잠금 */
        div[data-testid="stRadio"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
            margin-bottom: 0.3rem !important;
        }

        /* 2. radiogroup 및 하위 div의 줄바꿈을 원천 차단하고 1줄 가로스크롤 강제 */
        div[data-testid="stRadio"] > div,
        div[data-testid="stRadio"] [role="radiogroup"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important; /* ★ 2줄 줄바꿈 금지 */
            overflow-x: auto !important; /* ★ 가로 스크롤 활성화 */
            overflow-y: hidden !important;
            -webkit-overflow-scrolling: touch !important; /* 모바일 부드러운 터치 스크롤 */
            scrollbar-width: none !important; /* 파이어폭스 스크롤바 숨김 */
            gap: 1.2rem !important;
            padding-bottom: 4px !important;
            margin: 0 !important;
            width: 100% !important;
            white-space: nowrap !important;
        }

        /* 3. 스크롤바 감추기 (크롬 / 사파리 / 삼성인터넷) */
        div[data-testid="stRadio"] > div::-webkit-scrollbar,
        div[data-testid="stRadio"] [role="radiogroup"]::-webkit-scrollbar {
            display: none !important;
        }

        /* 4. 개별 탭 버튼이 찌그러지거나 아래로 떨어지지 않도록 설정 */
        div[data-testid="stRadio"] [role="radiogroup"] label {
            display: inline-flex !important;
            align-items: center !important;
            flex-shrink: 0 !important; /* ★ 화면이 좁아도 찌그러짐 방지 */
            background: transparent !important;
            border: none !important;
            padding: 0.3rem 0.1rem !important;
            margin: 0 !important;
            cursor: pointer !important;
            white-space: nowrap !important;
        }

        /* 5. 텍스트 글자 크기 및 색상 */
        div[data-testid="stRadio"] [role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
            color: #94a3b8 !important;
            font-size: 0.95rem !important;
            font-weight: 500 !important;
            margin: 0 !important;
            white-space: nowrap !important;
        }

        /* 6. 선택된 탭 강조 (빨간 밑줄) */
        div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
            border-bottom: 2px solid #ff4b4b !important;
        }
        div[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
                /* 뷰포트 가로 스크롤 이탈 절대 방지 */
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
            overflow-x: hidden !important;
            max-width: 100vw !important;
            position: relative !important;
        }

        /* 탭 라디오 바 자체만 가로 스크롤 허용 */
        div[data-testid="stRadio"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
        }

        div[data-testid="stRadio"] > div,
        div[data-testid="stRadio"] [role="radiogroup"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            -webkit-overflow-scrolling: touch !important;
            scrollbar-width: none !important;
            gap: 1.2rem !important;
            padding-bottom: 4px !important;
            width: 100% !important;
        }
        div[data-testid="stRadio"] > div::-webkit-scrollbar,
        div[data-testid="stRadio"] [role="radiogroup"]::-webkit-scrollbar {
            display: none !important;
        }

        div[data-testid="stRadio"] [role="radiogroup"] label {
            display: inline-flex !important;
            align-items: center !important;
            flex-shrink: 0 !important;
            background: transparent !important;
            white-space: nowrap !important;
        }
        
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df, tab_name="tab_default", has_naver_link=True, has_checkbox=False):
    if df is None or df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    # 1. 헤더 HTML 구성
    headers = [col for col in df.columns if not col.startswith("_")]
    th_html = ""
    start_idx = 0

    if has_checkbox:
        th_html += '<th style="width: 40px; text-align: center;"><input type="checkbox" class="header-select-all"></th>'
        start_idx = 1

    for i, col in enumerate(headers):
        col_idx = start_idx + i
        align = "left" if col in ["종목명", "종목코드"] else "right"
        th_html += f'<th class="sortable-th" data-col-idx="{col_idx}" style="text-align: {align};">{col}</th>'

    # 2. 파이썬 DF의 정렬 순서 그대로 HTML 행(tr) 생성
    rows_html = ""
    for _, row in df.iterrows():
        code = str(row.get("종목코드", "")).strip().zfill(6)
        rows_html += f'<tr data-code="{code}">'
        
        if has_checkbox:
            rows_html += f'<td style="text-align: center;"><input type="checkbox" class="stock-checkbox" data-code="{code}"></td>'

        for col in headers:
            val = row.get(col, "-")
            val_str = "-" if pd.isna(val) else str(val)
            align = "left" if col in ["종목명", "종목코드"] else "right"

            if col == "종목명" and has_naver_link and code:
                cell_content = f'<a href="https://m.stock.naver.com/item/main/{code}" target="_blank" style="color: inherit; text-decoration: none; font-weight: 600;">{val_str}</a>'
            elif col == "종목코드":
                cell_content = f'<span style="color: #94a3b8; font-family: monospace;">{val_str}</span>'
            else:
                cell_content = val_str

            rows_html += f'<td style="text-align: {align};">{cell_content}</td>'
        
        rows_html += '</tr>'

    table_id = f"table_{tab_name}"
    
    # 3. 테이블 렌더링 (sessionStorage 강제 재정렬 스크립트 제거)
    html_code = f"""
    <div class="custom-table-container">
        <table class="custom-grid-table" id="{table_id}">
            <thead>
                <tr>{th_html}</tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
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

        // 1. 화면이 우측으로 밀리는 포커스 강제 스크롤 차단 엔진
        function lockHorizontalScroll() {
            if (win.scrollX !== 0) win.scrollTo(0, win.scrollY);
            const containers = [
                doc.documentElement,
                doc.body,
                doc.querySelector('.stApp'),
                doc.querySelector('[data-testid="stAppViewContainer"]'),
                doc.querySelector('[data-testid="stMain"]'),
                doc.querySelector('section.main')
            ];
            containers.forEach(el => {
                if (el && el.scrollLeft !== 0) el.scrollLeft = 0;
            });
        }

        win.addEventListener('scroll', lockHorizontalScroll, { passive: true });
        doc.addEventListener('scroll', lockHorizontalScroll, { passive: true });

        // 탭 터치 시 전역 뷰포트 이동 즉시 차단
        doc.addEventListener('click', function(e) {
            const isTab = e.target.closest('div[data-testid="stRadio"]');
            if (isTab) {
                setTimeout(lockHorizontalScroll, 10);
                setTimeout(lockHorizontalScroll, 50);
                setTimeout(lockHorizontalScroll, 150);
            }
        }, true);

        // 2. Firebase 실시간 REST 정렬 동기화
        const FIREBASE_URL = "https://my-stock-view-default-rtdb.firebaseio.com/my_stock_view/sort_order.json";

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

            // 모든 탭의 표에 즉시 반영
            if (table.id !== 'table_tab_market') {
                const sortedCodes = rows.map(r => r.getAttribute('data-code')).filter(Boolean);
                
                doc.querySelectorAll('table.custom-grid-table:not(#table_tab_market)').forEach(otherTable => {
                    if (otherTable !== table) {
                        sortTableByCodeList(otherTable, sortedCodes);
                    }
                });

                // ★ Firebase DB에 즉시 HTTP PUT으로 저장 (다른 기기 즉시 연동)
                try {
                    fetch(FIREBASE_URL, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(sortedCodes)
                    }).catch(err => console.log('Firebase sync error:', err));
                } catch(e) {}
            }
        });

        // 체크박스 삭제 파라미터 관리
        function updateDelParam() {
            const checkedCodes = [];
            doc.querySelectorAll('.stock-checkbox:checked').forEach(cb => {
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

        function parseFin(str) {
            if (!str || str.trim() === '-' || str.trim() === '') return -999999999999;
            let clean = str.replace(/[,%원배\s]/g, '').trim();

            if (/^\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}$/.test(clean)) {
                let parts = clean.split(/[\/\-]/);
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

        // 초기 로드 시 Firebase 정렬 순서 가져와 즉시 적용
        fetch(FIREBASE_URL)
            .then(res => res.json())
            .then(order => {
                if (Array.isArray(order) && order.length > 0) {
                    doc.querySelectorAll('table.custom-grid-table:not(#table_tab_market)').forEach(tbl => {
                        sortTableByCodeList(tbl, order);
                    });
                }
            })
            .catch(() => {});
    })();
    </script>
    """, height=0, width=0)
