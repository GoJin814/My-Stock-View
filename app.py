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

# 3. 네이버 모바일 통합 정보 수집 (실시간 시세, 시가총액, 배당수익률, 외국인소진율)
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

# 4. 네이버 기업정보(Financial Highlight) 원본 재무제표 수집
def get_naver_company_financials(code: str):
    # 네이버 기업정보 페이지가 실제로 재무 테이블을 불러오는 원본 주소
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://stock.naver.com/domestic/stock/{code}/info/company"
    }
    
    fin_data = {
        "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan, 
        "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan,
        "PER": "-", "PBR": "-"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return fin_data
            
        tables = pd.read_html(resp.text, encoding="utf-8")
        target_df = None
        
        # Financial Highlight 테이블 탐색
        for df in tables:
            first_col_str = str(df.columns[0])
            if "주요재무정보" in first_col_str or "Financial" in first_col_str:
                target_df = df
                break
                
        if target_df is not None:
            # MultiIndex 평탄화 (2021/12, 2022/12, 2023/12 등 연간 결산 헤더 추출)
            if isinstance(target_df.columns, pd.MultiIndex):
                target_df.columns = [f"{c[1]}_{c[2]}" if c[2] else str(c[1]) for c in target_df.columns]
            
            first_col_name = target_df.columns[0]
            
            # 연간 결산 컬럼 선별 (분기 제외, 연간 결산만 추출)
            year_cols = []
            for c in target_df.columns[1:]:
                c_str = str(c)
                if ("/12" in c_str or "결산" in c_str or "20" in c_str) and ("/03" not in c_str and "/06" not in c_str and "/09" not in c_str):
                    year_cols.append(c)
            
            # (E) 추정치가 없는 가장 최근 확정 실적 컬럼 찾기
            actual_cols = [c for c in year_cols if "(E)" not in str(c)]
            
            recent_col = actual_cols[-1] if len(actual_cols) > 0 else (year_cols[0] if len(year_cols) > 0 else None)
            prev_col = actual_cols[-2] if len(actual_cols) >= 2 else None

            if recent_col:
                def get_val(keyword, target_col):
                    for idx, row in target_df.iterrows():
                        name = str(row[first_col_name]).strip()
                        if keyword in name:
                            raw = str(row[target_col]).replace(",", "").strip()
                            try:
                                return float(raw)
                            except:
                                return np.nan
                    return np.nan

                c_sales = get_val("매출액", recent_col)
                p_sales = get_val("매출액", prev_col) if prev_col else np.nan
                
                fin_data["매출액"] = c_sales
                if pd.notna(c_sales) and pd.notna(p_sales) and p_sales != 0:
                    fin_data["매출YoY"] = round(((c_sales - p_sales) / abs(p_sales)) * 100, 2)
                    
                fin_data["영업이익"] = get_val("영업이익", recent_col)
                fin_data["당기순이익"] = get_val("당기순이익", recent_col)
                fin_data["DPS"] = get_val("주당배당금", recent_col)
                fin_data["EPS"] = get_val("EPS", recent_col)
                fin_data["BPS"] = get_val("BPS", recent_col)
                
                c_per = get_val("PER", recent_col)
                c_pbr = get_val("PBR", recent_col)
                if pd.notna(c_per):
                    fin_data["PER"] = f"{c_per:.2f}배"
                if pd.notna(c_pbr):
                    fin_data["PBR"] = f"{c_pbr:.2f}배"
    except Exception:
        pass
        
    return fin_data

# --- 화면 렌더링 ---
st.title("📋 Scanning_주식 (네이버 증권 기업정보 연동)")
st.caption("https://stock.naver.com/domestic/stock/{code}/info/company 실시간 파싱")

current_codes = load_codes()

# 1. 종목 추가
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

# 3. 데이터 집계 및 테이블 렌더링
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권 기업정보에서 최근 결산 재무 데이터를 가져오는 중..."):
        for code in current_codes:
            summary = get_naver_summary(code)
            if not summary or "stockName" not in summary:
                continue
                
            fin = get_naver_company_financials(code)
            
            # 실시간 시세
            stock_name = summary.get("stockName", "-")
            curr_price = summary.get("dealTrendInfos", [{}])[0].get("closePrice", "0").replace(",", "")
            
            # totalInfos 파싱 (시가총액, 배당수익률, 폴백 PER/PBR)
            total_dict = {item.get("key", "").strip(): item.get("value", "").strip() for item in summary.get("totalInfos", [])}
            
            market_cap = total_dict.get("시가총액", "-")
            div_yield = total_dict.get("배당수익률", "-")
            
            # 밸류에이션: 재무제표 확정값 우선, 없으면 모바일 API 값 적용
            per_val = fin["PER"] if fin["PER"] != "-" else (f"{total_dict.get('PER')}배" if "PER" in total_dict else "-")
            pbr_val = fin["PBR"] if fin["PBR"] != "-" else (f"{total_dict.get('PBR')}배" if "PBR" in total_dict else "-")

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
