import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import re
from datetime import date
from api import to_num, normalize_date

MARKET_CACHE_FILE = "market_history.json"

def load_market_cache():
    if os.path.exists(MARKET_CACHE_FILE):
        try:
            with open(MARKET_CACHE_FILE, "r", encoding="utf-8") as f:
                raw_cache = json.load(f)
                cleaned_cache = {}
                for k, v in raw_cache.items():
                    norm_k = normalize_date(k)
                    if norm_k:
                        cleaned_cache[norm_k] = v
                return cleaned_cache
        except Exception:
            return {}
    return {}

def save_market_cache(data):
    with open(MARKET_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def render_market_inputs():
    market_cache = load_market_cache()

    # 1. 파일 일괄 가져오기 (CSV / JSON)
    with st.expander("📂 국내지수 데이터 일괄 불러오기 (CSV / JSON 파일 업로드)", expanded=False):
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
                    st.success(f"총 {count}건의 지수 데이터가 성공적으로 병합되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"파일 불러오기 중 오류가 발생했습니다: {e}")

    # 2. 신규 값 직접 입력 폼
    with st.expander("➕ 국내지수 지표 데이터 직접 입력 / 갱신", expanded=False):
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

        target_dt_str = normalize_date(in_date)

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

def render_tab_market():
    st.subheader("🌐 국내지수 및 자금동향 내역")
    market_cache = load_market_cache()

    if market_cache:
        sorted_dates = sorted(
            market_cache.keys(),
            key=lambda x: pd.to_datetime(x, errors='coerce'),
            reverse=True
        )
        
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

        # 세션 상태 기반 전체 선택 초기화
        if "select_all_market" not in st.session_state:
            st.session_state["select_all_market"] = False

        c_info, c_sel_all = st.columns([5, 2])
        with c_info:
            st.write(f"📊 저장된 지표 내역 (총 {len(df_market_rendered)}영업일)")
        with c_sel_all:
            select_all_m = st.checkbox("☑️ 전체 선택 / 해제", key="select_all_market_checkbox")

        if select_all_m != st.session_state["select_all_market"]:
            st.session_state["select_all_market"] = select_all_m
            df_market_rendered.insert(0, "선택", select_all_m)
        else:
            df_market_rendered.insert(0, "선택", st.session_state["select_all_market"])

        disabled_cols = [c for c in df_market_rendered.columns if c != "선택"]
        edited_market_df = st.data_editor(
            df_market_rendered,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", default=False, width="small", pinned=True),
                "일시": st.column_config.TextColumn("일시", pinned=True),
            },
            disabled=disabled_cols,
            hide_index=True,
            use_container_width=True,
            key=f"market_editor_{st.session_state['select_all_market']}"
        )
        return edited_market_df
    else:
        st.info("💡 등록된 지표 데이터가 없습니다. 화면 하단 입력란에 수치를 입력하거나 CSV/JSON 파일을 불러와주세요.")
        return None
