import html as _html

import streamlit as st
import streamlit.components.v1 as components


class Html(str):
    """이미 HTML로 만들어진 셀 값 (이스케이프하지 않음)."""


def apply_custom_styles():
    st.markdown("""
        <meta name="color-scheme" content="dark">
        <style>
        :root { color-scheme: dark !important; }
        html, body {
            color-scheme: dark !important;
            background-color: #0e1117 !important;
            overscroll-behavior-y: auto !important;
            touch-action: pan-x pan-y pinch-zoom !important;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
            background-color: #0e1117 !important;
            -webkit-overflow-scrolling: touch !important;
        }
        .block-container { padding-top: 1.8rem; padding-bottom: 3rem; max-width: 100% !important; }
        div[data-testid="stToggle"] { margin-bottom: 0.5rem !important; }
        div[data-testid="stToggle"] label p { font-size: 0.92rem !important; font-weight: 500 !important; color: #fafafa !important; }
        .filter-container-box {
            background-color: rgba(255,255,255,0.02) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 8px !important; padding: 12px 14px !important; margin-bottom: 1.2rem !important;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #262730 !important; border-color: #464855 !important; color: #ffffff !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #31333F !important; border-color: #5b5e71 !important;
        }

        /* ---- 범용 표 (render_table) ---- */
        .gw {
            overflow: auto; max-height: 70vh; border: 1px solid #334155; border-radius: 4px;
            background: #0e1117; margin-bottom: 1.2rem; position: relative;
            -webkit-overflow-scrolling: touch;
        }
        table.grid {
            border-collapse: separate !important; border-spacing: 0 !important;
            width: max-content; min-width: 100%; font-size: 0.82rem; color: #f3f4f6; background: #0e1117;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        table.grid th {
            position: sticky; top: 0; z-index: 10;
            background: #161a22; color: #9ca3af; font-weight: 500; font-size: 0.81rem;
            padding: 6px 10px; border-bottom: 2px solid #334155; border-right: 1px solid #262c36;
            text-align: center; white-space: normal; word-break: keep-all; line-height: 1.2; vertical-align: middle;
        }
        table.grid th.sub { top: 2.15rem; }
        table.grid td {
            background: #0e1117; padding: 8px 10px;
            border-bottom: 1px solid #1e242c; border-right: 1px solid #1e242c;
            white-space: nowrap; text-align: center; font-variant-numeric: tabular-nums;
        }
        table.grid.grouped tbody tr:last-child td { border-bottom: 2px solid #64748b; }
        table.grid .c-chk {
            position: sticky; left: 0; width: 40px; min-width: 40px; max-width: 40px;
            padding: 6px 0; text-align: center; z-index: 5; background: #0e1117;
        }
        table.grid th.c-chk { z-index: 101; background: #161a22; }
        table.grid .c-name {
            position: sticky; left: 0; width: 120px; min-width: 120px; max-width: 120px;
            text-align: left; padding-left: 12px; padding-right: 8px;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap; z-index: 5; background: #0e1117;
        }
        table.grid th.c-name { z-index: 100; background: #161a22; }
        table.grid.has-chk .c-name { left: 40px; }
        table.grid .div { border-right: 2.5px solid #ffffff !important; }
        table.grid tbody tr:hover td:not(.c-name):not(.c-chk) { background: rgba(255,255,255,0.03); }
        .up { color: #f87171 !important; font-weight: 500; }
        .down { color: #60a5fa !important; font-weight: 500; }
        .hl { color: #ff4b4b !important; font-weight: 700; }
        .naver-link { color: #58a6ff !important; text-decoration: none !important; }
        .naver-link:hover { text-decoration: underline !important; }
        .row-chk, .hdr-all { cursor: pointer; width: 16px; height: 16px; accent-color: #3b82f6; vertical-align: middle; }
        </style>
    """, unsafe_allow_html=True)


def _esc(v):
    if isinstance(v, Html):
        return str(v)
    if v is None:
        return "-"
    if isinstance(v, float) and v != v:
        return "-"
    s = str(v).strip()
    if s in ("", "nan", "None", "NaN"):
        return "-"
    return _html.escape(s)


def _cls(c):
    out = []
    if c.get("name"):
        out.append("c-name")
    if c.get("divider"):
        out.append("div")
    return " ".join(out)


def render_table(df, cols, tab_name, key_col="종목코드", *, has_checkbox=False, sel_param=None,
                 selected=(), merge_cols=(), cell_style=None,
                 empty_msg="표시할 데이터가 없습니다."):
    """
    cols: [{"key", "label", "group"?, "divider"?, "name"?, "link"?}, ...]
    group 이 하나라도 있으면 2단 헤더가 만들어진다 (group 없는 열은 rowspan=2).
    merge_cols: 같은 key(종목코드)끼리 세로 병합할 열. 체크박스도 함께 병합된다.
    sel_param: 체크 상태를 URL 쿼리파라미터에 저장할 이름 (예: sel_price).
    """
    if df is None or df.empty:
        st.info(empty_msg)
        return

    has_group = any(c.get("group") for c in cols)
    merge = set(merge_cols) if merge_cols else set()
    sel = set(selected)
    rs2 = ' rowspan="2"' if has_group else ""

    # ---- 헤더 ----
    top, sub = [], []
    if has_checkbox:
        top.append(f'<th{rs2} class="c-chk"><input type="checkbox" class="hdr-all" title="전체 선택"></th>')

    i = 0
    while i < len(cols):
        c = cols[i]
        if not c.get("group"):
            top.append(f'<th{rs2} class="{_cls(c)}">{c["label"]}</th>')
            i += 1
            continue
        g = c["group"]
        j = i
        while j < len(cols) and cols[j].get("group") == g:
            j += 1
        gdiv = " div" if cols[j - 1].get("divider") else ""
        top.append(f'<th colspan="{j - i}" class="grp{gdiv}">{g}</th>')
        for k in range(i, j):
            sub.append(f'<th class="sub {_cls(cols[k])}">{cols[k]["label"]}</th>')
        i = j

    thead = "<thead><tr>" + "".join(top) + "</tr>"
    if has_group:
        thead += "<tr>" + "".join(sub) + "</tr>"
    thead += "</thead>"

    # ---- 본문 ----
    recs = df.to_dict("records")
    if merge:
        groups = {}
        for r in recs:
            groups.setdefault(str(r.get(key_col, "")), []).append(r)
        blocks = list(groups.items())
    else:
        blocks = [(str(r.get(key_col, "")), [r]) for r in recs]

    body = []
    for key, rows in blocks:
        n = len(rows)
        body.append("<tbody>")
        for j, rec in enumerate(rows):
            body.append("<tr>")
            if has_checkbox and not (merge and j > 0):
                rs = f' rowspan="{n}"' if merge and n > 1 else ""
                ck = " checked" if key in sel else ""
                body.append(
                    f'<td{rs} class="c-chk"><input type="checkbox" class="row-chk" '
                    f'data-key="{_html.escape(key)}"{ck}></td>'
                )
            for c in cols:
                col = c["key"]
                if merge and col in merge and j > 0:
                    continue
                rs = f' rowspan="{n}"' if merge and col in merge and n > 1 else ""
                text = _esc(rec.get(col))
                if c.get("link") and key.isdigit() and len(key) == 6:
                    text = (f'<a class="naver-link" target="_blank" '
                            f'href="https://finance.naver.com/item/main.naver?code={key}">{text}</a>')
                extra = cell_style(rec, col) if cell_style else ""
                raw = str(rec.get(col, ""))
                if "%" in raw:
                    if raw.startswith("+"):
                        extra += " up"
                    elif raw.startswith("-"):
                        extra += " down"
                classes = " ".join(x for x in (_cls(c), extra.strip()) if x)
                cattr = f' class="{classes}"' if classes else ""
                body.append(f"<td{rs}{cattr}>{text}</td>")
            body.append("</tr>")
        body.append("</tbody>")

    table_cls = "grid" + (" has-chk" if has_checkbox else "") + (" grouped" if merge else "")
    sel_attr = f' data-sel="{sel_param}"' if sel_param else ""
    html_code = (f'<div class="gw"><table id="tbl_{tab_name}" class="{table_cls}"{sel_attr}>'
                 f'{thead}{"".join(body)}</table></div>')
    st.markdown(html_code, unsafe_allow_html=True)


def inject_client_sort_sync_engine():
    """당겨서 새로고침 + 체크박스 선택을 URL 쿼리파라미터(data-sel)에 동기화."""
    components.html("""
    <script>
    (function () {
        const doc = window.parent.document;
        const win = window.parent;
        if (!doc || !win) return;

        // 당겨서 새로고침 표시기
        let ptr = doc.getElementById('native_ptr_box');
        if (!ptr) {
            ptr = doc.createElement('div');
            ptr.id = 'native_ptr_box';
            ptr.style.cssText = 'position:fixed;top:-65px;left:50%;transform:translateX(-50%);width:42px;height:42px;background:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,.35);z-index:99999999;transition:top .15s ease,opacity .15s ease;opacity:0;pointer-events:none;';
            ptr.innerHTML = '<svg id="ptr_svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="#e2e8f0" stroke-width="2.5"/><path d="M12 3 A9 9 0 0 1 21 12" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round"/></svg>';
            doc.body.appendChild(ptr);
        }
        let startY = 0, startX = 0, canPull = false;
        function scrollTopNow() {
            const c1 = doc.querySelector('[data-testid="stAppViewContainer"]');
            const c2 = doc.querySelector('[data-testid="stMain"]');
            return Math.max(win.scrollY || 0, c1 ? c1.scrollTop : 0, c2 ? c2.scrollTop : 0);
        }
        win.ontouchstart = function (e) {
            canPull = e.touches.length === 1 && scrollTopNow() <= 1;
            if (canPull) { startY = e.touches[0].clientY; startX = e.touches[0].clientX; }
        };
        win.ontouchmove = function (e) {
            if (!canPull) return;
            const dy = e.touches[0].clientY - startY;
            const dx = Math.abs(e.touches[0].clientX - startX);
            if (dy <= 40 || dx > dy || scrollTopNow() > 1) {
                ptr.style.top = '-65px'; ptr.style.opacity = '0'; return;
            }
            const pull = Math.min((dy - 40) * 0.45, 80);
            ptr.style.top = (pull - 45) + 'px';
            ptr.style.opacity = Math.min((dy - 40) / 80, 1);
        };
        win.ontouchend = function (e) {
            if (!canPull) return;
            canPull = false;
            const dy = e.changedTouches[0].clientY - startY;
            if (dy >= 180 && scrollTopNow() <= 1) {
                ptr.style.top = '20px'; ptr.style.opacity = '1';
                setTimeout(function () { win.location.reload(); }, 120);
            } else {
                ptr.style.top = '-65px'; ptr.style.opacity = '0';
            }
        };

        // 체크박스 선택 -> URL 쿼리파라미터 (data-sel 로 지정된 이름)
        function syncSel(table) {
            if (!table) return;
            const param = table.getAttribute('data-sel');
            if (!param) return;
            const keys = Array.from(table.querySelectorAll('.row-chk:checked'))
                .map(c => c.getAttribute('data-key'));
            const url = new URL(win.location.href);
            if (keys.length) url.searchParams.set(param, keys.join(','));
            else url.searchParams.delete(param);
            win.history.replaceState(null, '', url.toString());
        }

        // 이전 실행의 리스너를 제거한 뒤 다시 등록 (rerun마다 iframe이 새로 만들어짐)
        const prev = win.__scanSync;
        if (prev) doc.removeEventListener('change', prev.onChange);
        const onChange = function (e) {
            const t = e.target;
            if (!t) return;
            if (t.classList.contains('hdr-all')) {
                const tbl = t.closest('table');
                if (tbl) tbl.querySelectorAll('.row-chk').forEach(c => { c.checked = t.checked; });
                syncSel(tbl);
            } else if (t.classList.contains('row-chk')) {
                syncSel(t.closest('table'));
            }
        };
        doc.addEventListener('change', onChange);
        win.__scanSync = { onChange: onChange };
    })();
    </script>
    """, height=0, width=0)
