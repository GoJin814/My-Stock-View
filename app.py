import streamlit as st
import requests
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="종목Scan 대시보드", layout="wide")

# 종목코드 영구 저장 파일 경로
SAVE_FILE = "saved_codes.txt"

# 저장된 종목코드 목록 불러오기
def load_codes():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            codes = [line.strip().zfill(6) for line in f.readlines() if line.strip()]
            return list(dict.fromkeys(codes)) # 중복 제거
    # 기본 초기 종목 리스트
    return ["178320", "001130", "086450", "007690", "095660"]

# 종목코드 파일에 영구 저장하기
def save_codes(codes):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        for c in codes:
            f.write(f"{c.strip().zfill(6)}\n")

# 1. 네이버 모바일 통합 정보 수집 (현재가, 시총, PER, PBR, 배당률 등)
def get_naver_summary(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# 2. 기업 상세 재무제표(최근 결산 연도) 수집
def get_recent_financials(code: str):
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://finance.naver.com/"
    }
    
    fin_data = {
        "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan, 
        "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan
    }
    
    try:
        # requests로 html을 먼저 받아온 후 파싱 (블록 방지)
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return fin_data
            
        tables = pd.read_html(resp.text, encoding="utf-8")
        target_df = None
        for df in tables:
            first_col = str(df.columns[0])
            if "주요재무정보" in first_col or "Financial" in first_col:
                target_df = df
                break
                
        if target_df is not None:
            if isinstance(target_df.columns, pd.MultiIndex):
                cols = [f"{c[1]}_{c[2]}" if c[2] else str(c[1]) for c in target_df.columns]
                target_df.columns = cols
            
            first_col_name = target_df.columns[0]
            year_cols = []
            for c in target_df.columns[1:]:
                c_str = str(c)
                # 연간 결산 컬럼 식별
                if ("20" in c_str and "/12" in c_str) or ("결산" in c_str):
                    year_cols.append(c)
            
            # (E) 추정치가 없는 가장 최근 확정 실적 컬럼 우선 선택
            actual_cols = [c for c in year_cols if "(E)" not in str(c)]
            
            recent_col = None
            if len(actual_cols) > 0:
                recent_col = actual_cols[-1]
            elif len(year_cols) > 0:
                recent_col = year_cols[0]

            prev_col = None
            if len(actual_cols) >= 2:
                prev_col = actual_cols[-2]

            if recent_col:
                def get_val(row_name, col_target):
                    matched = target_df[target_df[first_col_name].str.strip() == row_name]
                    if not matched.empty and col_target in matched.columns:
                        val = matched[col_target].values[0]
                        try:
                            return float(str(val).replace(",", ""))
                        except:
                            return np.nan
                    return np.nan

                curr_sales = get_val("매출액", recent_col)
                prev_sales = get_val("매출액", prev_col) if prev_col else np.nan
                
                fin_data["매출액"] = curr_sales
                if pd.notna(curr_sales) and pd.notna(prev_sales) and prev_sales != 0:
                    fin_data["매출YoY"] = round(((curr_sales - prev_sales) / abs(prev_sales)) * 100, 2)
                    
                fin_data["영업이익"] = get_val("영업이익", recent_col)
                fin_data["당기순이익"] = get_val("당기순이익", recent_col)
                fin_data["DPS"] = get_val("주당배당금(원)", recent_col)
                fin_data["EPS"] = get_val("EPS(원)", recent_col)
                fin_data["BPS"] = get_val("BPS(원)", recent_col)
    except Exception:
        pass
        
    return fin_data

# --- 대시보드 화면 구성 ---
st.title("📋 Scanning_주식 (누적 관리 모바일 뷰어)")
st.caption("네이버페이 증권 데이터 기반 실시간 자동 파싱 시스템")

# 파일에서 저장된 종목코드 목록 읽기
current_codes = load_codes()

# 1. 새 종목 추가 영역
col_add, col_btn = st.columns([3, 1])
with col_add:
    new_code = st.text_input("➕ 추가할 종목코드 (6자리)", placeholder="예: 005930 (삼성전자)", max_chars=6)
with col_btn:
    st.write("")
    if st.button("종목 추가", use_container_width=True):
        if new_code.strip():
            formatted_code = new_code.strip().zfill(6)
            if formatted_code not in current_codes:
                current_codes.append(formatted_code)
                save_codes(current_codes)
                st.success(f"{formatted_code} 종목이 추가되었습니다.")
                st.rerun()
            else:
                st.info("이미 목록에 등록되어 있는 종목입니다.")

# 2. 현재 관리 중인 종목 태그 표시 및 선택 삭제 기능
with st.expander("📌 관리 중인 종목 목록 / 개별 삭제", expanded=False):
    selected_to_remove = st.multiselect("삭제하고 싶은 종목코드를 선택하세요", current_codes)
    if st.button("선택 종목 삭제"):
        if selected_to_remove:
            current_codes = [c for c in current_codes if c not in selected_to_remove]
            save_codes(current_codes)
            st.success("선택한 종목이 삭제되었습니다.")
            st.rerun()

# 3. 데이터 파싱 및 테이블 출력
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권에서 종목별 최근 재무 및 시세를 집계하고 있습니다..."):
        for code in current_codes:
            summary = get_naver_summary(code)
            if not summary or "stockName" not in summary:
                continue
                
            fin = get_recent_financials(code)
            
            # 기본 시세 파싱
            stock_name = summary.get("stockName", "-")
            curr_price = summary.get("dealTrendInfos", [{}])[0].get("closePrice", "0").replace(",", "")
            
            # 요약 지표 파싱
            total_dict = {item.get("key"): item.get("value") for item in summary.get("totalInfos", [])}
            
            per_val = total_dict.get("PER", "-")
            pbr_val = total_dict.get("PBR", "-")
            div_yield = total_dict.get("배당수익률", "-")
            
            # 시가총액 텍스트
            market_cap = total_dict.get("시가총액", "-")
            
            scan_results.append({
                "종목코드": code,
                "종목명": stock_name,
                "현재가": f"{int(curr_price):,}원" if curr_price.isdigit() else curr_price,
                "시총": market_cap,
                "매출액(억)": f"{fin['매출액']:,.1f}" if pd.notna(fin['매출액']) else "-",
                "매출 YoY": f"{fin['매출YoY']:+.1f}%" if pd.notna(fin['매출YoY']) else "-",
                "영업이익(억)": f"{fin['영업이익']:,.1f}" if pd.notna(fin['영업이익']) else "-",
                "당기순익(억)": f"{fin['당기순이익']:,.1f}" if pd.notna(fin['당기순이익']) else "-",
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
