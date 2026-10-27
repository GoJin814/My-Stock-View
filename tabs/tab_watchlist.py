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
    st.markdown("#### ⭐ 관심종목 실적 관리 (직전연도 / 최신연도)")
    st.caption("현재 시세 탭에서 선택한 종목의 '직전연도'와 '가장 마지막 연도' 데이터를 정확히 매칭하여 2단 행으로 관리합니다.")

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
                from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num
                import numpy as np

                added_count = 0
                for code in selected_codes:
                    # 기본 시세 정보 (현재가, 시총, PER, PBR)
                    basic = fetch_basic(code)
                    integration = fetch_integration(code)
                    
                    stock_name = basic.get("stockName", f"종목_{code}")
                    
                    raw_close = basic.get("closePrice", "-")
                    curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)

                    total_infos = integration.get("totalInfos", [])
                    market_cap = "-"
                    integration_dict = {}
                    for item in total_infos:
                        item_code = str(item.get("code", "")).strip()
                        item_key = str(item.get("key", "")).strip()
                        item_val = str(item.get("value", "")).strip()
                        if item_code == "marketValue" or item_key in ["시총", "시가총액"]:
                            market_cap = item_val
                        integration_dict[item_key] = item_val

                    raw_per = basic.get("per", integration_dict.get("PER", "-"))
                    raw_pbr = basic.get("pbr", integration_dict.get("PBR", "-"))
                    
                    per_val = f"{str(raw_per).replace('배', '')}배" if raw_per not in ["-", "N/A", None] else "-"
                    pbr_val = f"{str(raw_pbr).replace('배', '')}배" if raw_pbr not in ["-", "N/A", None] else "-"

                    # 재무 데이터 추출 (엄격히 직전연도와 마지막 연도만 타겟팅)
                    fin_json = fetch_finance(code)
                    row_list = extract_row_list(fin_json)
                    
                    sorted_all_years = []
                    if row_list:
                        all_years = set()
                        for row in row_list:
                            columns = row.get("columns", {})
                            if columns:
                                all_years.update(columns.keys())
                        sorted_all_years = sorted(list(all_years))

                    # 정확히 마지막 연도와 직전 연도 추출
                    latest_k = sorted_all_years[-1] if sorted_all_years else None
                    prev_k = sorted_all_years[-2] if len(sorted_all_years) >= 2 else None

                    def get_metrics_for_yr(yr_key):
                        metrics = {"매출액": "-", "영업익": "-", "당기순이익": "-", "ROE": "-"}
                        if not yr_key or not row_list:
                            return metrics
                        for row in row_list:
                            raw_title = row.get("title", "").strip().replace(" ", "")
                            columns = row.get("columns", {})
                            if not columns: continue
                            c_item = columns.get(yr_key, {})
                            c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)

                            if raw_title in ["매출액", "수익"]:
                                metrics["매출액"] = f"{c_val:,.0f}억" if pd.notna(c_val) and c_val != 0 else "-"
                            elif raw_title == "영업이익":
                                metrics["영업익"] = f"{c_val:,.0f}억" if pd.notna(c_val) and c_val != 0 else "-"
                            elif raw_title in ["당기순이익", "당기순익"]:
                                metrics["당기순이익"] = f"{c_val:,.0f}억" if pd.notna(c_val) and c_val != 0 else "-"
                            elif "ROE" in raw_title:
                                metrics["ROE"] = f"{c_val:.2f}%" if pd.notna(c_val) and c_val != 0 else "-"
                        return metrics

                    prev_metrics = get_metrics_for_yr(prev_k)
                    latest_metrics = get_metrics_for_yr(latest_k)

                    prev_yr_str = f"{prev_k[:4]}년" if prev_k else ""
                    latest_yr_str = f"{latest_k[:4]}년" if latest_k else ""

                    # 2단 행 구성 (직전연도 / 최신연도)
                    row_list_data = []

                    if prev_k:
                        row_list_data.append({
                            "종목명": stock_name,
                            "현재가": curr_price_str,
                            "시총": market_cap,
                            "적용연도": prev_yr_str,
                            "PER": per_val,
                            "PBR": pbr_val,
                            "ROE": prev_metrics["ROE"],
                            "매출액": prev_metrics["매출액"],
                            "영업익": prev_metrics["영업익"],
                            "당기순이익": prev_metrics["당기순이익"]
                        })

                    if latest_k:
                        row_list_data.append({
                            "종목명": stock_name,
                            "현재가": curr_price_str,
                            "시총": market_cap,
                            "적용연도": latest_yr_str,
                            "PER": per_val,
                            "PBR": pbr_val,
                            "ROE": latest_metrics["ROE"],
                            "매출액": latest_metrics["매출액"],
                            "영업익": latest_metrics["영업익"],
                            "당기순이익": latest_metrics["당기순이익"]
                        })

                    watchlist[code] = row_list_data
                    added_count += 1

                save_watchlist_data(watchlist)
                st.success(f"🎉 총 {added_count}개 종목의 실적 데이터가 관심종목에 반영되었습니다!")
                st.rerun()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택한 뒤 위 버튼을 눌러주세요.")
        return

    # 저장된 데이터프레임 구성 (종목명, 현재가, 시총은 첫 번째 행에만 표시)
    rows = []
    for code, info_list in watchlist.items():
        if isinstance(info_list, list):
            for i, info in enumerate(info_list):
                if i == 0:
                    rows.append({
                        "종목명": info.get("종목명", code),
                        "현재가": info.get("현재가", "-"),
                        "시총": info.get("시총", "-"),
                        "적용연도": info.get("적용연도", ""),
                        "PER": info.get("PER", "-"),
                        "PBR": info.get("PBR", "-"),
                        "ROE": info.get("ROE", "-"),
                        "매출액": info.get("매출액", "-"),
                        "영업익": info.get("영업익", "-"),
                        "당기순이익": info.get("당기순이익", "-")
                    })
                else:
                    rows.append({
                        "종목명": "",
                        "현재가": "",
                        "시총": "",
                        "적용연도": info.get("적용연도", ""),
                        "PER": info.get("PER", "-"),
                        "PBR": info.get("PBR", "-"),
                        "ROE": info.get("ROE", "-"),
                        "매출액": info.get("매출액", "-"),
                        "영업익": info.get("영업익", "-"),
                        "당기순이익": info.get("당기순이익", "-")
                    })
        elif isinstance(info_list, dict):
            rows.append(info_list)
    
    df_watch = pd.DataFrame(rows)

    st.write("")
    st.markdown("#### 📋 관심종목 리스트 (직전연도 / 최신연도)")
    st.dataframe(df_watch, hide_index=True, use_container_width=True)

    # 개별 종목 삭제 기능
    st.write("")
    with st.expander("🗑️ 관심종목 개별 관리 (삭제)"):
        options_map = {}
        for code, info_list in watchlist.items():
            first_item = info_list[0] if isinstance(info_list, list) and len(info_list) > 0 else info_list
            s_name = first_item.get("종목명", code) if isinstance(first_item, dict) else code
            options_map[f"{s_name} ({code})"] = code

        selected_option = st.selectbox("삭제할 종목 선택", options=list(options_map.keys()), key="watch_del_select")
        
        if st.button("선택 종목 삭제", type="primary", key="watch_del_btn"):
            target_code = options_map[selected_option]
            if target_code in watchlist:
                del watchlist[target_code]
                save_watchlist_data(watchlist)
                st.success(f"종목 '{selected_option}' 삭제 완료")
                st.rerun()
