import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import json
import requests
from concurrent.futures import ThreadPoolExecutor

# Firebase Admin SDK 연동
import firebase_admin
from firebase_admin import credentials, db

from styles import apply_custom_styles, inject_client_sort_sync_engine
from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num
from tabs.tab_watchlist import render_tab_watchlist
from tabs.tab_basic import render_tab_basic
from tabs.tab_share import render_tab_share
from tabs.tab_perf import render_tab_perf
from tabs.tab_market import render_tab_market, render_market_inputs, load_market_cache, save_market_cache
from tabs.tab_returns_living import render_tab_returns_living
from tabs.tab_returns_pension import render_tab_returns_pension
from tabs.tab_returns_roun import render_tab_returns_roun
from tabs.tab_returns_jinwoo import render_tab_returns_jinwoo

st.set_page_config(page_title="Scanning", layout="wide")
apply_custom_styles()

# -------------------------------------------------------------
# 1. Firebase 초기화 및 동기화 함수
# -------------------------------------------------------------
if not firebase_admin._apps:
    try:
        cred_dict = dict(st.secrets["firebase"])
        db_url = cred_dict.pop("databaseURL", "https://my-stock-view-default-rtdb.firebaseio.com")
        if "private_key" in cred_dict and isinstance(cred_dict["private_key"], str):
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {"databaseURL": db_url})
    except Exception as e:
        st.error(f"⚠️ Firebase 초기화 실패: {e}")

def load_codes():
    """등록된 종목코드 목록 가져오기"""
    try:
        ref = db.reference("my_stock_view/saved_codes")
        codes = ref.get()
        if codes and isinstance(codes, list):
            cleaned = [str(c).strip().zfill(6) for c in codes if str(c).strip().isdigit()]
            if cleaned:
                return list(dict.fromkeys(cleaned))
    except Exception:
        pass

    SAVE_FILE = "saved_codes.txt"
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            codes = [line.strip().zfill(6) for line in f.readlines() if line.strip() and line.strip().isdigit()]
            if codes:
                return list(dict.fromkeys(codes))

    default_codes = ["005930"]
    save_codes(default_codes)
    return default_codes

def save_codes(codes):
    """종목코드 목록 저장"""
    cleaned = list(dict.fromkeys([str(c).strip().zfill(6) for c in codes if str(c).strip().isdigit()]))
    try:
        ref = db.reference("my_stock_view/saved_codes")
        ref.set(cleaned)
    except Exception as e:
        st.error(f"⚠️ Firebase 저장 실패: {e}")

    with open("saved_codes.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned) + "\n")

def get_synced_sort_order():
    """모든 기기 간 실시간 공유되는 종목 정렬 순서 가져오기"""
    try:
        ref = db.reference("my_stock_view/sort_order")
        order = ref.get()
        if order and isinstance(order, list):
            return [str(c).zfill(6) for c in order if str(c).strip()]
    except Exception:
        pass
    return None

def save_synced_sort_order(order_list):
    """현재 기기에서 정렬한 종목 순서를 Firebase에 동기화 저장"""
    try:
        cleaned = [str(c).zfill(6) for c in order_list if str(c).strip()]
        if cleaned:
            db.reference("my_stock_view/sort_order").set(cleaned)
    except Exception:
        pass


# -------------------------------------------------------------
# 2. 증권 데이터 수집 엔진
# -------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_single_stock(code: str):
    basic = fetch_basic(code)
    integration = fetch_integration(code)
    fin_json = fetch_finance(code)
    
    stock_name = basic.get("stockName", "-")
    raw_close = basic.get("closePrice", "-")
    curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)
    numeric_close = to_num(raw_close)

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

    fin_info = {
        "latest_yr": "-", "prev_yr": "-",
        "cur_rev": np.nan, "prev_rev": np.nan, "rev_yoy": np.nan,
        "cur_op": np.nan,  "prev_op": np.nan,  "op_yoy": np.nan,
        "cur_np": np.nan,  "prev_np": np.nan,  "np_yoy": np.nan,
        "cur_eps": np.nan, "prev_eps": np.nan,
        "cur_bps": np.nan, "prev_bps": np.nan,
        "cur_dps": np.nan, "prev_dps": np.nan,
        "cur_roe": np.nan, "prev_roe": np.nan,
        "cur_per": np.nan, "prev_per": np.nan,
        "cur_pbr": np.nan, "prev_pbr": np.nan,
    }

    row_list = extract_row_list(fin_json)
    if row_list:
        for row in row_list:
            raw_title = row.get("title", "").strip().replace(" ", "")
            columns = row.get("columns", {})
            if not columns:
                continue
            sorted_years = sorted(list(columns.keys()), key=lambda x: re.sub(r'[^0-9]', '', str(x)))
            if not sorted_years:
                continue
                
            latest_k = sorted_years[-1]
            prev_k = sorted_years[-2] if len(sorted_years) >= 2 else None
            fin_info["latest_yr"] = f"{latest_k[:4]}년"
            if prev_k:
                fin_info["prev_yr"] = f"{prev_k[:4]}년"

            c_item = columns.get(latest_k, {})
            c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)
            p_val = np.nan
            if prev_k:
                p_item = columns.get(prev_k, {})
                p_val = to_num(p_item.get("value") if isinstance(p_item, dict) else p_item)

            if raw_title in ["매출액", "수익"]:
                fin_info["cur_rev"] = c_val
                fin_info["prev_rev"] = p_val
                if pd.notna(c_val) and pd.notna(p_val) and p_val != 0:
                    fin_info["rev_yoy"] = round(((c_val - p_val) / abs(p_val)) * 100, 2)
            elif raw_title == "영업이익":
                fin_info["cur_op"] = c_val
                fin_info["prev_op"] = p_val
                if pd.notna(c_val) and pd.notna(p_val) and p_val != 0:
                    fin_info["op_yoy"] = round(((c_val - p_val) / abs(p_val)) * 100, 2)
            elif raw_title in ["당기순이익", "당기순익"]:
                fin_info["cur_np"] = c_val
                fin_info["prev_np"] = p_val
                if pd.notna(c_val) and pd.notna(p_val) and p_val != 0:
                    fin_info["np_yoy"] = round(((c_val - p_val) / abs(p_val)) * 100, 2)
            elif any(k in raw_title for k in ["수정주당순이익", "주당순이익", "EPS"]):
                fin_info["cur_eps"] = c_val
                fin_info["prev_eps"] = p_val
            elif any(k in raw_title for k in ["주당순자산", "BPS"]):
                fin_info["cur_bps"] = c_val
                fin_info["prev_bps"] = p_val
            elif any(k in raw_title for k in ["주당배당금", "DPS"]):
                fin_info["cur_dps"] = c_val
                fin_info["prev_dps"] = p_val
            elif "ROE" in raw_title:
                fin_info["cur_roe"] = c_val
                fin_info["prev_roe"] = p_val
            elif "PER" in raw_title:
                fin_info["cur_per"] = c_val
                fin_info["prev_per"] = p_val
            elif "PBR" in raw_title:
                fin_info["cur_pbr"] = c_val
                fin_info["prev_pbr"] = p_val

    dps_display = f"{fin_info['cur_dps']:,.0f}원" if pd.notna(fin_info['cur_dps']) else "-"

    if pd.notna(fin_info["cur_dps"]) and pd.notna(numeric_close) and numeric_close > 0:
        calc_div_yield = (fin_info["cur_dps"] / numeric_close) * 100.0
        div_val = f"{calc_div_yield:.2f}%"
    else:
        div_val = "-"

    rec_basic = {
        "선택": False,
        "종목명": stock_name,
        "종목코드": code,
        "현재가": curr_price_str,
        "시총": market_cap,
        "현재 PER": per_val,
        "현재 PBR": pbr_val,
        "DPS(원)": dps_display,
        "배당수익률": div_val
    }

    rec_perf = {
        "종목명": stock_name,
        "종목코드": code,
        "매출_직전": f"{fin_info['prev_rev']:,.0f}억" if pd.notna(fin_info['prev_rev']) else "-",
        "영업익_직전": f"{fin_info['prev_op']:,.0f}억" if pd.notna(fin_info['prev_op']) else "-",
        "순익_직전": f"{fin_info['prev_np']:,.0f}억" if pd.notna(fin_info['prev_np']) else "-",
        "매출_최근": f"{fin_info['cur_rev']:,.0f}억" if pd.notna(fin_info['cur_rev']) else "-",
        "영업익_최근": f"{fin_info['cur_op']:,.0f}억" if pd.notna(fin_info['cur_op']) else "-",
        "순익_최근": f"{fin_info['cur_np']:,.0f}억" if pd.notna(fin_info['cur_np']) else "-",
        "매출_YoY": f"{fin_info['rev_yoy']:+.1f}%" if pd.notna(fin_info['rev_yoy']) else "-",
        "영업익_YoY": f"{fin_info['op_yoy']:+.1f}%" if pd.notna(fin_info['op_yoy']) else "-",
        "순익_YoY": f"{fin_info['np_yoy']:+.1f}%" if pd.notna(fin_info['np_yoy']) else "-"
    }

    p_per_str = f"{fin_info['prev_per']:.2f}배" if pd.notna(fin_info['prev_per']) else "-"
    p_pbr_str = f"{fin_info['prev_pbr']:.2f}배" if pd.notna(fin_info['prev_pbr']) else "-"
    c_per_str = f"{fin_info['cur_per']:.2f}배" if pd.notna(fin_info['cur_per']) else "-"
    c_pbr_str = f"{fin_info['cur_pbr']:.2f}배" if pd.notna(fin_info['cur_pbr']) else "-"

    rec_share = {
        "종목명": stock_name,
        "종목코드": code,
        "PER_직전": p_per_str, "PBR_직전": p_pbr_str, "ROE_직전": f"{fin_info['prev_roe']:.2f}%" if pd.notna(fin_info['prev_roe']) else "-",
        "EPS_직전": f"{fin_info['prev_eps']:,.0f}원" if pd.notna(fin_info['prev_eps']) else "-", "BPS_직전": f"{fin_info['prev_bps']:,.0f}원" if pd.notna(fin_info['prev_bps']) else "-",
        "PER_최근": c_per_str, "PBR_최근": c_pbr_str, "ROE_최근": f"{fin_info['cur_roe']:.2f}%" if pd.notna(fin_info['cur_roe']) else "-",
        "EPS_최근": f"{fin_info['cur_eps']:,.0f}원" if pd.notna(fin_info['cur_eps']) else "-", "BPS_최근": f"{fin_info['cur_bps']:,.0f}원" if pd.notna(fin_info['cur_bps']) else "-",
        "_num_PER_최근": fin_info['cur_per'], "_num_PBR_최근": fin_info['cur_pbr'], "_num_ROE_최근": fin_info['cur_roe'],
        "_num_EPS_최근": fin_info['cur_eps'], "_num_BPS_최근": fin_info['cur_bps'],
        "_num_PER_직전": fin_info['prev_per'], "_num_PBR_직전": fin_info['prev_pbr'], "_num_ROE_직전": fin_info['prev_roe'],
        "_num_EPS_직전": fin_info['prev_eps'], "_num_BPS_직전": fin_info['prev_bps'],
    }

    rec_csv = {
        "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
        "직전연도": fin_info['prev_yr'], "최근연도": fin_info['latest_yr'],
        "매출액_직전": fin_info['prev_rev'], "매출액_최근": fin_info['cur_rev'], "매출_YoY": fin_info['rev_yoy'],
        "영업익_직전": fin_info['prev_op'], "영업익_최근": fin_info['cur_op'], "영업익_YoY": fin_info['op_yoy'],
        "순이익_직전": fin_info['prev_np'], "순이익_최근": fin_info['cur_np'], "순이익_YoY": fin_info['np_yoy'],
        "EPS_직전": fin_info['prev_eps'], "EPS_최근": fin_info['cur_eps'],
        "BPS_직전": fin_info['prev_bps'], "BPS_최근": fin_info['cur_bps'],
        "ROE_직전": fin_info['prev_roe'], "ROE_최근": fin_info['cur_roe'],
        "PER_직전": fin_info['prev_per'], "PER_최근": fin_info['cur_per'],
        "PBR_직전": fin_info['prev_pbr'], "PBR_최근": fin_info['cur_pbr'],
        "DPS": fin_info['cur_dps'], "현재PER": per_val, "현재PBR": pbr_val, "배당수익률": div_val
    }

    return rec_basic, rec_perf, rec_share, rec_csv, fin_info["prev_yr"], fin_info["latest_yr"]

def get_all_stocks_parallel(codes_list):
    scan_basic, scan_perf, scan_share, full_csv_records = [], [], [], []
    prev_years, latest_years = [], []

    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(fetch_single_stock, codes_list))

    for b, p, s, c, py, ly in results:
        scan_basic.append(b)
        scan_perf.append(p)
        scan_share.append(s)
        full_csv_records.append(c)
        if py != "-": prev_years.append(py)
        if ly != "-": latest_years.append(ly)

    most_prev_yr = max(set(prev_years), key=prev_years.count) if prev_years else "2025년"
    most_latest_yr = max(set(latest_years), key=latest_years.count) if latest_years else "2026년"

    return scan_basic, scan_perf, scan_share, full_csv_records, most_prev_yr, most_latest_yr


# -------------------------------------------------------------
# 3. 최상단 타이틀 & 동기화 버튼 (공간 최적화)
# -------------------------------------------------------------
title_col, sync_col = st.columns([3.8, 1.4])
with title_col:
    st.markdown('<h2 style="margin:0; padding:0; font-size:1.6rem; font-weight:800;">Scanning</h2>', unsafe_allow_html=True)
with sync_col:
    if st.button("🔄 시세 동기화", use_container_width=True, key="btn_sync_top"):
        fetch_single_stock.clear()
        st.rerun()

current_codes = load_codes()

if current_codes:
    # URL 쿼리 파라미터로 들어온 정렬 순서가 있다면 Firebase에 저장
    if "sort_codes" in st.query_params and st.query_params["sort_codes"]:
        new_order = [c.strip().zfill(6) for c in st.query_params["sort_codes"].split(",") if c.strip()]
        if new_order:
            save_synced_sort_order(new_order)

    # Firebase에 저장된 정렬 순서 불러와서 current_codes 순서 재배열
    synced_order = get_synced_sort_order()
    if synced_order:
        ordered_codes = [c for c in synced_order if c in current_codes]
        remaining = [c for c in current_codes if c not in ordered_codes]
        current_codes = ordered_codes + remaining

    with st.spinner("데이터 로딩 중..."):
        scan_basic, scan_perf, scan_share, full_csv_records, most_prev_yr, most_latest_yr = get_all_stocks_parallel(current_codes)

    df_basic = pd.DataFrame(scan_basic)
    df_perf = pd.DataFrame(scan_perf)
    df_share = pd.DataFrame(scan_share)

    # -------------------------------------------------------------
    # ★ 1번 요청: 밸류에이션 필터(좌)와 관심종목 추가 버튼(우)을 1줄로 결합
    # -------------------------------------------------------------
    filter_col, add_btn_col = st.columns([3.2, 2.0])
    with filter_col:
        show_filter = st.toggle("🎯 밸류에이션 (PER / PBR) 필터", value=False)
    
    with add_btn_col:
        selected_codes = []
        for param_key, param_val in st.query_params.items():
            if param_val and ("code" in param_key.lower() or "del" in param_key.lower() or "sel" in param_key.lower()):
                codes = [c.strip().zfill(6) for c in str(param_val).split(",") if c.strip() and c.strip().isdigit()]
                if codes:
                    selected_codes.extend(codes)
        selected_codes = list(dict.fromkeys(selected_codes))

        if st.button("⭐ 관심종목 추가", type="primary", use_container_width=True, key="btn_add_watchlist_top"):
            if not selected_codes:
                st.warning("⚠️ 표에서 체크박스를 먼저 선택해 주세요.")
            else:
                try:
                    w_ref = db.reference("my_stock_view/watchlist_codes")
                    w_codes = w_ref.get() or []
                    if not isinstance(w_codes, list):
                        w_codes = []
                    
                    added = 0
                    for c in selected_codes:
                        if c not in w_codes:
                            w_codes.append(c)
                            added += 1

                    if added > 0:
                        w_ref.set(w_codes)
                        try:
                            st.query_params.clear()
                        except Exception:
                            pass
                        st.success(f"🎉 {added}개 종목 관심종목 등록 완료!")
                        st.rerun()
                    else:
                        st.info("ℹ️ 이미 등록되어 있는 종목입니다.")
                except Exception as e:
                    st.error(f"저장 실패: {e}")

    # 필터 상세 옵션 (토글 열렸을 때만 표시)
    filter_year = f"최근 연도 ({most_latest_yr})"
    use_per_filter = False
    use_pbr_filter = False
    per_min, per_max = 0.0, 30.0
    pbr_min, pbr_max = 0.0, 3.0

    if show_filter:
        with st.container():
            st.markdown('<div class="filter-container-box">', unsafe_allow_html=True)
            f_c1, f_c2, f_c3 = st.columns(3)
            with f_c1:
                filter_year = st.selectbox("기준 연도", options=[f"최근 연도 ({most_latest_yr})", f"직전 연도 ({most_prev_yr})"])
            with f_c2:
                use_per_filter = st.checkbox("PER 필터")
                per_min = st.number_input("PER 최소", value=0.0, step=1.0, disabled=not use_per_filter)
                per_max = st.number_input("PER 최대", value=30.0, step=1.0, disabled=not use_per_filter)
            with f_c3:
                use_pbr_filter = st.checkbox("PBR 필터")
                pbr_min = st.number_input("PBR 최소", value=0.0, step=0.1, disabled=not use_pbr_filter)
                pbr_max = st.number_input("PBR 최대", value=3.0, step=0.1, disabled=not use_pbr_filter)
            st.markdown('</div>', unsafe_allow_html=True)

    filter_prefix = "_최근" if f"최근 연도 ({most_latest_yr})" in filter_year else "_직전"
    target_per_col = f"_num_PER{filter_prefix}"
    target_pbr_col = f"_num_PBR{filter_prefix}"

    valid_mask = pd.Series(True, index=df_share.index)
    if use_per_filter and target_per_col in df_share.columns:
        valid_mask &= (df_share[target_per_col] >= per_min) & (df_share[target_per_col] <= per_max)
    if use_pbr_filter and target_pbr_col in df_share.columns:
        valid_mask &= (df_share[target_pbr_col] >= pbr_min) & (df_share[target_pbr_col] <= pbr_max)

    df_basic = df_basic[valid_mask].reset_index(drop=True)
    df_perf = df_perf[valid_mask].reset_index(drop=True)
    df_share = df_share[valid_mask].reset_index(drop=True)

    # -------------------------------------------------------------
    # 4. 라디오 가로 탭 바 (1줄 고정)
    # -------------------------------------------------------------
    TAB_OPTIONS = [
        "⭐ 관심종목",
        "📊 현재시세", 
        "💰 주당가치",
        "📈 실적", 
        "🌐 국내지수",
        "📈 수익률-생활비",
        "📈 수익률-연금",
        "📈 수익률-roun",
        "📈 수익률-진우"
    ]

    if "current_active_tab" not in st.session_state or st.session_state.current_active_tab not in TAB_OPTIONS:
        st.session_state.current_active_tab = "⭐ 관심종목"

    current_tab = st.radio(
        "탭 네비게이션",
        TAB_OPTIONS,
        index=TAB_OPTIONS.index(st.session_state.current_active_tab),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_tab_radio"
    )
    st.session_state.current_active_tab = current_tab

    # -------------------------------------------------------------
    # 5. 각 탭 분기 렌더링
    # -------------------------------------------------------------
    if current_tab == "⭐ 관심종목":
        render_tab_watchlist()

    elif current_tab == "📊 현재시세":
        edited_basic_df = render_tab_basic(df_basic)
        st.write("")

        col_del, col_csv, col_bak = st.columns([1.6, 2.2, 1.8])
        with col_del:
            if st.button("🗑️ 선택 종목 삭제", type="primary", use_container_width=True, key="btn_del_basic"):
                raw_del = st.query_params.get("del_codes", "")
                del_codes = [c.strip().zfill(6) for c in str(raw_del).split(",") if c.strip() and c.strip().isdigit()]

                if del_codes:
                    remaining_codes = [c for c in current_codes if c not in del_codes]
                    save_codes(remaining_codes)
                    fetch_single_stock.clear()
                    try:
                        st.query_params.clear()
                    except Exception:
                        pass
                    st.success(f"종목 {len(del_codes)}개 삭제 완료")
                    st.rerun()
                else:
                    st.warning("삭제할 종목의 체크박스를 먼저 선택해 주세요.")

        with col_csv:
            csv_data = pd.DataFrame(full_csv_records).to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 전체 결과 CSV 다운로드",
                data=csv_data,
                file_name="종목Scan_비교결과.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_down_csv_basic"
            )

        with col_bak:
            codes_txt_data = "\n".join(current_codes).encode('utf-8')
            st.download_button(
                "📋 종목코드 백업(TXT)",
                data=codes_txt_data,
                file_name="saved_codes_backup.txt",
                mime="text/plain",
                help="현재 등록된 종목코드 목록을 TXT 파일로 내려받습니다.",
                use_container_width=True,
                key="btn_down_txt_basic"
            )

        st.write("")
        show_add_box = st.toggle("➕ 종목코드 추가 및 일괄 등록 (파일 / 텍스트 입력)", value=False)
        
        if show_add_box:
            with st.container():
                tab_single, tab_bulk_text, tab_bulk_file = st.tabs(["단건 추가", "텍스트 일괄 붙여넣기", "파일 일괄 업로드(TXT/CSV/XLSX)"])

                with tab_single:
                    c_code, c_btn = st.columns([3, 1])
                    with c_code:
                        new_code = st.text_input("종목코드 (6자리)", placeholder="예: 005930 (삼성전자)", max_chars=6, key="single_code_input")
                    with c_btn:
                        st.write("")
                        if st.button("종목 추가", use_container_width=True, key="btn_single_add"):
                            if new_code.strip():
                                formatted = new_code.strip().zfill(6)
                                if formatted not in current_codes:
                                    current_codes.append(formatted)
                                    save_codes(current_codes)
                                    st.success(f"{formatted} 추가 완료")
                                    st.rerun()

                with tab_bulk_text:
                    bulk_text = st.text_area(
                        "종목코드 목록 붙여넣기 (줄바꿈, 쉼표, 공백 구분)",
                        placeholder="예시:\n005930\n000660, 035420 035720",
                        height=120,
                        key="area_bulk_codes"
                    )
                    if st.button("📥 텍스트 목록 일괄 추가", type="primary", key="btn_bulk_text_add"):
                        if bulk_text.strip():
                            found_codes = [c.zfill(6) for c in re.findall(r'\b\d{1,6}\b', bulk_text) if len(c.zfill(6)) == 6]
                            if found_codes:
                                new_unique = [c for c in dict.fromkeys(found_codes) if c not in current_codes]
                                if new_unique:
                                    current_codes.extend(new_unique)
                                    save_codes(current_codes)
                                    st.success(f"총 {len(new_unique)}개 종목이 추가되었습니다.")
                                    st.rerun()
                                else:
                                    st.info("입력된 종목코드가 이미 모두 등록되어 있습니다.")
                            else:
                                st.warning("유효한 6자리 종목코드를 찾을 수 없습니다.")

                with tab_bulk_file:
                    up_file = st.file_uploader(
                        "종목코드가 포함된 파일 업로드",
                        type=["txt", "csv", "xlsx", "xls"],
                        key="stock_code_file_uploader"
                    )
                    if up_file is not None:
                        if st.button("📥 파일에서 종목코드 일괄 추출/추가", type="primary", key="btn_bulk_file_add"):
                            try:
                                extracted = []
                                content_bytes = up_file.read()
                                
                                if up_file.name.endswith(".txt"):
                                    content = content_bytes.decode("utf-8", errors="ignore")
                                    extracted = [c.zfill(6) for c in re.findall(r'\b\d{1,6}\b', content) if len(c.zfill(6)) == 6]
                                elif up_file.name.endswith((".xlsx", ".xls")):
                                    import io
                                    df_file = pd.read_excel(io.BytesIO(content_bytes), dtype=str)
                                    for col in df_file.columns:
                                        for val in df_file[col].dropna().astype(str):
                                            digits = re.sub(r'[^0-9]', '', val)
                                            if 1 <= len(digits) <= 6:
                                                extracted.append(digits.zfill(6))
                                elif up_file.name.endswith(".csv"):
                                    import io
                                    df_file = pd.read_csv(io.BytesIO(content_bytes), dtype=str)
                                    for col in df_file.columns:
                                        for val in df_file[col].dropna().astype(str):
                                            digits = re.sub(r'[^0-9]', '', val)
                                            if 1 <= len(digits) <= 6:
                                                extracted.append(digits.zfill(6))

                                if extracted:
                                    new_unique = [c for c in dict.fromkeys(extracted) if c not in current_codes]
                                    if new_unique:
                                        current_codes.extend(new_unique)
                                        save_codes(current_codes)
                                        st.success(f"파일에서 {len(new_unique)}개 종목이 정상 등록되었습니다.")
                                        st.rerun()
                                else:
                                    st.warning("파일 내에서 유효한 종목코드를 추출하지 못했습니다.")
                            except Exception as e:
                                st.error(f"파일 처리 중 오류 발생: {e}")

    elif current_tab == "💰 주당가치":
        render_tab_share(df_share, most_prev_yr, most_latest_yr)

    elif current_tab == "📈 실적":
        render_tab_perf(df_perf, most_prev_yr, most_latest_yr)

    elif current_tab == "🌐 국내지수":
        edited_market_df = render_tab_market()
        st.write("")
        render_market_inputs()

    elif current_tab == "📈 수익률-생활비":
        render_tab_returns_living()

    elif current_tab == "📈 수익률-연금":
        render_tab_returns_pension()

    elif current_tab == "📈 수익률-roun":
        render_tab_returns_roun()

    elif current_tab == "📈 수익률-진우":
        render_tab_returns_jinwoo()

    inject_client_sort_sync_engine()

else:
    st.info("등록된 종목이 없습니다. 아래에서 종목코드를 추가해 주세요.")
