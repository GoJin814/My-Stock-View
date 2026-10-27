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
    numeric_close = to_num(raw_close)

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
    
    # 연도별 데이터를 임시로 담을 딕셔너리 (예: {"2025년": {...}, "2026년": {...}})
    year_data_map = {}

    if row_list:
        for row in row_list:
            raw_title = row.get("title", "").strip().replace(" ", "")
            columns = row.get("columns", {})
            if not columns:
                continue
            
            # 각 컬럼의 연도 키를 분석하여 실제 연도(2025, 2026 등)와 매칭
            for k, c_item in columns.items():
                yr_match = re.search(r'(20\d{2})', str(k))
                if not yr_match:
                    continue
                yr_str = yr_match.group(1) + "년"  # 예: "2025년", "2026년"
                
                c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)
                
                if yr_str not in year_data_map:
                    year_data_map[yr_str] = {
                        "PER": np.nan, "PBR": np.nan, "ROE": np.nan,
                        "매출액": np.nan, "영업익": np.nan, "당기순이익": np.nan
                    }

                if raw_title in ["매출액", "수익"]:
                    year_data_map[yr_str]["매출액"] = c_val
                elif raw_title == "영업이익":
                    year_data_map[yr_str]["영업익"] = c_val
                elif raw_title in ["당기순이익", "당기순익"]:
                    year_data_map[yr_str]["당기순이익"] = c_val
                elif "ROE" in raw_title:
                    year_data_map[yr_str]["ROE"] = c_val
                elif "PER" in raw_title:
                    year_data_map[yr_str]["PER"] = c_val
                elif "PBR" in raw_title:
                    year_data_map[yr_str]["PBR"] = c_val

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
    # 연도 문자열(2025년, 2026년 등)을 오름차순으로 정렬하여 정확한 칸에 배치
    sorted_collected_years = sorted(list(year_data_map.keys()), key=lambda x: re.sub(r'[^0-9]', '', x))

    for yr in sorted_collected_years:
        metrics = year_data_map[yr]
        items.append({
            "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
            "적용연도": yr,
            "PER": fmt_multi(metrics["PER"]),
            "PBR": fmt_multi(metrics["PBR"]),
            "ROE": fmt_rate(metrics["ROE"]),
            "매출액": fmt_val(metrics["매출액"], "억"),
            "영업익": fmt_val(metrics["영업익"], "억"),
            "당기순이익": fmt_val(metrics["당기순이익"], "억")
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

    if not watchlist_codes:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택하고 [관심종목 추가] 버튼을 눌러주세요.")
        return

    st.write("")

    if "watchlist_checks" not in st.session_state:
        st.session_state.watchlist_checks = {}

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
            naver_url = f"https://m.stock.naver.com/domestic/stock/{code}/total"
            linked_name = f"[{stock_name}]({naver_url})"

            rows.append({
                "선택": is_checked if i == 0 else False,
                "종목코드": code,
                "종목명": linked_name,
                "현재가": info["현재가"],
                "시총": info["시총"],
                "적용연도": info["적용연도"],
                "PER": info["PER"],
                "PBR": info["PBR"],
                "ROE": info["ROE"],
                "매출액": info["매출액"],
                "영업익": info["영업익"],
                "당기순이익": info["당기순이익"]
            })

    if not rows:
        st.info("표시할 관심종목 데이터가 없습니다.")
        return

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

    if edited_df is not None and "선택" in edited_df.columns:
        for code in watchlist_codes:
            sub_df = edited_df[edited_df["종목코드"] == code]
            if not sub_df.empty:
                any_checked = sub_df["선택"].any()
                st.session_state.watchlist_checks[code] = bool(any_checked)
