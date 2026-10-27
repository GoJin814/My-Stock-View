import streamlit as st
import pandas as pd
import json
import os
import re
import base64
import requests
import numpy as np
from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num
from styles import render_multi_header_table
from concurrent.futures import ThreadPoolExecutor

WATCHLIST_FILE = "watchlist_codes.txt"

def commit_to_github(filename, content_str, commit_message="Auto-update watchlist from Streamlit"):
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
        payload = {
            "message": commit_message,
            "content": content_b64,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha
            
        put_res = requests.put(url, headers=headers, json=payload, timeout=7)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_watchlist_item(code: str):
    basic = fetch_basic(code)
    integration = fetch_integration(code)
    fin_json = fetch_finance(code)
    
    stock_name = basic.get("stockName", "")
    if not stock_name or stock_name == "-":
        stock_name = ""

    raw_close = basic.get("closePrice", "")
    if not raw_close or raw_close == "-":
        curr_price_str = ""
    else:
        curr_price_str = f"{raw_close}원" if "원" not in str(raw_close) else str(raw_close)

    total_infos = integration.get("totalInfos", [])
    market_cap = ""
    for item in total_infos:
        if str(item.get("code", "")).strip() == "marketValue" or str(item.get("key", "")).strip() in ["시총", "시가총액"]:
            val = str(item.get("value", "")).strip()
            if val and val != "-":
                market_cap = val
            break

    fin_info = {
        "prev_yr": "", "latest_yr": "",
        "prev_per": np.nan, "cur_per": np.nan,
        "prev_pbr": np.nan, "cur_pbr": np.nan,
        "prev_roe": np.nan, "cur_roe": np.nan,
        "prev_rev": np.nan, "cur_rev": np.nan,
        "prev_op": np.nan, "cur_op": np.nan,
        "prev_np": np.nan, "cur_np": np.nan,
    }

    row_list = extract_row_list(fin_json)
    if row_list:
        for row in row_list:
            raw_title = row.get("title", "").strip().replace(" ", "")
            columns = row.get("columns", {})
            if not columns:
                continue
            
            clean_years = []
            for k in columns.keys():
                yr_match = re.search(r'(20\d{2})', str(k))
                if yr_match:
                    clean_years.append((yr_match.group(1), k))
            clean_years = sorted(clean_years, key=lambda x: x[0])
            sorted_keys = [item[1] for item in clean_years]
            
            if not sorted_keys:
                continue
                
            latest_k = sorted_keys[-1]
            prev_k = sorted_keys[-2] if len(sorted_keys) >= 2 else None
            
            fin_info["latest_yr"] = f"{re.search(r'(20\d{2})', str(latest_k)).group(1)}년" if re.search(r'(20\d{2})', str(latest_k)) else ""
            fin_info["prev_yr"] = f"{re.search(r'(20\d{2})', str(prev_k)).group(1)}년" if prev_k and re.search(r'(20\d{2})', str(prev_k)) else ""

            c_item = columns.get(latest_k, {})
            c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)
            p_val = np.nan
            if prev_k:
                p_item = columns.get(prev_k, {})
                p_val = to_num(p_item.get("value") if isinstance(p_item, dict) else p_item)

            if raw_title in ["매출액", "수익"]:
                fin_info["cur_rev"] = c_val
                fin_info["prev_rev"] = p_val
            elif raw_title == "영업이익":
                fin_info["cur_op"] = c_val
                fin_info["prev_op"] = p_val
            elif raw_title in ["당기순이익", "당기순익"]:
                fin_info["cur_np"] = c_val
                fin_info["prev_np"] = p_val
            elif "ROE" in raw_title:
                fin_info["cur_roe"] = c_val
                fin_info["prev_roe"] = p_val
            elif "PER" in raw_title:
                fin_info["cur_per"] = c_val
                fin_info["prev_per"] = p_val
            elif "PBR" in raw_title:
                fin_info["cur_pbr"] = c_val
                fin_info["prev_pbr"] = p_val

    def fmt_val(v, suffix=""):
        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
            return "-"
        if isinstance(v, (int, float)):
            return f"{v:,.0f}{suffix}"
        return f"{str(v).strip()}{suffix}"

    def fmt_rate(v):
        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
            return "-"
        if isinstance(v, (int, float)):
            return f"{v:.2f}%"
        return f"{str(v).strip()}%"

    def fmt_multi(v):
        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
            return "-"
        return f"{str(v).strip()}배"

    items = []
    empty_space = "\u3164"  
    
    if fin_info["prev_yr"]:
        items.append({
            "선택": "",
            "종목코드": code, 
            "종목명": stock_name, 
            "현재가": curr_price_str, 
            "시총": market_cap,
            "적용연도": fin_info["prev_yr"],
            "PER": fmt_multi(fin_info["prev_per"]),
            "PBR": fmt_multi(fin_info["prev_pbr"]),
            "ROE": fmt_rate(fin_info["prev_roe"]),
            "매출액": fmt_val(fin_info["prev_rev"], "억"),
            "영업익": fmt_val(fin_info["prev_op"], "억"),
            "당기순이익": fmt_val(fin_info["prev_np"], "억")
        })

    if fin_info["latest_yr"]:
        is_second_row = (len(items) > 0)
        items.append({
            "선택": "",
            "종목코드": code, 
            "종목명": empty_space if is_second_row else stock_name, 
            "현재가": empty_space if is_second_row else curr_price_str, 
            "시총": empty_space if is_second_row else market_cap,
            "적용연도": fin_info["latest_yr"],
            "PER": fmt_multi(fin_info["cur_per"]),
            "PBR": fmt_multi(fin_info["cur_pbr"]),
            "ROE": fmt_rate(fin_info["cur_roe"]),
            "매출액": fmt_val(fin_info["cur_rev"], "억"),
            "영업익": fmt_val(fin_info["cur_op"], "억"),
            "당기순이익": fmt_val(fin_info["cur_np"], "억")
        })

    return items

def load_watchlist_codes():
    codes = []
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                codes = [line.strip().zfill(6) for line in f.readlines() if line.strip() and line.strip().isdigit()]
                if codes:
                    return list(dict.fromkeys(codes))
        except Exception:
            pass
    return []

def save_watchlist_codes(codes):
    cleaned_codes = [str(c).zfill(6) for c in codes if str(c).strip().isdigit()]
    content = "\n".join(cleaned_codes) + ("\n" if cleaned_codes else "")
    
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        f.write(content)
        
    commit_to_github(
        WATCHLIST_FILE, 
        content, 
        f"Auto-commit watchlist_codes.txt ({len(cleaned_codes)} stocks)"
    )

def render_tab_watchlist(full_csv_records_map=None):
    watchlist_codes = load_watchlist_codes()

    rows = []
    if watchlist_codes:
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(fetch_watchlist_item, watchlist_codes))

        for info_list in results:
            if not info_list:
                continue
            for info in info_list:
                rows.append(info)

    if rows:
        df_watch = pd.DataFrame(rows)
        
        # styles.py의 렌더러가 종목코드와 col_name == "종목명"을 인식하여 네이버 링크를 자동 생성하도록 설정
        render_multi_header_table(
            df_watch,
            tab_name="tab_watchlist",
            has_checkbox=True,
            has_naver_link=True
        )

        st.write("")
        
        col_l, col_r = st.columns([3, 1.8])
        with col_r:
            if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
                raw_del = st.query_params.get("del_codes", "")
                codes_to_delete = [c.strip().zfill(6) for c in str(raw_del).split(",") if c.strip() and c.strip().isdigit()]
                
                if not codes_to_delete:
                    for key, val in st.session_state.items():
                        if val is True:
                            for code in watchlist_codes:
                                if code in str(key) and code not in codes_to_delete:
                                    codes_to_delete.append(code)

                codes_to_delete = list(dict.fromkeys(codes_to_delete))

                if not codes_to_delete:
                    st.warning("⚠️ 삭제할 종목의 체크박스를 먼저 선택해 주세요.")
                else:
                    new_codes = [c for c in watchlist_codes if c not in codes_to_delete]
                    save_watchlist_codes(new_codes)
                    
                    if "del_codes" in st.query_params:
                        del st.query_params["del_codes"]
                        
                    st.success(f"🗑️ 선택한 종목({len(codes_to_delete)}개) 삭제 완료")
                    st.rerun()
    else:
        st.info("등록된 관심종목이 없습니다. 아래 토글을 켜서 종목코드를 추가해 주세요.")

    st.write("---")

    show_manage_box = st.toggle("➕ 종목코드 추가 및 관리", value=False, key="toggle_watchlist_manage")
    if show_manage_box:
        with st.container(border=True):
            if st.button("📥 현재시세 탭에서 체크된 종목 가져오기", use_container_width=True, type="secondary"):
                selected_codes = []
                for param_key, param_val in st.query_params.items():
                    if param_val:
                        codes = [c.strip().zfill(6) for c in str(param_val).split(",") if c.strip() and c.strip().isdigit()]
                        if codes:
                            selected_codes.extend(codes)
                selected_codes = list(dict.fromkeys(selected_codes))

                if not selected_codes:
                    st.warning("⚠️ 현재시세 탭에서 체크박스로 선택된 종목이 없습니다.")
                else:
                    current_codes = load_watchlist_codes()
                    added_count = 0
                    for code in selected_codes:
                        if code not in current_codes:
                            current_codes.append(code)
                            added_count += 1
                    
                    if added_count > 0:
                        save_watchlist_codes(current_codes)
                        st.success(f"🎉 총 {added_count}개의 종목이 관심종목에 추가되었습니다!")
                        st.rerun()
                    else:
                        st.info("ℹ️ 선택한 종목이 이미 모두 관심종목에 등록되어 있습니다.")

            st.markdown("---")
            st.caption("6자리 종목코드를 직접 입력하여 관심종목에 추가할 수 있습니다.")
            add_col1, add_col2 = st.columns([3, 1])
            with add_col1:
                input_code = st.text_input("종목코드 입력", placeholder="예: 005930 (삼성전자)", label_visibility="collapsed", key="input_new_watchlist_code")
            with add_col2:
                if st.button("종목 추가", use_container_width=True, type="primary"):
                    cleaned_code = input_code.strip().zfill(6)
                    if cleaned_code and cleaned_code.isdigit() and len(cleaned_code) == 6:
                        current_codes = load_watchlist_codes()
                        if cleaned_code not in current_codes:
                            current_codes.append(cleaned_code)
                            save_watchlist_codes(current_codes)
                            st.success(f"🎉 종목코드({cleaned_code})가 추가되었습니다!")
                            st.rerun()
                        else:
                            st.warning("⚠️ 이미 관심종목에 등록된 코드입니다.")
                    else:
                        st.error("⚠️ 올바른 6자리 숫자 종목코드를 입력해주세요.")

