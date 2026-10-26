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

def render_tab_watchlist():
    st.markdown("#### ⭐ 관심종목 최신 연도 실적 관리")
    st.caption("현재 시세 탭에서 선택한 종목을 불러와 가장 마지막 연도 데이터(YoY 제외)를 영구 저장하고 모니터링합니다.")

    watchlist = load_watchlist_data()

    # 1. '현재 시세' 탭의 세션 상태에서 선택된 종목 코드 가져오기 (기존 체크박스 브리지 활용)
    # 쿼리 파라미터나 st.session_state에 저장된 선택 종목 확인
    query_params = st.query_params
    del_codes_str = query_params.get("del_codes", "")
    selected_codes_from_market = [c.strip() for c in del_codes_str.split(",") if c.strip()]

    # UI 조작 버튼 영역
    c_btn1, c_btn2 = st.columns([2, 5])
    with c_btn1:
        if st.button("📥 현재 시세 선택 종목 가져오기", type="primary", use_container_width=True):
            if not selected_codes_from_market:
                st.warning("'현재 시세' 탭에서 체크박스로 선택된 종목이 없습니다.")
            else:
                # '실적' 탭 등에서 사용하는 전체 데이터 소스나 네이버 API 캐시에서 해당 종목들의 마지막 연도 데이터를 추출해 저장
                # 여기서는 세션에 캐시된 실적 데이터가 있다면 활용, 없으면 안내
                st.success(f"선택된 {len(set(selected_codes_from_market))}개 종목을 관심종목으로 연동 중입니다...")
                # 실제 데이터 매핑 로직 연결 지점
                st.rerun()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택한 뒤 위 버튼을 눌러주세요.")
        return

    # 데이터프레임 변환 및 출력
    rows = []
    for code, info in watchlist.items():
        rows.append({"종목코드": code, **info})
    
    df_watch = pd.DataFrame(rows)

    st.write("")
    st.markdown("#### 📋 관심종목 최신 연도 실적 리스트")
    st.dataframe(df_watch, hide_index=True, use_container_width=True)

    # 개별 종목 삭제 기능
    st.write("")
    with st.expander("🗑️ 관심종목 개별 관리 (삭제)"):
        target_code = st.selectbox("삭제할 종목 선택", options=list(watchlist.keys()))
        if st.button("선택 종목 삭제", type="primary"):
            if target_code in watchlist:
                del watchlist[target_code]
                save_watchlist_data(watchlist)
                st.success(f"종목 코드 {target_code} 삭제 완료")
                st.rerun()
