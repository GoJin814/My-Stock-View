import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import base64
import json
import requests
from concurrent.futures import ThreadPoolExecutor

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

SAVE_FILE = "saved_codes.txt"

def commit_to_github(filename, content_str, commit_message="Auto-update from Streamlit"):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    
    if not token or not repo:
        st.error("⚠️ Streamlit Secrets에 GITHUB_TOKEN 또는 GITHUB_REPO 설정이 누락되었습니다.")
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
        if put_res.status_code in [200, 201]:
            return True
        else:
            err_data = put_res.json()
            st.error(f"⚠️ GitHub 커밋 실패 ({put_res.status_code}): {err_data.get('message', '')}")
            return False
    except Exception as e:
        st.error(f"⚠️ GitHub 통신 에러: {e}")
        return False

def load_codes():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            codes = [line.strip().zfill(6) for line in f.readlines() if line.strip() and line.strip().isdigit()]
            if codes:
                return list(dict.fromkeys(codes))
    
    default_codes = ["005930"]
    save_codes(default_codes)
    return default_codes

def save_codes(codes):
    content = "\n".join([f"{c.strip().zfill(6)}" for c in codes]) + "\n"
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    commit_to_github(SAVE_FILE, content, f"Auto-commit saved_codes.txt ({len(codes)} stocks)")

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
            # 연도 문자열에서 숫자(연도)만 추출하여 정확한 오름차순 정렬 수행
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

# 상단 헤더
title_col, sync_col = st.columns([5, 1.2])
with title_col:
    st.title("Scanning_주식")
with sync_col:
    st.write("")
    if st.button("🔄 실시간 시세 동기화", use_container_width=True):
        fetch_single_stock.clear()
        st.rerun()

current_codes = load_codes()

if current_codes:
    with st.spinner(f"종목 {len(current_codes)}개 데이터를 동기화하는 중입니다..."):
        scan_basic, scan_perf, scan_share, full_csv_records, most_prev_yr, most_latest_yr = get_all_stocks_parallel(current_codes)

    df_basic = pd.DataFrame(scan_basic)
    df_perf = pd.DataFrame(scan_perf)
    df_share = pd.DataFrame(scan_share)

    # 1. 밸류에이션 필터링
    show_filter = st.toggle("🎯 밸류에이션 (PER / PBR) 범위 조건 필터링", value=False)
    
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
                filter_year = st.selectbox("필터 기준 연도", options=[f"최근 연도 ({most_latest_yr})", f"직전 연도 ({most_prev_yr})"])
            with f_c2:
                use_per_filter = st.checkbox("PER 범위 필터 적용")
                per_min = st.number_input("PER 최소값", value=0.0, step=1.0, disabled=not use_per_filter)
                per_max = st.number_input("PER 최대값", value=30.0, step=1.0, disabled=not use_per_filter)
            with f_c3:
                use_pbr_filter = st.checkbox("PBR 범위 필터 적용")
                pbr_min = st.number_input("PBR 최소값", value=0.0, step=0.1, disabled=not use_pbr_filter)
                pbr_max = st.number_input("PBR 최대값", value=3.0, step=0.1, disabled=not use_pbr_filter)
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

    # 2. 9개 탭 분기 렌더링
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "⭐ 관심종목",
        "📊 현재시세", 
        "💰 주당가치",
        "📈 실적", 
        "🌐 국내지수",
        "📈 수익률-생활비",
        "📈 수익률-연금",
        "📈 수익률-roun",
        "📈 수익률-진우"
    ])

    # 1. 관심종목 탭
    with tab1:
        render_tab_watchlist()

    # 2. 현재 시세 탭
    with tab2:
        st.markdown("""
            <style>
            div[data-testid="stButton"] > button[kind="primary"] {
                background-color: #262730 !important;
                border-color: #464855 !important;
                color: #ffffff !important;
            }
            div[data-testid="stButton"] > button[kind="primary"]:hover {
                background-color: #31333F !important;
                border-color: #5b5e71 !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # 💡 컬럼 비율을 [4.2, 1.8]로 주어 버튼을 오른쪽 끝으로 정렬
        _, b_col0 = st.columns([4.2, 1.8])
        
        with b_col0:
            selected_codes = []
            
            for param_key, param_val in st.query_params.items():
                if param_val and ("code" in param_key.lower() or "del" in param_key.lower() or "sel" in param_key.lower()):
                    codes = [c.strip().zfill(6) for c in str(param_val).split(",") if c.strip() and c.strip().isdigit()]
                    if codes:
                        selected_codes.extend(codes)
            
            if not selected_codes and 'edited_basic_df' in locals() and edited_basic_df is not None:
                if "선택" in edited_basic_df.columns and "종목코드" in edited_basic_df.columns:
                    checked_rows = edited_basic_df[edited_basic_df["선택"] == True]
                    if not checked_rows.empty:
                        selected_codes = checked_rows["종목코드"].dropna().astype(str).str.zfill(6).tolist()

            if not selected_codes and "선택" in df_basic.columns and "종목코드" in df_basic.columns:
                checked_sub = df_basic[df_basic["선택"] == True]
                if not checked_sub.empty:
                    selected_codes = checked_sub["종목코드"].dropna().astype(str).str.zfill(6).tolist()

            selected_codes = list(dict.fromkeys([c.zfill(6) for c in selected_codes if str(c).strip().isdigit() and len(str(c).strip()) <= 6]))

            if st.button("⭐ 관심종목 추가", type="primary", use_container_width=True, key="btn_add_watchlist_market"):
                if not selected_codes:
                    st.warning("⚠️ 체크박스로 선택된 종목이 없습니다. 표의 체크박스를 확인해 주세요.")
                else:
                    WATCHLIST_FILE = "watchlist_codes.txt"
                    watchlist_codes = []
                    
                    if os.path.exists(WATCHLIST_FILE):
                        try:
                            with open(WATCHLIST_FILE, "r", encoding="utf-8") as wf:
                                watchlist_codes = [line.strip().zfill(6) for line in wf.readlines() if line.strip() and line.strip().isdigit()]
                        except Exception:
                            pass

                    added_count = 0
                    for code in selected_codes:
                        if code not in watchlist_codes:
                            watchlist_codes.append(code)
                            added_count += 1

                    if added_count > 0:
                        content = "\n".join(watchlist_codes) + ("\n" if watchlist_codes else "")
                        with open(WATCHLIST_FILE, "w", encoding="utf-8") as wf:
                            wf.write(content)
                        
                        commit_to_github(
                            WATCHLIST_FILE, 
                            content, 
                            f"Auto-commit watchlist_codes.txt ({len(watchlist_codes)} stocks)"
                        )

                        try:
                            st.query_params.clear()
                        except Exception:
                            pass

                        st.success(f"🎉 총 {added_count}개 종목이 관심종목에 추가되었습니다! (상단 '⭐ 관심종목' 탭에서 확인)")
                        st.rerun()
                    else:
                        st.info("ℹ️ 선택한 종목이 이미 모두 관심종목에 등록되어 있습니다.")

        # 테이블 렌더링 및 에디터 수정 결과값(체크 상태 포함) 받기
        edited_basic_df = render_tab_basic(df_basic)

        st.write("")

        # 💡 3개의 버튼을 하나의 행에 나란히 배치 ([삭제, CSV 다운로드, TXT 백업])
        col_del, col_csv, col_bak = st.columns([1.6, 2.2, 1.8])

        with col_del:
            if st.button("🗑️ 선택 종목 삭제", type="primary", use_container_width=True, key="btn_del_basic"):
                raw_del = st.query_params.get("del_codes", "")
                selected_codes = [c.strip().zfill(6) for c in str(raw_del).split(",") if c.strip() and c.strip().isdigit()]

                if selected_codes:
                    remaining_codes = [c for c in current_codes if c not in selected_codes]
                    save_codes(remaining_codes)
                    fetch_single_stock.clear()
                    try:
                        st.query_params.clear()
                    except Exception:
                        pass
                    st.success(f"종목 {len(selected_codes)}개 삭제 및 GitHub 저장 완료")
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
                                    st.success(f"{formatted} 추가 및 GitHub 커밋 완료")
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
                                    st.warning("파일 내에서 유효한 종목코드를 추출하지 못했습니다. 파일 형식을 확인해 주세요.")
                            except Exception as e:
                                st.error(f"파일 처리 중 오류 발생: {e}")

    # 3. 주당 가치 탭
    with tab3:
        render_tab_share(df_share, most_prev_yr, most_latest_yr)

    # 4. 실적 탭
    with tab4:
        render_tab_perf(df_perf, most_prev_yr, most_latest_yr)

    # 5. 국내지수 탭
    with tab5:
        edited_market_df = render_tab_market()
        st.write("")
        render_market_inputs()

    # 6. 생활비 수익률 탭
    with tab6:
        render_tab_returns_living()

    # 7. 연금 수익률 탭
    with tab7:
        render_tab_returns_pension()

    # 8. roun 수익률 탭
    with tab8:
        render_tab_returns_roun()

    # 9. 진우 수익률 탭
    with tab9:
        render_tab_returns_jinwoo()

    # 무새로고침 클라이언트 정렬 및 탭 간 동기화 엔진 마운트
    inject_client_sort_sync_engine()

else:
    st.info("등록된 종목이 없습니다. 아래에서 종목코드를 추가해 주세요.")
    with st.container(border=True):
        st.markdown("##### ➕ 종목코드 추가 및 일괄 등록")
        c_code, c_btn = st.columns([3, 1])
        with c_code:
            init_code = st.text_input("종목코드 (6자리)", placeholder="예: 005930", max_chars=6, key="init_single_code")
        with c_btn:
            st.write("")
            if st.button("종목 추가", use_container_width=True, key="btn_init_add"):
                if init_code.strip():
                    formatted = init_code.strip().zfill(6)
                    save_codes([formatted])
                    st.success(f"{formatted} 등록 완료")
                    st.rerun()

st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 실시간 연동")
