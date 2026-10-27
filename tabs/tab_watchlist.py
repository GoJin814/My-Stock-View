import streamlit as st
import pandas as pd
import json
import os
import base64
import requests
import streamlit.components.v1 as components

WATCHLIST_CACHE_FILE = "watchlist_data.json"

def load_watchlist_data():
    if "persistent_watchlist" in st.session_state and st.session_state.persistent_watchlist:
        return st.session_state.persistent_watchlist

    data = {}
    if os.path.exists(WATCHLIST_CACHE_FILE):
        try:
            with open(WATCHLIST_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if not data:
        github_data = load_from_github(WATCHLIST_CACHE_FILE)
        if github_data:
            data = github_data
            with open(WATCHLIST_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    st.session_state.persistent_watchlist = data
    return data

def load_from_github(filename):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    if not token or not repo:
        return {}
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        res = requests.get(url, headers=headers, params={"ref": branch}, timeout=7)
        if res.status_code == 200:
            content_b64 = res.json().get("content", "")
            content_bytes = base64.b64decode(content_b64)
            return json.loads(content_bytes.decode("utf-8"))
    except Exception:
        pass
    return {}

def commit_to_github(filename, content_str, commit_message="Auto-update watchlist data"):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    if not token or not repo:
        return False
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        res = requests.get(url, headers=headers, params={"ref": branch}, timeout=7)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        payload = {"message": commit_message, "content": content_b64, "branch": branch}
        if sha: payload["sha"] = sha
        put_res = requests.put(url, headers=headers, json=payload, timeout=7)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

def save_watchlist_data(data):
    st.session_state.persistent_watchlist = data
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(WATCHLIST_CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(json_text)
    commit_to_github(WATCHLIST_CACHE_FILE, json_text, "Auto-commit watchlist_data.json")

def render_tab_watchlist(full_csv_records_map=None):
    st.markdown("#### ⭐ 관심종목 실적 관리")
    st.caption("'현재 시세' 탭에서 추가한 관심종목의 직전/최근연도 실적 데이터를 병합된 셀 구조로 관리합니다. 종목명을 클릭하면 네이버 증권 페이지로 이동합니다.")

    watchlist = load_watchlist_data()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택하고 [관심종목 추가] 버튼을 눌러주세요.")
        return

    st.write("")

    query_params = st.query_params
    action = query_params.get("action", "")

    # 삭제 버튼이 눌렸을 때 쿼리 파라미터를 통해 일괄 삭제 수행
    if action == "delete_selected":
        # Streamlit 폼 제출 데이터를 통해 전달된 체크된 종목 코드 수집
        codes_to_delete = []
        for code in watchlist.keys():
            if query_params.get(f"chk_{code}") == "on":
                codes_to_delete.append(code)

        if codes_to_delete:
            deleted_names = []
            for code in codes_to_delete:
                if code in watchlist:
                    first_item = watchlist[code][0] if isinstance(watchlist[code], list) else {}
                    deleted_names.append(first_item.get("종목명", code))
                    del watchlist[code]
            
            save_watchlist_data(watchlist)
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.success(f"🗑️ 선택한 종목({', '.join(deleted_names)}) 삭제 완료")
            st.rerun()
        else:
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.warning("⚠️ 삭제할 종목을 선택해 주세요.")
            st.rerun()

    # 상단 컨트롤: 삭제 버튼 우측 배치
    _, col_del = st.columns([4, 1.5])
    with col_del:
        if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
            # 자바스크립트를 통해 폼 데이터를 쿼리 파라미터로 안전하게 전달하여 삭제 실행
            st.components.v1.html("""
                <script>
                    const form = window.parent.document.getElementById("watchlist_form");
                    if (form) {
                        const formData = new FormData(form);
                        let params = new URLSearchParams();
                        params.append("action", "delete_selected");
                        for (let pair of formData.entries()) {
                            params.append(pair[0], pair[1]);
                        }
                        window.parent.location.href = "?" + params.toString();
                    }
                </script>
            """, height=0)

    st.write("")

    # HTML 표 구성 (체크박스를 누를 때 절대 새로고침되지 않는 네이티브 form 구조)
    html_parts = [
        """
        <html>
        <head>
        <style>
            body {
                background-color: #0e1117;
                color: #ffffff !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 0;
            }
            .custom-stock-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
                text-align: center;
                background-color: #0e1117;
            }
            .custom-stock-table th {
                background-color: #262730;
                color: #ffffff !important;
                padding: 10px 6px;
                border: 1px solid #464855;
                text-align: center;
                font-weight: 600;
            }
            .custom-stock-table td {
                padding: 10px 6px;
                border: 1px solid #31333F;
                vertical-align: middle;
                text-align: center;
                color: #ffffff !important;
                background-color: #0e1117;
            }
            .custom-stock-table tr:hover {
                background-color: rgba(255, 255, 255, 0.06);
            }
            .col-select { width: 35px; white-space: nowrap; }
            .col-name { width: 85px; white-space: nowrap; }
            .stock-link {
                color: #58a6ff !important;
                text-decoration: none;
                font-weight: bold;
            }
            .stock-link:hover {
                text-decoration: underline;
            }
        </style>
        <script>
            function toggleAll(source) {
                checkboxes = document.getElementsByName('row_chk');
                for(let i=0, n=checkboxes.length; i<n; i++) {
                    checkboxes[i].checked = source.checked;
                }
            }
        </script>
        </head>
        <body>
        <form id="watchlist_form">
        <table class="custom-stock-table">
            <thead>
                <tr>
                    <th class="col-select"><input type="checkbox" onclick="toggleAll(this)"></th>
                    <th class="col-name">종목명</th>
                    <th>현재가</th>
                    <th>시총</th>
                    <th>적용연도</th>
                    <th>PER</th>
                    <th>PBR</th>
                    <th>ROE</th>
                    <th>매출액</th>
                    <th>영업익</th>
                    <th>당기순이익</th>
                </tr>
            </thead>
            <tbody>
        """
    ]

    total_rows = 0
    for code, info_list in watchlist.items():
        if not isinstance(info_list, list) or len(info_list) == 0:
            continue
        
        total_rows += len(info_list)

        first_info = info_list[0]
        second_info = info_list[1] if len(info_list) > 1 else None

        stock_name = first_info.get("종목명", code)
        curr_price = first_info.get("현재가", "-")
        market_cap = first_info.get("시총", "-")

        rowspan_attr = 'rowspan="2"' if second_info else ''
        naver_stock_url = f"https://m.stock.naver.com/domestic/stock/{code}/total"

        yr1 = first_info.get("적용연도", "-")
        per1 = first_info.get("PER", "-")
        pbr1 = first_info.get("PBR", "-")
        roe1 = first_info.get("ROE", "-")
        rev1 = first_info.get("매출액", "-")
        op1 = first_info.get("영업익", "-")
        np1 = first_info.get("당기순이익", "-")

        html_parts.append(f"""
            <tr>
                <td class="col-select" {rowspan_attr}><input type="checkbox" name="chk_{code}" value="on" class="row_chk" style="transform: scale(1.1);"></td>
                <td class="col-name" {rowspan_attr}><a href="{naver_stock_url}" target="_blank" class="stock-link">{stock_name}</a></td>
                <td {rowspan_attr}>{curr_price}</td>
                <td {rowspan_attr}>{market_cap}</td>
                <td><b>{yr1}</b></td>
                <td>{per1}</td>
                <td>{pbr1}</td>
                <td>{roe1}</td>
                <td>{rev1}</td>
                <td>{op1}</td>
                <td>{np1}</td>
            </tr>
        """)

        if second_info:
            yr2 = second_info.get("적용연도", "-")
            per2 = second_info.get("PER", "-")
            pbr2 = second_info.get("PBR", "-")
            roe2 = second_info.get("ROE", "-")
            rev2 = second_info.get("매출액", "-")
            op2 = second_info.get("영업익", "-")
            np2 = second_info.get("당기순이익", "-")

            html_parts.append(f"""
                <tr>
                    <td><b>{yr2}</b></td>
                    <td>{per2}</td>
                    <td>{pbr2}</td>
                    <td>{roe2}</td>
                    <td>{rev2}</td>
                    <td>{op2}</td>
                    <td>{np2}</td>
                </tr>
            """)

    html_parts.append("</tbody></table></form></body></html>")
    final_html = "".join(html_parts)

    calc_height = max(120, (total_rows * 45) + 60)
    components.html(final_html, height=calc_height, scrolling=False)
