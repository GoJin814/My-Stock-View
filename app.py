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

# 2. 통합 정보 (/integration) - 시총 텍스트 원본 추출용
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

def to_num(val):
    if val is None or val in ["", "-", "N/A"]:
        return np.nan
    try:
        return float(str(val).replace(",", "").strip())
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

# 3. 테이블 데이터 집계
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권 데이터를 동기화하고 있습니다..."):
        for code in current_codes:
            basic = fetch_basic(code)
            integration = fetch_integration(code)
            fin_json = fetch_finance(code)
            
            # 종목명 및 현재가 (/basic)
            stock_name = basic.get("stockName", "-")
            raw_close = basic.get("closePrice", "-")
            curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)
            
            # 시가총액 추출: code="marketValue" 또는 key="시총" 매핑
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

            # PER / PBR / 배당수익률
            raw_per = basic.get("per", integration_dict.get("PER", "-"))
            raw_pbr = basic.get("pbr", integration_dict.get("PBR", "-"))
            raw_div = basic.get("dividendYield", integration_dict.get("배당수익률", "-"))
            
            per_val = f"{str(raw_per).replace('배', '')}배" if raw_per not in ["-", "N/A", None] else "-"
            pbr_val = f"{str(raw_pbr).replace('배', '')}배" if raw_pbr not in ["-", "N/A", None] else "-"
            div_val = f"{raw_div}%" if (raw_div not in ["-", "N/A", None] and "%" not in str(raw_div)) else str(raw_div)

            # --- [연간 재무제표 rowList 파싱: 정확한 타이틀 일치 적용] ---
            fin_data = {
                "기준연도": "-",
                "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan,
                "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan
            }
            
            row_list = fin_json.get("rowList", [])
            if not row_list and isinstance(fin_json, dict):
                for val in fin_json.values():
                    if isinstance(val, dict) and "rowList" in val:
                        row_list = val.get("rowList", [])
                        break

            if row_list:
                for row in row_list:
                    raw_title = row.get("title", "").strip()
                    columns = row.get("columns", {})
                    if not columns:
                        continue
                        
                    sorted_years = sorted(list(columns.keys()))
                    if not sorted_years:
                        continue
                        
                    latest_yr = sorted_years[-1]
                    prev_yr = sorted_years[-2] if len(sorted_years) >= 2 else None
                    
                    fin_data["기준연도"] = f"{latest_yr[:4]}년"
                    
                    latest_item = columns.get(latest_yr, {})
                    latest_val_str = latest_item.get("value") if isinstance(latest_item, dict) else latest_item
                    cur_v = to_num(latest_val_str)
                    
                    prev_item = columns.get(prev_yr, {}) if prev_yr else {}
                    prev_val_str = prev_item.get("value") if isinstance(prev_item, dict) else prev_item
                    prev_v = to_num(prev_val_str)

                    # 완전 일치(==)로 영업이익률 등 다른 항목의 오버라이트 방지
                    if raw_title in ["매출액", "수익"]:
                        fin_data["매출액"] = cur_v
                        if pd.notna(cur_v) and pd.notna(prev_v) and prev_v != 0:
                            fin_data["매출YoY"] = round(((cur_v - prev_v) / abs(prev_v)) * 100, 2)
                    elif raw_title == "영업이익":
                        fin_data["영업이익"] = cur_v
                    elif raw_title in ["당기순이익", "당기순익"]:
                        fin_data["당기순이익"] = cur_v
                    elif raw_title in ["주당배당금(원)", "주당배당금", "DPS"]:
                        fin_data["DPS"] = cur_v
                    elif raw_title in ["수정주당순이익(원)", "주당순이익(원)", "EPS"]:
                        fin_data["EPS"] = cur_v
                    elif raw_title in ["주당순자산(원)", "주당순자산가치(원)", "BPS"]:
                        fin_data["BPS"] = cur_v

            scan_results.append({
                "종목코드": code,
                "종목명": stock_name,
                "현재가": curr_price_str,
                "시총": market_cap,
                "기준실적": fin_data["기준연도"],
                "매출액(억)": f"{fin_data['매출액']:,.0f}억" if pd.notna(fin_data['매출액']) else "-",
                "매출 YoY": f"{fin_data['매출YoY']:+.1f}%" if pd.notna(fin_data['매출YoY']) else "-",
                "영업이익(억)": f"{fin_data['영업이익']:,.0f}억" if pd.notna(fin_data['영업이익']) else "-",
                "당기순익(억)": f"{fin_data['당기순이익']:,.0f}억" if pd.notna(fin_data['당기순이익']) else "-",
                "DPS(원)": f"{fin_data['DPS']:,.0f}원" if pd.notna(fin_data['DPS']) else "-",
                "배당수익률": div_val,
                "EPS(원)": f"{fin_data['EPS']:,.0f}원" if pd.notna(fin_data['EPS']) else "-",
                "현재 PER": per_val,
                "BPS(원)": f"{fin_data['BPS']:,.0f}원" if pd.notna(fin_data['BPS']) else "-",
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
