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

# 2. 연간 재무제표 (/finance/annual)
def fetch_finance(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/finance/annual"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def to_num(val):
    if val is None or val in ["", "-", "N/A"]:
        return np.nan
    try:
        return float(str(val).replace(",", "").strip())
    except:
        return np.nan

# --- 화면 구성 ---
st.title("📋 Scanning_주식 (모바일 뷰어)")
st.caption("네이버 증권 공식 모바일 API (/basic, /finance/annual) 실시간 연동")

current_codes = load_codes()

# 종목 추가
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

# 관리/삭제
with st.expander("📌 등록된 종목 관리 / 개별 삭제", expanded=False):
    to_delete = st.multiselect("삭제할 종목 선택", current_codes)
    if st.button("선택 삭제"):
        if to_delete:
            current_codes = [c for c in current_codes if c not in to_delete]
            save_codes(current_codes)
            st.rerun()

# 데이터 수집 및 표 생성
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권 데이터를 동기화하고 있습니다..."):
        for code in current_codes:
            basic = fetch_basic(code)
            fin_json = fetch_finance(code)
            
            # 1) /basic 데이터 파싱
            stock_name = basic.get("stockName", "-")
            
            # 말씀해주신 closePrice 필드 직접 타겟팅
            raw_close = basic.get("closePrice", "-")
            if raw_close != "-":
                curr_price_str = f"{raw_close}원" if "원" not in str(raw_close) else str(raw_close)
            else:
                curr_price_str = "-"
                
            # 시총 (marketValue는 원 단위 숫자로 들어오므로 억원 단위 환산)
            market_cap_raw = basic.get("marketValue", "-")
            if market_cap_raw != "-" and str(market_cap_raw).isdigit():
                market_cap = f"{int(market_cap_raw) // 100000000:,}억"
            else:
                market_cap = str(market_cap_raw)
            
            # PER / PBR / 배당수익률
            raw_per = basic.get("per", "-")
            raw_pbr = basic.get("pbr", "-")
            raw_div = basic.get("dividendYield", "-")
            
            per_val = f"{raw_per}배" if (raw_per not in ["-", "N/A", None]) else "-"
            pbr_val = f"{raw_pbr}배" if (raw_pbr not in ["-", "N/A", None]) else "-"
            div_val = f"{raw_div}%" if (raw_div not in ["-", "N/A", None] and "%" not in str(raw_div)) else str(raw_div)

            # 2) /finance/annual 재무제표 파싱
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
                            
                        cur_v = to_num(vals[rec_idx]) if rec_idx < len(vals) else np.nan
                        prev_v = to_num(vals[prev_idx]) if (prev_idx is not None and prev_idx < len(vals)) else np.nan
                        
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
                "현재가": curr_price_str,
                "시총": market_cap,
                "매출액(억)": f"{fin_data['매출액']:,.0f}" if pd.notna(fin_data['매출액']) else "-",
                "매출 YoY": f"{fin_data['매출YoY']:+.1f}%" if pd.notna(fin_data['매출YoY']) else "-",
                "영업이익(억)": f"{fin_data['영업이익']:,.0f}" if pd.notna(fin_data['영업이익']) else "-",
                "당기순익(억)": f"{fin_data['당기순이익']:,.0f}" if pd.notna(fin_data['당기순이익']) else "-",
                "DPS(원)": f"{fin_data['DPS']:,.0f}" if pd.notna(fin_data['DPS']) else "-",
                "배당수익률": div_val,
                "EPS(원)": f"{fin_data['EPS']:,.0f}" if pd.notna(fin_data['EPS']) else "-",
                "현재 PER": per_val,
                "BPS(원)": f"{fin_data['BPS']:,.0f}" if pd.notna(fin_data['BPS']) else "-",
                "현재 PBR": pbr_val
            })

    if scan_results:
        result_df = pd.DataFrame(scan_results)
        st.dataframe(result_df, use_container_width=True, hide_index=True)
        
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 조회 결과 CSV 다운로드",
            data=csv,
            file_name="종목Scan_결과.csv",
            mime="text/csv"
        )
else:
    st.info("등록된 종목이 없습니다. 상단에서 종목코드를 추가해 주세요.")
