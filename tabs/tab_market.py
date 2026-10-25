import streamlit as st
import pandas as pd
import json
import os
import re

MARKET_CACHE_FILE = "market_indices_cache.json"

def normalize_date(val):
    if not val or pd.isna(val):
        return ""
    val_str = str(val).strip()
    parsed = pd.to_datetime(val_str, errors='coerce')
    if pd.notnull(parsed):
        return parsed.strftime('%Y-%m-%d')
    digits = re.sub(r'[^0-9]', '', val_str)
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return val_str

def load_market_cache():
    if os.path.exists(MARKET_CACHE_FILE):
        try:
            with open(MARKET_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}

def save_market_cache(cache_data):
    try:
        with open(MARKET_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"지수 데이터 저장 중 오류 발생: {e}")

def render_tab_market():
    m_cache = load_market_cache()
    if not m_cache:
        st.info("기록된 국내지수 데이터가 없습니다. 아래 입력 패널에서 데이터를 등록해 주세요.")
        return None

    # 일자 역순 정렬 (최신 날짜가 위로)
    sorted_dates = sorted(list(m_cache.keys()), reverse=True)
    records = []
    for d in sorted_dates:
        row = {"선택": False, "일시": d}
        row.update(m_cache[d])
        records.append(row)

    df_market = pd.DataFrame(records)
    
    # 3층 복합 헤더 렌더링
    st.markdown("""
        <div style="overflow-x: auto; margin-bottom: 1rem;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem; text-align: center;">
            <thead>
                <tr style="background-color: var(--secondary-background-color, #f0f2f6);">
                    <th rowspan="3" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">선택</th>
                    <th rowspan="3" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">일시</th>
                    <th colspan="4" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">KOSPI</th>
                    <th colspan="4" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">KOSDAQ</th>
                    <th colspan="4" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">KOSPI200</th>
                </tr>
                <tr style="background-color: var(--secondary-background-color, #f0f2f6);">
                    <th colspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">PER</th>
                    <th colspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">PBR</th>
                    <th colspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">PER</th>
                    <th colspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">PBR</th>
                    <th colspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">PER</th>
                    <th colspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">PBR</th>
                </tr>
                <tr style="background-color: var(--secondary-background-color, #f0f2f6);">
                    <th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">최근</th><th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">12M Fwd</th>
                    <th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">최근</th><th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">12M Fwd</th>
                    <th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">최근</th><th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">12M Fwd</th>
                    <th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">최근</th><th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">12M Fwd</th>
                    <th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">최근</th><th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">12M Fwd</th>
                    <th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">최근</th><th style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">12M Fwd</th>
                </tr>
            </thead>
        </table>
        </div>
    """, unsafe_allow_html=True)

    disabled_cols = [c for c in df_market.columns if c != "선택"]
    edited_df = st.data_editor(
        df_market,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width="small"),
            "일시": st.column_config.TextColumn("일시", width="medium"),
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key="market_monitor_editor"
    )

    # 지수 데이터 백업 다운로드 버튼 제공
    json_bytes = json.dumps(m_cache, ensure_ascii=False, indent=2).encode('utf-8')
    st.download_button(
        "💾 국내지수 전체 백업(JSON 다운로드)",
        data=json_bytes,
        file_name="market_indices_backup.json",
        mime="application/json",
        help="서버가 재부팅되더라도 언제든 복원할 수 있도록 지수 데이터를 파일로 저장합니다."
    )

    return edited_df

def render_market_inputs():
    with st.expander("🌐 국내지수 밸류에이션 데이터 수기 입력 / 백업 복원", expanded=False):
        t_manual, t_restore = st.tabs(["수기 입력", "📂 백업 파일(JSON) 복원"])

        with t_manual:
            c_date, c_submit = st.columns([2, 1])
            with c_date:
                input_date = st.date_input("기준 일자", key="market_input_date")
            date_str = str(input_date)

            st.write("**지수별 밸류에이션 입력**")
            col_kpi, col_kdq, col_k200 = st.columns(3)

            with col_kpi:
                st.markdown("##### KOSPI")
                kpi_per_c = st.text_input("PER (최근)", key="kpi_per_c", placeholder="예: 11.23")
                kpi_per_f = st.text_input("PER (12M Fwd)", key="kpi_per_f", placeholder="예: 9.85")
                kpi_pbr_c = st.text_input("PBR (최근)", key="kpi_pbr_c", placeholder="예: 0.95")
                kpi_pbr_f = st.text_input("PBR (12M Fwd)", key="kpi_pbr_f", placeholder="예: 0.88")

            with col_kdq:
                st.markdown("##### KOSDAQ")
                kdq_per_c = st.text_input("PER (최근)", key="kdq_per_c", placeholder="예: 18.50")
                kdq_per_f = st.text_input("PER (12M Fwd)", key="kdq_per_f", placeholder="예: 14.20")
                kdq_pbr_c = st.text_input("PBR (최근)", key="kdq_pbr_c", placeholder="예: 1.65")
                kdq_pbr_f = st.text_input("PBR (12M Fwd)", key="kdq_pbr_f", placeholder="예: 1.45")

            with col_k200:
                st.markdown("##### KOSPI 200")
                k200_per_c = st.text_input("PER (최근)", key="k200_per_c", placeholder="예: 10.80")
                k200_per_f = st.text_input("PER (12M Fwd)", key="k200_per_f", placeholder="예: 9.20")
                k200_pbr_c = st.text_input("PBR (최근)", key="k200_pbr_c", placeholder="예: 0.92")
                k200_pbr_f = st.text_input("PBR (12M Fwd)", key="k200_pbr_f", placeholder="예: 0.85")

            if st.button("📌 해당 일자 지수 데이터 저장", type="primary", key="btn_save_market"):
                cache = load_market_cache()
                cache[date_str] = {
                    "KOSPI_PER_최근": kpi_per_c.strip() or "-",
                    "KOSPI_PER_12M": kpi_per_f.strip() or "-",
                    "KOSPI_PBR_최근": kpi_pbr_c.strip() or "-",
                    "KOSPI_PBR_12M": kpi_pbr_f.strip() or "-",
                    "KOSDAQ_PER_최근": kdq_per_c.strip() or "-",
                    "KOSDAQ_PER_12M": kdq_per_f.strip() or "-",
                    "KOSDAQ_PBR_최근": kdq_pbr_c.strip() or "-",
                    "KOSDAQ_PBR_12M": kdq_pbr_f.strip() or "-",
                    "KOSPI200_PER_최근": k200_per_c.strip() or "-",
                    "KOSPI200_PER_12M": k200_per_f.strip() or "-",
                    "KOSPI200_PBR_최근": k200_pbr_c.strip() or "-",
                    "KOSPI200_PBR_12M": k200_pbr_f.strip() or "-",
                }
                save_market_cache(cache)
                st.success(f"{date_str} 지수 데이터가 성공적으로 저장되었습니다.")
                st.rerun()

        with t_restore:
            up_json = st.file_uploader("백업받은 market_indices_backup.json 업로드", type=["json"], key="json_backup_restore")
            if up_json is not None:
                if st.button("📥 백업 데이터 즉시 복원", type="primary", key="btn_restore_json"):
                    try:
                        content = json.load(up_json)
                        if isinstance(content, dict):
                            cache = load_market_cache()
                            cache.update(content)
                            save_market_cache(cache)
                            st.success(f"총 {len(content)}일자의 지수 데이터가 성공적으로 복원되었습니다.")
                            st.rerun()
                        else:
                            st.error("올바른 JSON 형식의 백업 파일이 아닙니다.")
                    except Exception as e:
                        st.error(f"복원 중 오류 발생: {e}")
