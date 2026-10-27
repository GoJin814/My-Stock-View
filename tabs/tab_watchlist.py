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
    st.markdown("#### ⭐ 관심종목 실적 관리")
    st.caption("현재 시세 탭에서 체크박스로 선택한 종목의 실적 데이터를 불러와 저장합니다. (최신 연도에 데이터가 없으면 값이 존재하는 가장 최근 직전 연도 데이터 자동 탐색, YoY 제외)")

    watchlist = load_watchlist_data()

    # 1. '현재 시세' 탭에서 선택된 종목 코드 가져오기
    query_params = st.query_params
    del_codes_str = query_params.get("del_codes", "")
    selected_codes = [c.strip().zfill(6) for c in del_codes_str.split(",") if c.strip() and c.strip().isdigit()]

    c_btn1, c_btn2 = st.columns([2, 5])
    with c_btn1:
        if st.button("📥 현재 시세 선택 종목 가져오기", type="primary", use_container_width=True):
            if not selected_codes:
                st.warning("⚠️ '현재 시세' 탭에서 체크박스로 선택된 종목이 없습니다. 현재시세 탭에서 종목을 먼저 체크해 주세요.")
            else:
                from api import fetch_basic, fetch_finance, extract_row_list, to_num
                import numpy as np

                added_count = 0
                for code in selected_codes:
                    # 종목명 가져오기
                    basic = fetch_basic(code)
                    stock_name = basic.get("stockName", f"종목_{code}")

                    fin_json = fetch_finance(code)
                    row_list = extract_row_list(fin_json)
                    
                    target_yr_str = "-"
                    fin_snapshot = {}

                    if row_list:
                        # 1단계: 전체 연도 목록 추출 (오름차순 정렬)
                        all_years = set()
                        for row in row_list:
                            columns = row.get("columns", {})
                            if columns:
                                all_years.update(columns.keys())
                        
                        sorted_all_years = sorted(list(all_years))
                        
                        if sorted_all_years:
                            # 2단계: 최신 연도부터 과거 방향(역순)으로 탐색하여 실제 데이터(매출액, 영업이익 등 주요 항목)가 존재하는 가장 가까운 연도 찾기
                            valid_target_k = None
                            for yr in reversed(sorted_all_years):
                                has_valid_data = False
                                for row in row_list:
                                    raw_t = row.get("title", "").strip().replace(" ", "")
                                    # 주요 실적 항목 중 하나라도 값이 있으면 유효한 연도로 판단
                                    if raw_t in ["매출액", "수익", "영업이익", "당기순이익", "당기순익"]:
                                        cols = row.get("columns", {})
                                        val_item = cols.get(yr)
                                        if val_item is not None:
                                            num_v = to_num(val_item.get("value") if isinstance(val_item, dict) else val_item)
                                            if pd.notna(num_v) and num_v != 0:
                                                has_valid_data = True
                                                break
                                if has_valid_data:
                                    valid_target_k = yr
                                    break
                            
                            # 만약 위에서 못 찾았으면 안전하게 가장 마지막 연도 선택
                            if not valid_target_k:
                                valid_target_k = sorted_all_years[-1]

                            target_k = valid_target_k
                            target_yr_str = f"{target_k[:4]}년"

                            # 3단계: 선택된 연도의 각 재무 항목 데이터 추출
                            for row in row_list:
                                raw_title = row.get("title", "").strip().replace(" ", "")
                                columns = row.get("columns", {})
                                if not columns: continue
                                
                                c_item = columns.get(target_k, {})
                                c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)

                                if raw_title in ["매출액", "수익"]:
                                    fin_snapshot["매출액"] = f"{c_val:,.0f}억" if pd.notna(c_val) else "-"
                                elif raw_title == "영업이익":
                                    fin_snapshot["영업익"] = f"{c_val:,.0f}억" if pd.notna(c_val) else "-"
                                elif raw_title in ["당기순이익", "당기순익"]:
                                    fin_snapshot["순이익"] = f"{c_val:,.0f}억" if pd.notna(c_val) else "-"
                                elif any(k in raw_title for k in ["수정주당순이익", "주당순이익", "EPS"]):
                                    fin_snapshot["EPS"] = f"{c_val:,.0f}원" if pd.notna(c_val) else "-"
                                elif any(k in raw_title for k in ["주당순자산", "BPS"]):
                                    fin_snapshot["BPS"] = f"{c_val:,.0f}원" if pd.notna(c_val) else "-"
                                elif "ROE" in raw_title:
                                    fin_snapshot["ROE"] = f"{c_val:.2f}%" if pd.notna(c_val) else "-"

                    watchlist[code] = {
                        "종목명": stock_name,
                        "적용연도": target_yr_str,
                        **fin_snapshot
                    }
                    added_count += 1

                save_watchlist_data(watchlist)
                st.success(f"🎉 총 {added_count}개 종목의 실적 데이터가 유효한 최신 연도 기준으로 관심종목에 반영되었습니다!")
                st.rerun()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택한 뒤 위 버튼을 눌러주세요.")
        return

    # 저장된 관심종목 데이터프레임 구성
    rows = []
    for code, info in watchlist.items():
        row_data = {"종목명": info.get("종목명", code), "적용연도": info.get("적용연도", "-")}
        for k, v in info.items():
            if k not in ["종목명", "적용연도"]:
                row_data[k] = v
        rows.append(row_data)
    
    df_watch = pd.DataFrame(rows)

    st.write("")
    st.markdown("#### 📋 관심종목 실적 리스트")
    st.dataframe(df_watch, hide_index=True, use_container_width=True)

    # 개별 종목 삭제 기능
    st.write("")
    with st.expander("🗑️ 관심종목 개별 관리 (삭제)"):
        options_map = {f"{info.get('종목명', code)} ({code})": code for code, info in watchlist.items()}
        selected_option = st.selectbox("삭제할 종목 선택", options=list(options_map.keys()), key="watch_del_select")
        
        if st.button("선택 종목 삭제", type="primary", key="watch_del_btn"):
            target_code = options_map[selected_option]
            if target_code in watchlist:
                del watchlist[target_code]
                save_watchlist_data(watchlist)
                st.success(f"종목 '{selected_option}' 삭제 완료")
                st.rerun()
