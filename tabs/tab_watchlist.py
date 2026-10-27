import streamlit as st
import pandas as pd
import json
import os
import base64
import requests

WATCHLIST_CACHE_FILE = "watchlist_data.json"

def load_watchlist_data():
    if os.path.exists(WATCHLIST_CACHE_FILE):
        try:
            with open(WATCHLIST_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
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
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(WATCHLIST_CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(json_text)
    commit_to_github(WATCHLIST_CACHE_FILE, json_text, "Auto-commit watchlist_data.json")

def render_tab_watchlist(full_csv_records_map=None):
    st.markdown("#### ⭐ 관심종목 실적 관리")
    st.caption("'현재 시세' 탭에서 추가한 관심종목의 직전/최근연도 실적 데이터를 병합된 셀 구조로 관리합니다.")

    watchlist = load_watchlist_data()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택하고 [관심종목 추가] 버튼을 눌러주세요.")
        return

    st.write("")

    # 세션 상태에 삭제 선택용 체크박스 관리 딕셔너리 초기화
    if "watchlist_checks" not in st.session_state:
        st.session_state.watchlist_checks = {}

    # 상단 일괄 삭제 및 전체 선택 컨트롤
    col_c1, col_c2, _ = st.columns([1.5, 2, 4])
    with col_c1:
        if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
            codes_to_delete = [code for code, checked in st.session_state.watchlist_checks.items() if checked]
            if not codes_to_delete:
                st.warning("⚠️ 삭제할 종목을 선택해 주세요.")
            else:
                deleted_names = []
                for code in codes_to_delete:
                    if code in watchlist:
                        first_item = watchlist[code][0] if isinstance(watchlist[code], list) else {}
                        deleted_names.append(first_item.get("종목명", code))
                        del watchlist[code]
                
                # 체크 상태 초기화 후 저장 및 새로고침
                st.session_state.watchlist_checks = {}
                save_watchlist_data(watchlist)
                st.success(f"🗑️ 선택한 종목({', '.join(deleted_names)}) 삭제 완료")
                st.rerun()

    with col_c2:
        select_all = st.checkbox("전체 선택 / 해제", key="watchlist_select_all_cb")
        if select_all != st.session_state.get("_prev_select_all", False):
            for code in watchlist.keys():
                st.session_state.watchlist_checks[code] = select_all
            st.session_state["_prev_select_all"] = select_all

    st.write("")

    # HTML 표 디자인 및 스타일 정의 (가운데 정렬 및 병합 셀 스타일)
    html_table = """
    <style>
        .custom-stock-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: center;
            background-color: transparent;
        }
        .custom-stock-table th {
            background-color: #262730;
            color: #ffffff;
            padding: 10px 8px;
            border: 1px solid #464855;
            text-align: center;
            font-weight: 600;
        }
        .custom-stock-table td {
            padding: 10px 8px;
            border: 1px solid #31333F;
            vertical-align: middle;
            text-align: center;
        }
        .custom-stock-table tr:hover {
            background-color: rgba(255, 255, 255, 0.03);
        }
    </style>
    <table class="custom-stock-table">
        <thead>
            <tr>
                <th style="width: 50px;">선택</th>
                <th>종목명</th>
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

    for code, info_list in watchlist.items():
        if not isinstance(info_list, list) or len(info_list) == 0:
            continue
        
        # 세션 상태 체크값 연동
        is_checked = st.session_state.watchlist_checks.get(code, False)
        checked_attr = "checked" if is_checked else ""

        first_info = info_list[0]
        second_info = info_list[1] if len(info_list) > 1 else None

        stock_name = first_info.get("종목명", code)
        curr_price = first_info.get("현재가", "-")
        market_cap = first_info.get("시총", "-")

        # 행 개수 산정 (2단 행 병합 구조)
        rowspan_attr = 'rowspan="2"' if second_info else ''

        # 1번째 줄 (직전연도 등)
        yr1 = first_info.get("적용연도", "-")
        per1 = first_info.get("PER", "-")
        pbr1 = first_info.get("PBR", "-")
        roe1 = first_info.get("ROE", "-")
        rev1 = first_info.get("매출액", "-")
        op1 = first_info.get("영업익", "-")
        np1 = first_info.get("당기순이익", "-")

        html_table += f"""
            <tr>
                <td {rowspan_attr}><input type="checkbox" name="chk_{code}" {checked_attr} onclick="window.location.href='?toggle_code={code}'"></td>
                <td {rowspan_attr}><b>{stock_name}</b></td>
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
        """

        # 2번째 줄 (최근연도 등 존재할 경우)
        if second_info:
            yr2 = second_info.get("적용연도", "-")
            per2 = second_info.get("PER", "-")
            pbr2 = second_info.get("PBR", "-")
            roe2 = second_info.get("ROE", "-")
            rev2 = second_info.get("매출액", "-")
            op2 = second_info.get("영업익", "-")
            np2 = second_info.get("당기순이익", "-")

            html_table += f"""
                <tr>
                    <td><b>{yr2}</b></td>
                    <td>{per2}</td>
                    <td>{pbr2}</td>
                    <td>{roe2}</td>
                    <td>{rev2}</td>
                    <td>{op2}</td>
                    <td>{np2}</td>
                </tr>
            """

    html_table += "</tbody></table>"

    # 체크박스 클릭 시 쿼리 파라미터를 통해 세션 상태 토글 반영
    query_params = st.query_params
    toggle_code = query_params.get("toggle_code", "")
    if toggle_code and toggle_code in watchlist:
        st.session_state.watchlist_checks[toggle_code] = not st.session_state.watchlist_checks.get(toggle_code, False)
        # 쿼리 파라미터 초기화 후 리런
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

    # 커스텀 HTML 표 렌더링
    st.markdown(html_table, unsafe_allow_html=True)
