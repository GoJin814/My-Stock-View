import streamlit as st
import requests
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="종목Scan 대시보드", layout="wide")

SAVE_FILE = "saved_codes.txt"

# 1. 영구 저장된 종목코드 목록 읽기
def load_codes():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            codes = [line.strip().zfill(6) for line in f.readlines() if line.strip()]
            return list(dict.fromkeys(codes))
    return ["178320", "001130", "086450", "007690", "095660", "161890"]

# 2. 종목코드 영구 저장
def save_codes(codes):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        for c in codes:
            f.write(f"{c.strip().zfill(6)}\n")

# 3. 네이버 모바일 통합 정보 수집 (현재가, 시총, 실시간 PER/PBR, 배당수익률)
def get_naver_summary(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# 4. 네이버 모바일 연간 재무제표 전용 JSON API 수집
# (사용자 제공 URL: m.stock.naver.com/domestic/stock/{code}/finance/annual 의 원천 API)
def get_naver_annual_finance_api(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/finance/annual"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    
    fin_data = {
        "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan, 
        "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code != 200:
            return fin_data
            
        data = res.json()
        
        # 날짜 헤더 목록 (예: ['2021.12', '2022.12', '2023.12', '2024.12(E)'])
        date_list = data.get("dates", [])
        if not date_list:
            return fin_data
            
        # (E) 추정치가 없는 가장 최근 확정 결산 인덱스 선택
        actual_indices = [i for i, d in enumerate(date_list) if "(E)" not in str(d)]
        recent_idx = actual_indices[-1] if actual_indices else 0
        prev_idx = actual_indices[-2] if len(actual_indices) >= 2 else None
        
        # 재무 계정 테이블 리스트 탐색
        for table in data.get("tables", []):
            for row in table.get("rows", []):
                title = row.get("title", "").strip()
                values = row.get("values", [])
                
                def parse_val(idx):
                    if idx is not None and idx < len(values):
                        raw = str(values[idx]).replace(",", "").strip()
                        try:
                            return float(raw)
                        except:
                            return np.nan
                    return np.nan

                if "매출액" in title:
                    c_sales = parse_val(recent_idx)
                    p_sales = parse_val(prev_idx) if prev_idx is not None else np.nan
                    fin_data["매출액"] = c_sales
                    if pd.notna(c_sales) and pd.notna(p_sales) and p_sales != 0:
                        fin_data["매출YoY"] = round(((c_sales - p_sales) / abs(p_sales)) * 100, 2)
                        
                elif "영업이익" in title:
                    fin_data["영업이익"] = parse_val(recent_idx)
                elif "당기순이익" in title:
                    fin_data["당기순이익"] = parse_val(recent_idx)
                elif "주당배당금" in title or "DPS" in title:
                    fin_data["DPS"] = parse_val(recent_idx)
                elif "EPS" in title:
                    fin_data["EPS"] = parse_val(recent_idx)
                elif "BPS" in title:
                    fin_data["BPS"] = parse_val(recent_idx)
                    
    except Exception:
        pass
        
    return fin_data

# --- 대시보드 화면 렌더링 ---
st.title("📋 Scanning_주식 (모바일 뷰어)")
st.caption("네이버페이 증권 모바일 연간 재무 API 직접 연동")

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

# 2. 관리/삭제 아코디언
with st.expander("📌 등록된 종목 관리 / 개별 삭제", expanded=False):
    to_delete = st.multiselect("삭제할 종목 선택", current_codes)
    if st.button("선택 삭제"):
        if to_delete:
            current_codes = [c for c in current_codes if c not in to_delete]
            save_codes(current_codes)
            st.rerun()

# 3. 데이터 집계 및 표 렌더링
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권에서 최근 결산 재무 데이터를 가져오는 중..."):
        for code in current_codes:
            summary = get_naver_summary(code)
            if not summary or "stockName" not in summary:
                continue
                
            fin = get_naver_annual_finance_api(code)
            
            # 실시간 시세
            stock_name = summary.get("stockName", "-")
            curr_price = summary.get("dealTrendInfos", [{}])[0].get("closePrice", "0").replace(",", "")
            
            # totalInfos 파싱 (시가총액, PER, PBR, 배당수익률)
            total_dict = {item.get("key", "").strip(): item.get("value", "").strip() for item in summary.get("totalInfos", [])}
            
            market_cap = total_dict.get("시가총액", "-")
            div_yield = total_dict.get("배당수익률", "-")
            
            # 단위 중복("배배") 방지 처리: 이미 '배'가 있으면 그대로 사용
            def clean_ratio(val_str):
                if not val_str or val_str in ["-", "N/A"]:
                    return "-"
                val_str = val_str.replace("배", "").strip()
                return f"{val_str}배"

            per_val = clean_ratio(total_dict.get("PER", "-"))
            pbr_val = clean_ratio(total_dict.get("PBR", "-"))

            scan_results.append({
                "종목코드": code,
                "종목명": stock_name,
                "현재가": f"{int(curr_price):,}원" if curr_price.isdigit() else curr_price,
                "시총": market_cap,
                "매출액(억)": f"{fin['매출액']:,.0f}" if pd.notna(fin['매출액']) else "-",
                "매출 YoY": f"{fin['매출YoY']:+.1f}%" if pd.notna(fin['매출YoY']) else "-",
                "영업이익(억)": f"{fin['영업이익']:,.0f}" if pd.notna(fin['영업이익']) else "-",
                "당기순익(억)": f"{fin['당기순이익']:,.0f}" if pd.notna(fin['당기순이익']) else "-",
                "DPS(원)": f"{fin['DPS']:,.0f}" if pd.notna(fin['DPS']) else "-",
                "배당수익률": div_yield,
                "EPS(원)": f"{fin['EPS']:,.0f}" if pd.notna(fin['EPS']) else "-",
                "현재 PER": per_val,
                "BPS(원)": f"{fin['BPS']:,.0f}" if pd.notna(fin['BPS']) else "-",
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
