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

# 1. 네이버 모바일 통합 정보 수집 (현재가, 시총, PER, PBR, 배당수익률 등)
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

# 2. 네이버 기업정보 재무제표 원본 테이블 수집 (가장 확실한 HTML 방식 - 블록 우회 헤더 적용)
def get_naver_financials_direct(code: str):
    fin_data = {
        "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan, 
        "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan
    }
    
    # 네이버페이 증권이 Financial Highlight를 가져오는 WiseReport 프레임 주소
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://navercomp.wisereport.co.kr/"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=7)
        if resp.status_code == 200:
            tables = pd.read_html(resp.text)
            
            # 11~14번째 인근 또는 '주요재무정보'가 포함된 테이블 탐색
            target_df = None
            for t in tables:
                col_text = " ".join([str(c) for c in t.columns.values])
                if "주요재무정보" in col_text or "매출액" in t.to_string():
                    target_df = t
                    break
                    
            if target_df is not None:
                # 2단 헤더를 평탄화 (예: 2023/12, 2024/12 등)
                if isinstance(target_df.columns, pd.MultiIndex):
                    target_df.columns = [f"{c[1]}" if c[1] else str(c[0]) for c in target_df.columns]
                
                # 첫 번째 열을 계정과목 열로 지정
                item_col = target_df.columns[0]
                
                # 연간 실적 컬럼 찾기 (보통 앞쪽 4~5개 컬럼이 연간 실적)
                date_cols = [c for c in target_df.columns[1:] if ("20" in str(c) or "/12" in str(c))]
                
                # (E) 추정치가 안 붙은 가장 최근 확정 결산 컬럼
                actual_cols = [c for c in date_cols if "(E)" not in str(c)]
                
                recent_col = actual_cols[-1] if actual_cols else (date_cols[0] if date_cols else None)
                prev_col = actual_cols[-2] if len(actual_cols) >= 2 else None

                if recent_col:
                    def parse_row(name):
                        for _, row in target_df.iterrows():
                            title = str(row[item_col]).strip()
                            if name in title:
                                val_str = str(row[recent_col]).replace(",", "").strip()
                                try:
                                    return float(val_str)
                                except:
                                    return np.nan
                        return np.nan

                    def parse_prev(name):
                        if not prev_col:
                            return np.nan
                        for _, row in target_df.iterrows():
                            title = str(row[item_col]).strip()
                            if name in title:
                                val_str = str(row[prev_col]).replace(",", "").strip()
                                try:
                                    return float(val_str)
                                except:
                                    return np.nan
                        return np.nan

                    c_sales = parse_row("매출액")
                    p_sales = parse_prev("매출액")
                    
                    fin_data["매출액"] = c_sales
                    if pd.notna(c_sales) and pd.notna(p_sales) and p_sales != 0:
                        fin_data["매출YoY"] = round(((c_sales - p_sales) / abs(p_sales)) * 100, 2)
                        
                    fin_data["영업이익"] = parse_row("영업이익")
                    fin_data["당기순이익"] = parse_row("당기순이익")
                    fin_data["DPS"] = parse_row("주당배당금")
                    fin_data["EPS"] = parse_row("EPS")
                    fin_data["BPS"] = parse_row("BPS")
    except Exception:
        pass
        
    return fin_data

# --- UI 화면 ---
st.title("📋 Scanning_주식 (모바일 뷰어)")
st.caption("네이버페이 증권 데이터 기반 실시간 자동 파싱 시스템")

current_codes = load_codes()

# 1. 새 종목 추가 영역
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

# 2. 관리/삭제
with st.expander("📌 등록된 종목 관리 / 개별 삭제", expanded=False):
    to_delete = st.multiselect("삭제할 종목 선택", current_codes)
    if st.button("선택 삭제"):
        if to_delete:
            current_codes = [c for c in current_codes if c not in to_delete]
            save_codes(current_codes)
            st.rerun()

# 3. 데이터 집계 및 테이블 출력
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권에서 재무제표와 실시간 시세를 수집하는 중..."):
        for code in current_codes:
            summary = get_naver_summary(code)
            if not summary or "stockName" not in summary:
                continue
                
            fin = get_naver_financials_direct(code)
            
            # 실시간 시세
            stock_name = summary.get("stockName", "-")
            curr_price = summary.get("dealTrendInfos", [{}])[0].get("closePrice", "0").replace(",", "")
            
            # totalInfos에서 모든 키-값 추출 (키워드 매칭으로 시가총액 안전하게 추출)
            market_cap = "-"
            per_val = "-"
            pbr_val = "-"
            div_yield = "-"
            
            for item in summary.get("totalInfos", []):
                k = item.get("key", "").strip()
                v = item.get("value", "").strip()
                
                if "시가총액" in k:
                    market_cap = v
                elif k == "PER":
                    per_val = f"{v.replace('배', '').strip()}배" if v not in ["-", "N/A"] else "-"
                elif k == "PBR":
                    pbr_val = f"{v.replace('배', '').strip()}배" if v not in ["-", "N/A"] else "-"
                elif "배당수익률" in k:
                    div_yield = v

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
