import streamlit as st
import requests
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="종목Scan 대시보드", layout="wide")

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

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Referer": "https://m.stock.naver.com/",
    "Accept": "application/json, text/plain, */*"
}

# 1. 실시간 시세 및 밸류에이션 (/basic)
def fetch_basic(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

# 2. 통합 정보 (/integration)
def fetch_integration(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

# 3. 연간 재무제표 (/finance/annual)
def fetch_finance(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/finance/annual"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def to_clean_float(val):
    if val is None or val in ["", "-", "N/A"]:
        return np.nan
    try:
        return float(str(val).replace(",", "").replace("배", "").replace("%", "").strip())
    except:
        return np.nan

# --- 화면 렌더링 ---
st.title("📋 Scanning_주식 (모바일 뷰어)")
st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 실시간 연동")

current_codes = load_codes()

# 1. 종목 추가 영역
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

# 2. 종목 관리 및 삭제
with st.expander("📌 등록된 종목 관리 / 개별 삭제", expanded=False):
    to_delete = st.multiselect("삭제할 종목 선택", current_codes)
    if st.button("선택 삭제"):
        if to_delete:
            current_codes = [c for c in current_codes if c not in to_delete]
            save_codes(current_codes)
            st.rerun()

# 3. 데이터 집계
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권 데이터를 동기화하고 있습니다..."):
        for code in current_codes:
            basic = fetch_basic(code)
            integration = fetch_integration(code)
            fin_json = fetch_finance(code)
            
            stock_name = basic.get("stockName", "-")
            
            # 1) 현재가: 순수 정수형 숫자 추출
            raw_close = basic.get("closePrice")
            curr_price = to_clean_float(raw_close)
            
            # 2) 시총: 1억 미만 반올림된 순수 숫자(억원 단위)
            raw_mv = basic.get("marketValue")
            if raw_mv and str(raw_mv).isdigit():
                market_cap_eok = round(float(raw_mv) / 100000000)
            else:
                market_cap_eok = np.nan
                
            # 3) 지표: 순수 float 추출
            total_infos = integration.get("totalInfos", [])
            integration_dict = {str(item.get("key", "")).strip(): item.get("value") for item in total_infos}
            
            per_val = to_clean_float(basic.get("per", integration_dict.get("PER")))
            pbr_val = to_clean_float(basic.get("pbr", integration_dict.get("PBR")))
            div_val = to_clean_float(basic.get("dividendYield", integration_dict.get("배당수익률")))

            # 4) 연간 재무제표: 순수 float 추출
            fin_data = {
                "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan,
                "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan
            }
            
            data_obj = fin_json.get("data", fin_json) if isinstance(fin_json, dict) else {}
            dates = data_obj.get("dates", [])
            tables = data_obj.get("tables", [])
            
            if dates and tables:
                actual_indices = [i for i, d in enumerate(dates) if "(E)" not in str(d)]
                rec_idx = actual_indices[-1] if actual_indices else (len(dates) - 1)
                prev_idx = actual_indices[-2] if len(actual_indices) >= 2 else None
                
                for t in tables:
                    for r in t.get("rows", []):
                        title = r.get("title", "").strip()
                        vals = r.get("values", [])
                        if not vals:
                            continue
                            
                        cur_v = to_clean_float(vals[rec_idx]) if rec_idx < len(vals) else np.nan
                        prev_v = to_clean_float(vals[prev_idx]) if (prev_idx is not None and prev_idx < len(vals)) else np.nan
                        
                        if "매출액" in title:
                            fin_data["매출액"] = cur_v
                            if pd.notna(cur_v) and pd.notna(prev_v) and prev_v != 0:
                                fin_data["매출YoY"] = round(((cur_v - prev_v) / abs(prev_v)) * 100, 2)
                        elif "영업이익" in title:
                            fin_data["영업이익"] = cur_v
                        elif "당기순이익" in title:
                            fin_data["당기순이익"] = cur_v
                        elif "주당배당금" in title or "DPS" in title:
                            fin_data["DPS"] = cur_v
                        elif "EPS" in title:
                            fin_data["EPS"] = cur_v
                        elif "BPS" in title:
                            fin_data["BPS"] = cur_v

            scan_results.append({
                "종목코드": code,
                "종목명": stock_name,
                "현재가": curr_price,
                "시총(억)": market_cap_eok,
                "매출액(억)": fin_data["매출액"],
                "매출 YoY": fin_data["매출YoY"],
                "영업이익(억)": fin_data["영업이익"],
                "당기순익(억)": fin_data["당기순이익"],
                "DPS": fin_data["DPS"],
                "배당수익률": div_val,
                "EPS": fin_data["EPS"],
                "현재 PER": per_val,
                "BPS": fin_data["BPS"],
                "현재 PBR": pbr_val
            })

    if scan_results:
        result_df = pd.DataFrame(scan_results)
        
        # 순수 숫자로 저장된 데이터에 화면 표시용 포맷팅 적용
        st.dataframe(
            result_df,
            column_config={
                "종목코드": st.column_config.TextColumn("종목코드"),
                "종목명": st.column_config.TextColumn("종목명"),
                "현재가": st.column_config.NumberColumn("현재가", format="%,d원"),
                "시총(억)": st.column_config.NumberColumn("시총(억)", format="%,d억"),
                "매출액(억)": st.column_config.NumberColumn("매출액(억)", format="%,d억"),
                "매출 YoY": st.column_config.NumberColumn("매출 YoY", format="%+.1f%%"),
                "영업이익(억)": st.column_config.NumberColumn("영업이익(억)", format="%,d억"),
                "당기순익(억)": st.column_config.NumberColumn("당기순익(억)", format="%,d억"),
                "DPS": st.column_config.NumberColumn("DPS(원)", format="%,d원"),
                "배당수익률": st.column_config.NumberColumn("배당수익률", format="%.2f%%"),
                "EPS": st.column_config.NumberColumn("EPS(원)", format="%,d원"),
                "현재 PER": st.column_config.NumberColumn("현재 PER", format="%.2f배"),
                "BPS": st.column_config.NumberColumn("BPS(원)", format="%,d원"),
                "현재 PBR": st.column_config.NumberColumn("현재 PBR", format="%.2f배"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 조회 결과 CSV 다운로드",
            data=csv,
            file_name="종목Scan_결과.csv",
            mime="text/csv"
        )
else:
    st.info("등록된 종목이 없습니다. 상단에서 종목코드를 추가해 주세요.")
