import streamlit as st
import pandas as pd
import numpy as np
import os
import re

from styles import apply_custom_styles
from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num
from tabs.tab_basic import render_tab_basic
from tabs.tab_share import render_tab_share
from tabs.tab_perf import render_tab_perf
from tabs.tab_market import render_tab_market, render_market_inputs, load_market_cache, save_market_cache

st.set_page_config(page_title="Scanning_주식", layout="wide")
apply_custom_styles()

SAVE_FILE = "saved_codes.txt"

def load_codes():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            codes = [line.strip().zfill(6) for line in f.readlines() if line.strip()]
            return list(dict.fromkeys(codes))
    return ["178320", "001130", "086450", "007690", "095660", "161890"]

def save_codes(codes):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        for c in codes:
            f.write(f"{c.strip().zfill(6)}\n")

@st.cache_data(ttl=600, show_spinner="증권 데이터를 동기화하고 있습니다...")
def fetch_all_stock_data(codes_tuple):
    scan_basic = []
    scan_perf = []
    scan_share = []
    full_csv_records = []
    prev_years = []
    latest_years = []

    for code in codes_tuple:
        basic = fetch_basic(code)
        integration = fetch_integration(code)
        fin_json = fetch_finance(code)
        
        stock_name = basic.get("stockName", "-")
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
        raw_div = basic.get("dividendYield", integration_dict.get("배당수익률", "-"))
        
        per_val = f"{str(raw_per).replace('배', '')}배" if raw_per not in ["-", "N/A", None] else "-"
        pbr_val = f"{str(raw_pbr).replace('배', '')}배" if raw_pbr not in ["-", "N/A", None] else "-"
        div_val = f"{raw_div}%" if (raw_div not in ["-", "N/A", None] and "%" not in str(raw_div)) else str(raw_div)

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
                sorted_years = sorted(list(columns.keys()))
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

        if fin_info["prev_yr"] != "-":
            prev_years.append(fin_info["prev_yr"])
        if fin_info["latest_yr"] != "-":
            latest_years.append(fin_info["latest_yr"])

        dps_display = f"{fin_info['cur_dps']:,.0f}원" if pd.notna(fin_info['cur_dps']) else "-"

        # 기본 & 시세
        scan_basic.append({
            "선택": False,
            "종목명": stock_name,
            "종목코드": code,
            "현재가": curr_price_str,
            "시총": market_cap,
            "현재 PER": per_val,
            "현재 PBR": pbr_val,
            "DPS(원)": dps_display,
            "배당수익률": div_val
        })

        # 실적 & 성장성
        scan_perf.append({
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
        })

        # 주당 가치
        p_per_str = f"{fin_info['prev_per']:.2f}배" if pd.notna(fin_info['prev_per']) else "-"
        p_pbr_str = f"{fin_info['prev_pbr']:.2f}배" if pd.notna(fin_info['prev_pbr']) else "-"
        c_per_str = f"{fin_info['cur_per']:.2f}배" if pd.notna(fin_info['cur_per']) else "-"
        c_pbr_str = f"{fin_info['cur_pbr']:.2f}배" if pd.notna(fin_info['cur_pbr']) else "-"

        scan_share.append({
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
        })

        full_csv_records.append({
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
        })

    most_prev_yr = max(set(prev_years), key=prev_years.count) if prev_years else "2025년"
    most_latest_yr = max(set(latest_years), key=latest_years.count) if latest_years else "2026년"

    return scan_basic, scan_perf, scan_share, full_csv_records, most_prev_yr, most_latest_yr

title_col, sync_col = st.columns([5, 1])
with title_col:
    st.title("Scanning_주식")
with sync_col:
    st.write("")
    if st.button("🔄 실시간 시세 동기화", use_container_width=True):
        fetch_all_stock_data.clear()
        st.rerun()

current_codes = load_codes()

if current_codes:
    scan_basic, scan_perf, scan_share, full_csv_records, most_prev_yr, most_latest_yr = fetch_all_stock_data(tuple(current_codes))

    df_basic = pd.DataFrame(scan_basic)
    df_perf = pd.DataFrame(scan_perf)
    df_share = pd.DataFrame(scan_share)

    # 1. 정렬 제어
    sort_col1, sort_col2, _ = st.columns([2, 1.5, 3.5])
    with sort_col1:
        sort_metric = st.selectbox(
            "🔽 정렬 기준 지표 (모든 탭 동기화)",
            options=[
                "기본 순서 (등록순)",
                f"최근 PER ({most_latest_yr})",
                f"최근 PBR ({most_latest_yr})",
                f"최근 ROE ({most_latest_yr})",
                f"최근 EPS ({most_latest_yr})",
                f"최근 BPS ({most_latest_yr})",
                f"직전 PER ({most_prev_yr})",
                f"직전 PBR ({most_prev_yr})",
                f"직전 ROE ({most_prev_yr})",
                f"직전 EPS ({most_prev_yr})",
                f"직전 BPS ({most_prev_yr})",
            ],
            index=0
        )
    with sort_col2:
        sort_order = st.radio("정렬 방향", options=["오름차순 (▲)", "내림차순 (▼)"], horizontal=True)

    # 2. 밸류에이션 필터링
    with st.expander("🎯 밸류에이션(PER / PBR) 범위 조건 필터링", expanded=False):
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

    filter_prefix = "_최근" if f"최근 연도 ({most_latest_yr})" in filter_year else "_직전"
    target_per_col = f"_num_PER{filter_prefix}"
    target_pbr_col = f"_num_PBR{filter_prefix}"

    valid_mask = pd.Series(True, index=df_share.index)
    if use_per_filter:
        valid_mask &= (df_share[target_per_col] >= per_min) & (df_share[target_per_col] <= per_max)
    if use_pbr_filter:
        valid_mask &= (df_share[target_pbr_col] >= pbr_min) & (df_share[target_pbr_col] <= pbr_max)

    df_basic = df_basic[valid_mask].copy()
    df_perf = df_perf[valid_mask].copy()
    df_share = df_share[valid_mask].copy()

    # 정렬 수행
    metric_map = {
        f"최근 PER ({most_latest_yr})": "_num_PER_최근",
        f"최근 PBR ({most_latest_yr})": "_num_PBR_최근",
        f"최근 ROE ({most_latest_yr})": "_num_ROE_최근",
        f"최근 EPS ({most_latest_yr})": "_num_EPS_최근",
        f"최근 BPS ({most_latest_yr})": "_num_BPS_최근",
        f"직전 PER ({most_prev_yr})": "_num_PER_직전",
        f"직전 PBR ({most_prev_yr})": "_num_PBR_직전",
        f"직전 ROE ({most_prev_yr})": "_num_ROE_직전",
        f"직전 EPS ({most_prev_yr})": "_num_EPS_직전",
        f"직전 BPS ({most_prev_yr})": "_num_BPS_직전",
    }

    if sort_metric in metric_map and not df_share.empty:
        target_col = metric_map[sort_metric]
        is_asc = (sort_order == "오름차순 (▲)")
        sorted_indices = df_share[target_col].sort_values(ascending=is_asc, na_position='last').index
        
        df_basic = df_basic.loc[sorted_indices].reset_index(drop=True)
        df_perf = df_perf.loc[sorted_indices].reset_index(drop=True)
        df_share = df_share.loc[sorted_indices].reset_index(drop=True)
    else:
        df_basic = df_basic.reset_index(drop=True)
        df_perf = df_perf.reset_index(drop=True)
        df_share = df_share.reset_index(drop=True)

    # 4개 탭 렌더링
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 기본 & 시세", 
        "💰 주당 가치 (2개년 비교)",
        "📈 실적 & 성장성 (2개년 비교)", 
        "🌐 국내지수 Monitor"
    ])

    with tab1:
        edited_df = render_tab_basic(df_basic)

    with tab2:
        render_tab_share(df_share, most_prev_yr, most_latest_yr)

    with tab3:
        render_tab_perf(df_perf, most_prev_yr, most_latest_yr)

    with tab4:
        edited_market_df = render_tab_market()

    # 하단 컨트롤
    btn_col1, btn_col2, _ = st.columns([1.5, 2, 4])
    with btn_col1:
        delete_btn = st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True)
    with btn_col2:
        csv_data = pd.DataFrame(full_csv_records).to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 전체 결과 CSV 다운로드",
            data=csv_data,
            file_name="종목Scan_비교결과.csv",
            mime="text/csv",
            use_container_width=True
        )

    if delete_btn:
        deleted_anything = False

        if edited_df is not None and not edited_df.empty:
            selected_codes = edited_df[edited_df["선택"] == True]["종목코드"].tolist()
            if selected_codes:
                remaining_codes = [c for c in current_codes if c not in selected_codes]
                save_codes(remaining_codes)
                fetch_all_stock_data.clear()
                st.success(f"종목 {len(selected_codes)}개 삭제 완료")
                deleted_anything = True

        if edited_market_df is not None and not edited_market_df.empty:
            selected_dates = edited_market_df[edited_market_df["선택"] == True]["일시"].tolist()
            if selected_dates:
                m_cache = load_market_cache()
                for d in selected_dates:
                    m_cache.pop(d, None)
                save_market_cache(m_cache)
                st.success(f"지수 데이터 {len(selected_dates)}일자 삭제 완료")
                deleted_anything = True

        if deleted_anything:
            st.rerun()
        else:
            st.warning("삭제할 항목(종목 또는 일자)의 체크박스를 먼저 선택해 주세요.")
else:
    st.info("등록된 종목이 없습니다. 아래에서 종목코드를 추가해 주세요.")

# 종목코드 추가 및 일괄 등록
st.write("")
with st.expander("➕ 종목코드 추가 및 일괄 등록 (파일 / 텍스트 입력)", expanded=False):
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
                        fetch_all_stock_data.clear()
                        st.success(f"{formatted} 추가 완료")
                        st.rerun()

    with tab_bulk_text:
        bulk_text = st.text_area(
            "종목코드 목록 붙여넣기 (줄바꿈, 쉼표, 공백 구분)",
            placeholder="예시:\n005930\n000660, 035420 035720",
            height=120
        )
        if st.button("📥 텍스트 목록 일괄 추가", type="primary", key="btn_bulk_text_add"):
            if bulk_text.strip():
                found_codes = re.findall(r'\b\d{6}\b', bulk_text)
                if found_codes:
                    new_unique = [c for c in dict.fromkeys(found_codes) if c not in current_codes]
                    if new_unique:
                        current_codes.extend(new_unique)
                        save_codes(current_codes)
                        fetch_all_stock_data.clear()
                        st.success(f"총 {len(new_unique)}개 종목이 추가되었습니다: {', '.join(new_unique)}")
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
                    if up_file.name.endswith(".txt"):
                        content = up_file.read().decode("utf-8", errors="ignore")
                        extracted = re.findall(r'\b\d{6}\b', content)
                    elif up_file.name.endswith((".xlsx", ".xls")):
                        df_file = pd.read_excel(up_file, dtype=str)
                        for col in df_file.columns:
                            items = df_file[col].dropna().astype(str).str.strip().str.zfill(6)
                            valid_codes = [c for c in items if len(c) == 6 and c.isdigit()]
                            extracted.extend(valid_codes)
                    elif up_file.name.endswith(".csv"):
                        df_file = pd.read_csv(up_file, dtype=str)
                        for col in df_file.columns:
                            items = df_file[col].dropna().astype(str).str.strip().str.zfill(6)
                            valid_codes = [c for c in items if len(c) == 6 and c.isdigit()]
                            extracted.extend(valid_codes)

                    if extracted:
                        new_unique = [c for c in dict.fromkeys(extracted) if c not in current_codes]
                        if new_unique:
                            current_codes.extend(new_unique)
                            save_codes(current_codes)
                            fetch_all_stock_data.clear()
                            st.success(f"파일에서 {len(new_unique)}개 종목이 등록되었습니다: {', '.join(new_unique)}")
                            st.rerun()
                        else:
                            st.info("파일 내 종목코드가 이미 등록되어 있습니다.")
                    else:
                        st.warning("파일에서 6자리 종목코드를 추출하지 못했습니다.")
                except Exception as e:
                    st.error(f"파일 처리 중 오류 발생: {e}")

# 국내지수 파일 업로드 및 수기 입력 영역
st.write("")
render_market_inputs()

st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 실시간 연동")
