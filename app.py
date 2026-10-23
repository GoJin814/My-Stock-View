import streamlit as st
import requests
import pandas as pd
import numpy as np
import os
import re

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

# 1. 네이버 모바일 기본 시세 및 밸류에이션 지표 수집
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

# 2. 네이버 금융 기업 실적분석 테이블 직접 파싱 (PC 버전)
def get_naver_finance_pc(code: str):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    fin_data = {
        "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan, 
        "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan,
        "PER": "-", "PBR": "-", "시총": "-"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return fin_data
            
        tables = pd.read_html(resp.text, encoding="euc-kr")
        
        # 1) 기업실적분석 테이블 찾기
        fin_df = None
        for t in tables:
            first_col_str = str(t.columns[0])
            if "주요재무정보" in first_col_str or "매출액" in str(t.iloc[:, 0].values):
                fin_df = t
                break
                
        if fin_df is not None:
            # MultiIndex 컬럼 평탄화 (최근 연간 실적 영역 추출)
            # 네이버 재무제표는 상위 컬럼이 '최근 연간 실적', '최근 분기 실적'으로 나뉨
            if isinstance(fin_df.columns, pd.MultiIndex):
                # 최근 연간 실적에 해당하는 컬럼만 필터링
                annual_cols = [c for c in fin_df.columns if "연간" in str(c[0])]
                
                if annual_cols:
                    # 추정치 (E) 제외한 가장 최근 확정 연도 찾기
                    actual_cols = [c for c in annual_cols if "(E)" not in str(c[1])]
                    recent_col = actual_cols[-1] if actual_cols else annual_cols[0]
                    prev_col = actual_cols[-2] if len(actual_cols) >= 2 else None
                    
                    first_col = fin_df.columns[0]
                    
                    def extract_num(row_keyword, target_col):
                        for idx, row in fin_df.iterrows():
                            val_name = str(row[first_col])
                            if row_keyword in val_name:
                                raw_val = str(row[target_col]).replace(",", "").strip()
                                try:
                                    return float(raw_val)
                                except:
                                    return np.nan
                        return np.nan

                    c_sales = extract_num("매출액", recent_col)
                    p_sales = extract_num("매출액", prev_col) if prev_col else np.nan
                    
                    fin_data["매출액"] = c_sales
                    if pd.notna(c_sales) and pd.notna(p_sales) and p_sales != 0:
                        fin_data["매출YoY"] = round(((c_sales - p_sales) / abs(p_sales)) * 100, 2)
                        
                    fin_data["영업이익"] = extract_num("영업이익", recent_col)
                    fin_data["당기순이익"] = extract_num("당기순이익", recent_col)
                    fin_data["DPS"] = extract_num("주당배당금", recent_col)
                    fin_data["EPS"] = extract_num("EPS", recent_col)
                    fin_data["BPS"] = extract_num("BPS", recent_col)
                    
                    # 최근 결산 기준 확정 PER / PBR
                    c_per = extract_num("PER", recent_col)
                    c_pbr = extract_num("PBR", recent_col)
                    if pd.notna(c_per):
                        fin_data["PER"] = f"{c_per:.2f}배"
                    if pd.notna(c_pbr):
                        fin_data["PBR"] = f"{c_pbr:.2f}배"
    except Exception:
        pass
        
    return fin_data

# --- 대시보드 화면 구성 ---
st.title("📋 Scanning_주식 (모바일 뷰어)")
st.caption("네이버페이 증권 공식 데이터 연동 시스템")

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

# 3. 데이터 수집 및 표 렌더링
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권에서 재무제표와 시세를 집계하고 있습니다..."):
        for code in current_codes:
            summary = get_naver_summary(code)
            if not summary or "stockName" not in summary:
                continue
                
            fin = get_naver_finance_pc(code)
            
            # 기본 시세
            stock_name = summary.get("stockName", "-")
            curr_price = summary.get("dealTrendInfos", [{}])[0].get("closePrice", "0").replace(",", "")
            
            # 모바일 API 내 totalInfos를 딕셔너리로 추출
            total_dict = {}
            for item in summary.get("totalInfos", []):
                k = item.get("key", "").strip()
                v = item.get("value", "").strip()
                total_dict[k] = v
                
            # 시총 파싱 (모바일 summary 우선, 없으면 fallback)
            market_cap = total_dict.get("시가총액", "-")
            
            # PER / PBR 파싱: 재무제표 테이블 값 우선, 없으면 모바일 API 값 적용
            per_val = fin["PER"] if fin["PER"] != "-" else total_dict.get("PER", "-")
            pbr_val = fin["PBR"] if fin["PBR"] != "-" else total_dict.get("PBR", "-")
            div_yield = total_dict.get("배당수익률", "-")
            
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
