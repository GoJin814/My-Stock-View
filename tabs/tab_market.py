import streamlit as st
import pandas as pd
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

MARKET_CACHE_FILE = "market_indices_cache.json"

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://finance.naver.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def parse_index_detail(index_code: str):
    """네이버 증권 지수 상세 페이지에서 PER, PBR 크롤링"""
    url = f"https://finance.naver.com/sise/sise_index.naver?code={index_code}"
    result = {"PER_최근": "-", "PER_12M": "-", "PBR_최근": "-", "PBR_12M": "-"}
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for tr in soup.find_all("tr"):
                th = tr.find("th")
                td = tr.find("td")
                if not th or not td:
                    continue
                text_th = th.get_text().strip()
                text_td = td.get_text().strip()
                
                if "PER" in text_th:
                    if "추정" in text_th or "12M" in text_th or "Fwd" in text_th:
                        result["PER_12M"] = text_td.replace("배", "").strip()
                    else:
                        result["PER_최근"] = text_td.replace("배", "").strip()
                elif "PBR" in text_th:
                    if "추정" in text_th or "12M" in text_th or "Fwd" in text_th:
                        result["PBR_12M"] = text_td.replace("배", "").strip()
                    else:
                        result["PBR_최근"] = text_td.replace("배", "").strip()
    except Exception:
        pass
    return result

def fetch_market_indices():
    """KOSPI, KOSDAQ, KPI200 전체 자동 스크래핑"""
    kpi = parse_index_detail("KOSPI")
    kdq = parse_index_detail("KOSDAQ")
    k200 = parse_index_detail("KPI200")
    
    return {
        "KOSPI_PER_최근": kpi["PER_최근"], "KOSPI_PER_12M": kpi["PER_12M"],
        "KOSPI_PBR_최근": kpi["PBR_최근"], "KOSPI_PBR_12M": kpi["PBR_12M"],
        "KOSDAQ_PER_최근": kdq["PER_최근"], "KOSDAQ_PER_12M": kdq["PER_12M"],
        "KOSDAQ_PBR_최근": kdq["PBR_최근"], "KOSDAQ_PBR_12M": kdq["PBR_12M"],
        "KOSPI200_PER_최근": k200["PER_최근"], "KOSPI200_PER_12M": k200["PER_12M"],
        "KOSPI200_PBR_최근": k200["PBR_최근"], "KOSPI200_PBR_12M": k200["PBR_12M"],
    }

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

    # 상단 자동 수집 버튼
    btn_c1, _ = st.columns([2, 4])
    with btn_c1:
        if st.button("⚡ 오늘 지수 데이터 자동 불러오기", type="primary", use_container_width=True):
            today_str = datetime.today().strftime('%Y-%m-%d')
            with st.spinner("네이버 증권에서 오늘 지수 데이터를 불러오는 중..."):
                latest_data = fetch_market_indices()
                if today_str not in m_cache:
                    m_cache[today_str] = {}
                m_cache[today_str].update(latest_data)
                save_market_cache(m_cache)
                st.success(f"{today_str} 지수 밸류에이션 데이터가 자동 등록되었습니다!")
                st.rerun()

    if not m_cache:
        st.info("기록된 국내지수 데이터가 없습니다. 상단 '오늘 지수 데이터 자동 불러오기' 버튼을 누르거나 아래에서 CSV/Excel 파일을 업로드해 주세요.")
        return None

    # 최신 날짜순 정렬
    sorted_dates = sorted(list(m_cache.keys()), reverse=True)
    records = []
    for d in sorted_dates:
        row = {"선택": False, "일시": d}
        row.update(m_cache[d])
        records.append(row)

    df_market = pd.DataFrame(records)

    macro_cols = ["KOSPI", "시가총액(억원)", "고객예탁금(억원)", "신용잔고(억원)", "환율"]
    has_macro = any(col in df_market.columns for col in macro_cols)

    macro_header_html = ""
    macro_sub_header_html = ""
    if has_macro:
        macro_header_html = '<th colspan="5" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px; background-color: var(--secondary-background-color, #f0f2f6);">시장 매크로 지표</th>'
        macro_sub_header_html = """
            <th rowspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">KOSPI지수</th>
            <th rowspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">시가총액(억)</th>
            <th rowspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">고객예탁금(억)</th>
            <th rowspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">신용잔고(억)</th>
            <th rowspan="2" style="border: 1px solid rgba(128,128,128,0.3); padding: 4px;">환율(원)</th>
        """

    st.markdown(f"""
        <div style="overflow-x: auto; margin-bottom: 1rem;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem; text-align: center;">
            <thead>
                <tr style="background-color: var(--secondary-background-color, #f0f2f6);">
                    <th rowspan="3" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">선택</th>
                    <th rowspan="3" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">일시</th>
                    {macro_header_html}
                    <th colspan="4" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">KOSPI</th>
                    <th colspan="4" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">KOSDAQ</th>
                    <th colspan="4" style="border: 1px solid rgba(128,128,128,0.3); padding: 6px;">KOSPI200</th>
                </tr>
                <tr style="background-color: var(--secondary-background-color, #f0f2f6);">
                    {macro_sub_header_html}
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
    with st.expander("🌐 국내지수 데이터 파일 업로드(CSV / Excel) 및 수기 등록", expanded=False):
        t_upload, t_manual, t_restore = st.tabs(["📊 CSV / Excel 파일 일괄 업로드", "✍️ 개별 수기 입력", "📂 백업 파일(JSON) 복원"])

        with t_upload:
            st.write("보유하고 계신 **CSV 또는 Excel(.xlsx)** 파일을 업로드하면 날짜별 데이터가 자동으로 병합/추가됩니다.")
            market_file = st.file_uploader(
                "지수 데이터 파일 선택 (일시, KOSPI, 시가총액, PER, PBR 등)",
                type=["csv", "xlsx", "xls"],
                key="market_csv_excel_uploader"
            )
            if market_file is not None:
                if st.button("📥 파일 데이터 읽어서 추가하기", type="primary", key="btn_apply_market_file"):
                    try:
                        if market_file.name.endswith(".csv"):
                            try:
                                df_up = pd.read_csv(market_file, encoding="utf-8")
                            except UnicodeDecodeError:
                                market_file.seek(0)
                                df_up = pd.read_csv(market_file, encoding="cp949")
                        else:
                            df_up = pd.read_excel(market_file)

                        df_up.columns = [str(c).replace(" ", "").strip() for c in df_up.columns]

                        date_col = None
                        for c in df_up.columns:
                            if any(k in c for k in ["일시", "날짜", "Date", "DATE"]):
                                date_col = c
                                break

                        if not date_col:
                            st.error("파일에서 '일시' 또는 '날짜' 컬럼을 찾을 수 없습니다.")
                        else:
                            cache = load_market_cache()
                            added_count = 0

                            for _, r in df_up.iterrows():
                                raw_d = str(r[date_col]).strip()
                                d_str = normalize_date(raw_d)
                                if not d_str:
                                    continue

                                if d_str not in cache:
                                    cache[d_str] = {}

                                for col in df_up.columns:
                                    if col == date_col:
                                        continue
                                    val_str = str(r[col]).strip()
                                    if val_str in ["nan", "None", ""]:
                                        val_str = "-"

                                    if "시가총액" in col:
                                        cache[d_str]["시가총액(억원)"] = val_str
                                    elif "고객예탁금" in col or "예탁금" in col:
                                        cache[d_str]["고객예탁금(억원)"] = val_str
                                    elif "신용잔고" in col or "신용융자" in col:
                                        cache[d_str]["신용잔고(억원)"] = val_str
                                    elif "환율" in col:
                                        cache[d_str]["환율"] = val_str
                                    elif col == "PER":
                                        cache[d_str]["KOSPI_PER_최근"] = val_str
                                    elif col == "PBR":
                                        cache[d_str]["KOSPI_PBR_최근"] = val_str
                                    elif col in ["KOSPI", "코스피"]:
                                        cache[d_str]["KOSPI"] = val_str
                                    else:
                                        cache[d_str][col] = val_str

                                added_count += 1

                            save_market_cache(cache)
                            st.success(f"총 {added_count}개 일자의 지수 데이터가 성공적으로 반영되었습니다!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")

        with t_manual:
            c_date, _ = st.columns([2, 4])
            with c_date:
                input_date = st.date_input("기준 일자", key="market_input_date")
            date_str = str(input_date)

            col_kpi, col_kdq, col_k200 = st.columns(3)
            with col_kpi:
                st.markdown("##### KOSPI")
                kpi_per_c = st.text_input("PER (최근)", key="kpi_per_c", placeholder="예: 18.19")
                kpi_per_f = st.text_input("PER (12M Fwd)", key="kpi_per_f", placeholder="예: 9.85")
                kpi_pbr_c = st.text_input("PBR (최근)", key="kpi_pbr_c", placeholder="예: 1.90")
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

            if st.button("📌 수기 데이터 저장", type="primary", key="btn_save_market"):
                cache = load_market_cache()
                if date_str not in cache:
                    cache[date_str] = {}
                cache[date_str].update({
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
                })
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
