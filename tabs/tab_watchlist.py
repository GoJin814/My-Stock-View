import streamlit as st
import pandas as pd
import json
import os
import base64
import requests
import re
import numpy as np
from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num
from concurrent.futures import ThreadPoolExecutor

WATCHLIST_CACHE_FILE = "watchlist_data.json"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_watchlist_item(code: str):
    """관심종목 코드를 받아 실시간으로 기본정보 및 최근/직전연도 실적을 파싱합니다."""
    basic = fetch_basic(code)
    integration = fetch_integration(code)
    fin_json = fetch_finance(code)
    
    stock_name = basic.get("stockName", "-")
    raw_close = basic.get("closePrice", "-")
    curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)

    total_infos = integration.get("totalInfos", [])
    market_cap = "-"
    for item in total_infos:
        if str(item.get("code", "")).strip() == "marketValue" or str(item.get("key", "")).strip() in ["시총", "시가총액"]:
            market_cap = str(item.get("value", "")).strip()

    fin_info = {
        "prev_yr": "-", "latest_yr": "-",
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
            
            fin_info["latest_yr"] = f"{re.search(r'(20\d{2})', str(latest_k)).group(1)}년" if re.search(r'(20\d{2})', str(latest_k)) else "-"
            fin_info["prev_yr"] = f"{re.search(r'(20\d{2})', str(prev_k)).group(1)}년" if prev_k and re.search(r'(20\d{2})', str(prev_k)) else "-"

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
    if fin_info["prev_yr"] != "-":
        items.append({
            "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
            "적용연도": fin_info["prev_yr"],
            "PER": fmt_multi(fin_info["prev_per"]),
            "PBR": fmt_multi(fin_info["prev_pbr"]),
            "ROE": fmt_rate(fin_info["prev_roe"]),
            "매출액": fmt_val(fin_info["prev_rev"], "억"),
            "영업익": fmt_val(fin_info["prev_op"], "억"),
            "당기순이익": fmt_val(fin_info["prev_np"], "억")
        })

    if fin_info["latest_yr"] != "-":
        items.append({
            "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
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
    if os.path.exists(WATCHLIST_CACHE_FILE):
        try:
            with open(WATCHLIST_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    codes = [str(c).zfill(6) for c in data]
                elif isinstance(data, dict):
                    codes = [str(c).zfill(6) for c in data.keys()]
        except Exception:
            pass
    return list(dict.fromkeys(codes))

def save_watchlist_codes(codes):
    json_text = json.dumps(codes, ensure_ascii=False, indent=2)
    with open(WATCHLIST_CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(json_text)

def render_tab_watchlist(full_csv_records_map=None):
    st.markdown("#### ⭐ 관심종목 실적 관리")
    st.caption("'현재 시세' 탭에서 추가한 관심종목의 직전/최근연도 실적 데이터를 관리합니다. 종목명을 클릭하면 네이버 증권 페이지로 이동합니다.")

    watchlist_codes = load_watchlist_codes()

    if "watchlist_checks" not in st.session_state:
        st.session_state.watchlist_checks = {}

    if watchlist_codes:
        col_l, col_r = st.columns([3, 1.8])
        with col_l:
            select_all = st.checkbox("전체 선택 / 해제", key="watchlist_master_select")
            if select_all != st.session_state.get("_prev_master_select", False):
                for code in watchlist_codes:
                    st.session_state.watchlist_checks[code] = select_all
                st.session_state["_prev_master_select"] = select_all

        with col_r:
            if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True):
                codes_to_delete = [code for code, checked in st.session_state.watchlist_checks.items() if checked]
                if not codes_to_delete:
                    st.warning("⚠️ 삭제할 종목을 선택해 주세요.")
                else:
                    new_codes = [c for c in watchlist_codes if c not in codes_to_delete]
                    save_watchlist_codes(new_codes)
                    st.session_state.watchlist_checks = {}
                    st.success("🗑️ 선택한 종목 삭제 완료")
                    st.rerun()

        st.write("")

    # 병렬로 관심종목 데이터 실시간 로드
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(fetch_watchlist_item, watchlist_codes))

    rows = []
    for info_list in results:
        if not info_list:
            continue
        code = info_list[0]["종목코드"]
        is_checked = st.session_state.watchlist_checks.get(code, False)

        for i, info in enumerate(info_list):
            stock_name = info["종목명"]
            # 링크 주소와 마크다운 서식을 결합하여 올바른 LinkColumn 규격 준수
            naver_url = f"https://m.stock.naver.com/domestic/stock/{code}/total"
            linked_display_name = f"[{stock_name} ↗]({naver_url})" if i == 0 else ""

            if i > 0:
                display_name = ""
                display_price = ""
                display_mcap = ""
                display_check = False
            else:
                display_name = linked_display_name
                display_price = info["현재가"]
                display_mcap = info["시총"]
                display_check = is_checked

            rows.append({
                "선택": display_check,
                "종목코드": code,
                "종목명": display_name,
                "현재가": display_price,
                "시총": display_mcap,
                "적용연도": info["적용연도"],
                "PER": info["PER"],
                "PBR": info["PBR"],
                "ROE": info["ROE"],
                "매출액": info["매출액"],
                "영업익": info["영업익"],
                "당기순이익": info["당기순이익"]
            })

    if rows:
        df_watch = pd.DataFrame(rows)
        edited_df = st.data_editor(
            df_watch,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", default=False, width=40),
                "종목코드": None,
                "종목명": st.column_config.LinkColumn("종목명", display_text=r"\[(.*?)\]", width=100),
                "현재가": st.column_config.TextColumn("현재가", width=90),
                "시총": st.column_config.TextColumn("시총", width=90),
                "적용연도": st.column_config.TextColumn("적용연도", width=70),
            },
            disabled=["종목명", "현재가", "시총", "적용연도", "PER", "PBR", "ROE", "매출액", "영업익", "당기순이익"],
            hide_index=True,
            use_container_width=True,
            key="watchlist_editor"
        )

        if edited_df is not None and "선택" in edited_df.columns:
            for code in watchlist_codes:
                sub_df = edited_df[edited_df["종목코드"] == code]
                if not sub_df.empty:
                    any_checked = sub_df["선택"].any()
                    st.session_state.watchlist_checks[code] = bool(any_checked)
    else:
        st.info("등록된 관심종목이 없습니다. 아래 토글을 켜서 종목코드를 추가해 주세요.")

    st.write("---")

    # 하단 토글 및 종목코드 추가 기능
    show_manage_box = st.toggle("➕ 종목코드 추가 및 관리", value=False, key="toggle_watchlist_manage")
    if show_manage_box:
        with st.container(border=True):
            st.caption("6자리 종목코드를 직접 입력하여 관심종목에 추가할 수 있습니다.")
            add_col1, add_col2 = st.columns([3, 1])
            with add_col1:
                input_code = st.text_input("종목코드 입력", placeholder="예: 005930 (삼성전자)", label_visibility="collapsed", key="input_new_watchlist_code")
            with add_col2:
                if st.button("종목 추가", use_container_width=True, type="primary"):
                    cleaned_code = input_code.strip().zfill(6)
                    if cleaned_code and cleaned_code.isdigit() and len(cleaned_code) == 6:
                        if cleaned_code not in watchlist_codes:
                            watchlist_codes.append(cleaned_code)
                            save_watchlist_codes(watchlist_codes)
                            st.success(f"🎉 종목코드({cleaned_code})가 추가되었습니다!")
                            st.rerun()
                        else:
                            st.warning("⚠️ 이미 관심종목에 등록된 코드입니다.")
                    else:
                        st.error("⚠️ 올바른 6자리 숫자 종목코드를 입력해주세요.")
