import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import json
from datetime import date

from styles import apply_custom_styles, render_multi_header_table, render_single_header_table
from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num, normalize_date

st.set_page_config(page_title="Scanning_주식", layout="wide")
apply_custom_styles()

SAVE_FILE = "saved_codes.txt"
MARKET_CACHE_FILE = "market_history.json"

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

def load_market_cache():
    if os.path.exists(MARKET_CACHE_FILE):
        try:
            with open(MARKET_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_market_cache(data):
    with open(MARKET_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

st.title("Scanning_주식")
current_codes = load_codes()

if current_codes:
    scan_basic = []
    scan_perf = []
    scan_share = []
    full_csv_records = []
    prev_years = []
    latest_years = []

    with st.spinner("증권 데이터를 동기화하고 있습니다..."):
        for code in current_codes:
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
                    raw_title = row.get("title", "").strip()
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
                    elif raw_title in ["수정주당순이익(원)", "주당순이익(원)", "EPS"]:
                        fin_info["cur_eps"] = c_val
                        fin_info["prev_eps"] = p_val
                    elif raw_title in ["주당순자산(원)", "주당순자산가치(원)", "BPS"]:
                        fin_info["cur_bps"] = c_val
                        fin_info["prev_bps"] = p_val
                    elif raw_title in ["주당배당금(원)", "주당배당금", "DPS"]:
                        fin_info["cur_dps"] = c_val
                        fin_info["prev_dps"] = p_val
                    elif raw_title in ["ROE(%)", "ROE"]:
                        fin_info["cur_roe"] = c_val
                        fin_info["prev_roe"] = p_val
                    elif raw_title in ["PER(배)", "PER"]:
                        fin_info["cur_per"] = c_val
                        fin_info["prev_per"] = p_val
                    elif raw_title in ["PBR(배)", "PBR"]:
                        fin_info["cur_pbr"] = c_val
                        fin_info["prev_pbr"] = p_val

            if fin_info["prev_yr"] != "-":
                prev_years.append(fin_info["prev_yr"])
            if fin_info["latest_yr"] != "-":
                latest_years.append(fin_info["latest_yr"])

            dps_display = f"{fin_info['cur_dps']:,.0f}원" if pd.notna(fin_info['cur_dps']) else "-"

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

            scan_perf.append({
                "종목명": stock_name,
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

            p_per_str = f"{fin_info['prev_per']:.2f}배" if pd.notna(fin_info['prev_per']) else "-"
            p_pbr_str = f"{fin_info['prev_pbr']:.2f}배" if pd.notna(fin_info['prev_pbr']) else "-"
            c_per_str = f"{fin_info['cur_per']:.2f}배" if pd.notna(fin_info['cur_per']) else "-"
            c_pbr_str = f"{fin_info['cur_pbr']:.2f}배" if pd.notna(fin_info['cur_pbr']) else "-"

            scan_share.append({
                "종목명": stock_name,
                "EPS_직전": f"{fin_info['prev_eps']:,.0f}원" if pd.notna(fin_info['prev_eps']) else "-",
                "BPS_직전": f"{fin_info['prev_bps']:,.0f}원" if pd.notna(fin_info['prev_bps']) else "-",
                "ROE_직전": f"{fin_info['prev_roe']:.2f}%" if pd.notna(fin_info['prev_roe']) else "-",
                "PER_직전": p_per_str,
                "PBR_직전": p_pbr_str,
                "EPS_최근": f"{fin_info['cur_eps']:,.0f}원" if pd.notna(fin_info['cur_eps']) else "-",
                "BPS_최근": f"{fin_info['cur_bps']:,.0f}원" if pd.notna(fin_info['cur_bps']) else "-",
                "ROE_최근": f"{fin_info['cur_roe']:.2f}%" if pd.notna(fin_info['cur_roe']) else "-",
                "PER_최근": c_per_str,
                "PBR_최근": c_pbr_str
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

    df_basic = pd.DataFrame(scan_basic)
    df_perf = pd.DataFrame(scan_perf)
    df_share = pd.DataFrame(scan_share)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 기본 & 시세", 
        "📈 실적 & 성장성 (2개년 비교)", 
        "💰 주당 가치 (2개년 비교)",
        "🌐 국내지수 Monitor"
    ])

    with tab1:
        disabled_cols = [c for c in df_basic.columns if c != "선택"]
        edited_df = st.data_editor(
            df_basic,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", default=False, width="small", pinned=True),
                "종목명": st.column_config.TextColumn("종목명", pinned=True),
            },
            disabled=disabled_cols,
            hide_index=True,
            use_container_width=True,
            key="tab1_editor"
        )

    with tab2:
        top_headers_perf = [
            ("종목명", 1, False),
            (most_prev_yr, 3, True),
            (most_latest_yr, 3, True),
            ("성장률 (YoY)", 3, False)
        ]
        sub_headers_perf = [
            "매출액", "영업이익", "당기순익",
            "매출액", "영업이익", "당기순익",
            "매출 YoY", "영업익 YoY", "순익 YoY"
        ]
        render_multi_header_table(
            df_perf,
            top_headers=top_headers_perf,
            sub_headers=sub_headers_perf,
            divider_indices=[3, 6]
        )

    with tab3:
        top_headers_share = [
            ("종목명", 1, False),
            (most_prev_yr, 5, True),
            (most_latest_yr, 5, False)
        ]
        sub_headers_share = [
            "EPS", "BPS", "ROE", "PER", "PBR",
            "EPS", "BPS", "ROE", "PER", "PBR"
        ]
        render_multi_header_table(
            df_share,
            top_headers=top_headers_share,
            sub_headers=sub_headers_share,
            divider_indices=[5]
        )

    with tab4:
        st.subheader("📝 국내지수 및 자금동향 관리")
        market_cache = load_market_cache()

        # 1. 파일 일괄 가져오기 (CSV / JSON)
        with st.expander("📂 기존 데이터 일괄 불러오기 (CSV / JSON 파일 업로드)", expanded=False):
            uploaded_file = st.file_uploader("파일 선택", type=["csv", "json"], key="market_file_uploader")
            if uploaded_file is not None:
                if st.button("📥 데이터 병합하여 저장하기", type="primary"):
                    try:
                        count = 0
                        if uploaded_file.name.endswith(".json"):
                            imported_data = json.load(uploaded_file)
                            for k, v in imported_data.items():
                                dt_norm = normalize_date(k)
                                if dt_norm:
                                    market_cache[dt_norm] = v
                                    count += 1
                        else:
                            df_up = pd.read_csv(uploaded_file)
                            # 컬럼명의 공백, 개행(\n, \r), 특수문자 정리
                            df_up.columns = [re.sub(r'[\s\n\r]+', '', str(c)) for c in df_up.columns]

                            for _, row in df_up.iterrows():
                                r_dict = {k: v for k, v in row.items()}
                                
                                dt_raw = r_dict.get("일시") or r_dict.get("날짜") or r_dict.get("Date") or list(r_dict.values())[0]
                                dt_norm = normalize_date(dt_raw)
                                if not dt_norm:
                                    continue
                                
                                k_v = to_num(r_dict.get("KOSPI") or r_dict.get("코스피"))
                                mcap_v = r_dict.get("시가총액(억원)") or r_dict.get("시총") or r_dict.get("시가총액") or "-"
                                per_v = r_dict.get("PER") or "-"
                                pbr_v = r_dict.get("PBR") or "-"
                                dep_v = to_num(r_dict.get("고객예탁금(억원)") or r_dict.get("고객예탁금") or r_dict.get("예탁금"))
                                crd_v = to_num(r_dict.get("신용잔고(억원)") or r_dict.get("신용잔고") or r_dict.get("신용융자"))
                                fx_v = to_num(r_dict.get("환율") or r_dict.get("원달러환율"))

                                market_cache[dt_norm] = {
                                    "KOSPI": k_v if pd.notna(k_v) else None,
                                    "시가총액(억원)": str(mcap_v).strip(),
                                    "PER": str(per_v).strip(),
                                    "PBR": str(pbr_v).strip(),
                                    "고객예탁금(억원)": dep_v if pd.notna(dep_v) else None,
                                    "신용잔고(억원)": crd_v if pd.notna(crd_v) else None,
                                    "환율": fx_v if pd.notna(fx_v) else None
                                }
                                count += 1
                        save_market_cache(market_cache)
                        st.success(f"총 {count}건의 데이터가 성공적으로 병합되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"파일 불러오기 중 오류가 발생했습니다: {e}")

        # 2. 직접 입력 폼
        with st.form("market_input_form", clear_on_submit=False):
            r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
            with r1_c1:
                in_date = st.date_input("기준일자", value=date.today())
            with r1_c2:
                in_kospi = st.text_input("KOSPI (포인트)", placeholder="예: 2650.50")
            with r1_c3:
                in_mcap = st.text_input("시가총액(억원)", placeholder="예: 2150000")
            with r1_c4:
                in_fx = st.text_input("환율 (원)", placeholder="예: 1350.5")

            r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
            with r2_c1:
                in_per = st.text_input("PER (배)", placeholder="예: 12.50")
            with r2_c2:
                in_pbr = st.text_input("PBR (배)", placeholder="예: 0.95")
            with r2_c3:
                in_dep = st.text_input("고객예탁금(억원)", placeholder="예: 54000")
            with r2_c4:
                in_credit = st.text_input("신용잔고(억원)", placeholder="예: 18000")

            f_btn1, f_btn2, _ = st.columns([1.5, 1.5, 3])
            with f_btn1:
                save_manual_btn = st.form_submit_button("💾 데이터 저장 / 갱신", type="primary", use_container_width=True)
            with f_btn2:
                del_manual_btn = st.form_submit_button("🗑️ 해당 일자 삭제", use_container_width=True)

        target_dt_str = in_date.strftime("%Y-%m-%d")

        if save_manual_btn:
            k_val = to_num(in_kospi)
            dep_val = to_num(in_dep)
            crd_val = to_num(in_credit)
            fx_val = to_num(in_fx)

            market_cache[target_dt_str] = {
                "KOSPI": k_val if pd.notna(k_val) else None,
                "시가총액(억원)": in_mcap.strip() if in_mcap.strip() else "-",
                "PER": in_per.strip() if in_per.strip() else "-",
                "PBR": in_pbr.strip() if in_pbr.strip() else "-",
                "고객예탁금(억원)": dep_val if pd.notna(dep_val) else None,
                "신용잔고(억원)": crd_val if pd.notna(crd_val) else None,
                "환율": fx_val if pd.notna(fx_val) else None
            }
            save_market_cache(market_cache)
            st.success(f"{target_dt_str} 지표가 저장되었습니다.")
            st.rerun()

        if del_manual_btn:
            if target_dt_str in market_cache:
                del market_cache[target_dt_str]
                save_market_cache(market_cache)
                st.success(f"{target_dt_str} 기록이 삭제되었습니다.")
                st.rerun()
            else:
                st.info(f"{target_dt_str}에 저장된 데이터가 없습니다.")

        # 3. 테이블 렌더링
        if market_cache:
            sorted_dates = sorted(market_cache.keys(), reverse=True)
            table_rows = []
            for dt in sorted_dates:
                info = market_cache[dt]
                k_val = info.get("KOSPI")
                kospi_str = f"{float(k_val):,.2f}" if (k_val is not None and not np.isnan(k_val)) else "-"

                mcap_raw = info.get("시가총액(억원)", "-")
                mcap_num = to_num(mcap_raw)
                mcap_str = f"{mcap_num:,.0f}" if pd.notna(mcap_num) else str(mcap_raw)

                dep_val = info.get("고객예탁금(억원)")
                cust_dep_str = f"{float(dep_val):,.0f}" if (dep_val is not None and not np.isnan(dep_val)) else "-"

                crd_val = info.get("신용잔고(억원)")
                credit_tot_str = f"{float(crd_val):,.0f}" if (crd_val is not None and not np.isnan(crd_val)) else "-"

                ex_val = info.get("환율")
                ex_str = f"{float(ex_val):,.1f}원" if (ex_val is not None and not np.isnan(ex_val)) else "-"

                # 고객예탁금 / 시가총액, 신용잔고 / 시가총액 (%)
                dep_to_mcap_str = "-"
                crd_to_mcap_str = "-"
                if pd.notna(mcap_num) and mcap_num > 0:
                    if dep_val is not None and not np.isnan(dep_val):
                        dep_to_mcap_str = f"{(float(dep_val) / mcap_num) * 100:.2f}%"
                    if crd_val is not None and not np.isnan(crd_val):
                        crd_to_mcap_str = f"{(float(crd_val) / mcap_num) * 100:.2f}%"

                table_rows.append({
                    "일시": dt,
                    "KOSPI": kospi_str,
                    "시가총액(억원)": mcap_str,
                    "PER": str(info.get("PER", "-")),
                    "PBR": str(info.get("PBR", "-")),
                    "고객예탁금(억원)": cust_dep_str,
                    "신용잔고(억원)": credit_tot_str,
                    "환율": ex_str,
                    "고객예탁금/시가총액": dep_to_mcap_str,
                    "신용잔고/시가총액": crd_to_mcap_str
                })

            df_market_rendered = pd.DataFrame(table_rows)
            st.write(f"📊 저장된 지표 내역 (총 {len(df_market_rendered)}영업일)")
            render_single_header_table(df_market_rendered, divider_indices=[4, 6])
        else:
            st.info("💡 등록된 지표 데이터가 없습니다. 상단 입력란에 수치를 입력하거나 CSV/JSON 파일을 불러와주세요.")

    btn_col1, btn_col2, _ = st.columns([1.5, 2, 4])
    with btn_col1:
        delete_btn = st.button("🗑️ 선택 종목 삭제", type="primary", use_container_width=True)
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
        selected_codes = edited_df[edited_df["선택"] == True]["종목코드"].tolist()
        if selected_codes:
            remaining_codes = [c for c in current_codes if c not in selected_codes]
            save_codes(remaining_codes)
            st.success(f"{len(selected_codes)}개 종목 삭제 완료")
            st.rerun()
        else:
            st.warning("삭제할 종목의 체크박스를 먼저 선택해 주세요. (기본 & 시세 탭)")
else:
    st.info("등록된 종목이 없습니다. 아래에서 종목코드를 추가해 주세요.")

st.write("")
col_add, col_btn = st.columns([3, 1])
with col_add:
    new_code = st.text_input("➕ 추가할 종목코드 (6자리)", placeholder="예: 005930 (삼성전자)", max_chars=6)
with col_btn:
    st.write("")
    if st.button("종목 추가", use_container_width=True):
        if new_code.strip():
            formatted = new_code.strip().zfill(6)
            if formatted not in current_codes:
                current_codes.append(formatted)
                save_codes(current_codes)
                st.success(f"{formatted} 추가 완료")
                st.rerun()

st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 실시간 연동")
