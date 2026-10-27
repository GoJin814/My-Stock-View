import streamlit as st
import pandas as pd
import json
import os
import base64
import requests

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

    if "watchlist_checks" not in st.session_state:
        st.session_state.watchlist_checks = {}

    # 상단 우측 버튼 영역 설정 (전체 선택 체크박스 + 삭제 버튼)
    col_l, col_r = st.columns([4, 2])
    with col_l:
        select_all = st.checkbox("전체 선택 / 해제", key="watchlist_master_select")
        if select_all != st.session_state.get("_prev_master_select", False):
            for code in watchlist.keys():
                st.session_state.watchlist_checks[code] = select_all
            st.session_state["_prev_master_select"] = select_all

    with col_r:
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
                
                st.session_state.watchlist_checks = {}
                save_watchlist_data(watchlist)
                st.success(f"🗑️ 선택한 종목({', '.join(deleted_names)}) 삭제 완료")
                st.rerun()

    st.write("")

    # 데이터프레임 구성 (체크박스 컬럼 포함)
    rows = []
    for code, info_list in watchlist.items():
        if not isinstance(info_list, list) or len(info_list) == 0:
            continue
        
        is_checked = st.session_state.watchlist_checks.get(code, False)

        for i, info in enumerate(info_list):
            def clean_cell(val):
                if val is None or pd.isna(val) or str(val).strip().lower() in ["none", ""]:
                    return "-"
                return str(val).strip()

            stock_name = clean_cell(info.get("종목명", code))
            naver_url = f"https://m.stock.naver.com/domestic/stock/{code}/total"
            linked_name = f"[{stock_name}]({naver_url})"

            if i == 0:
                rows.append({
                    "선택": is_checked,
                    "종목코드": code,
                    "종목명": linked_name,
                    "현재가": clean_cell(info.get("현재가", "-")),
                    "시총": clean_cell(info.get("시총", "-")),
                    "적용연도": clean_cell(info.get("적용연도", "")),
                    "PER": clean_cell(info.get("PER", "-")),
                    "PBR": clean_cell(info.get("PBR", "-")),
                    "ROE": clean_cell(info.get("ROE", "-")),
                    "매출액": clean_cell(info.get("매출액", "-")),
                    "영업익": clean_cell(info.get("영업익", "-")),
                    "당기순이익": clean_cell(info.get("당기순이익", "-"))
                })
            else:
                rows.append({
                    "선택": None,  # 병합된 하단 행은 체크박스 비활성화
                    "종목코드": code,
                    "종목명": "",
                    "현재가": "",
                    "시총": "",
                    "적용연도": clean_cell(info.get("적용연도", "")),
                    "PER": clean_cell(info.get("PER", "-")),
                    "PBR": clean_cell(info.get("PBR", "-")),
                    "ROE": clean_cell(info.get("ROE", "-")),
                    "매출액": clean_cell(info.get("매출액", "-")),
                    "영업익": clean_cell(info.get("영업익", "-")),
                    "당기순이익": clean_cell(info.get("당기순이익", "-"))
                })

    df_watch = pd.DataFrame(rows)

    edited_df = st.data_editor(
        df_watch,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width=40),
            "종목코드": None,
            "종목명": st.column_config.LinkColumn("종목명", display_text=r"\[(.*?)\]", width=90),
        },
        disabled=["종목명", "현재가", "시총", "적용연도", "PER", "PBR", "ROE", "매출액", "영업익", "당기순이익"],
        hide_index=True,
        use_container_width=True,
        key="watchlist_editor"
    )

    # 사용자가 에디터에서 체크박스를 조작한 경우 실시간으로 세션 상태에 반영
    if edited_df is not None and "선택" in edited_df.columns:
        for idx, row in edited_df.iterrows():
            code = row.get("종목코드")
            val = row.get("선택")
            if code and pd.notna(val):
                st.session_state.watchlist_checks[code] = bool(val)
