import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="종목Scan 대시보드", layout="wide")

# 1. 네이버 모바일 통합 정보 수집 (현재가, 시총, PER, PBR, 배당률 등)
def get_naver_summary(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    fin_data = {
        "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan, 
        "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan
    }
    
    try:
        tables = pd.read_html(url, encoding="utf-8")
        target_df = None
        for df in tables:
            first_col = str(df.columns[0])
            if "주요재무정보" in first_col or "Financial" in first_col:
                target_df = df
                break
                
        if target_df is not None:
            # 멀티 인덱스 평탄화
            if isinstance(target_df.columns, pd.MultiIndex):
                cols = [f"{c[1]}_{c[2]}" if c[2] else str(c[1]) for c in target_df.columns]
                target_df.columns = cols
            
            # 연간 실적 컬럼 추출
            first_col_name = target_df.columns[0]
            year_cols = []
            for c in target_df.columns[1:]:
                c_str = str(c)
                if ("20" in c_str and "/12" in c_str) or ("결산" in c_str):
                    year_cols.append(c)
            
            # (E) 추정치가 없는 확정 실적 컬럼 우선 선택 (문법 오류 방지용 안전 분기)
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

                # 값 추출
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
st.title("📋 Scanning_주식 (모바일 뷰어)")
st.caption("네이버페이 증권 데이터 기반 실시간 자동 파싱 시스템")

# 종목코드 입력창
raw_input = st.text_input(
    "종목코드를 입력하세요 (여러 개는 쉼표나 띄어쓰기로 구분)", 
    value="178320, 001130, 086450, 007690, 095660"
)

if raw_input:
    code_list = [c.strip().zfill(6) for c in raw_input.replace(",", " ").split() if c.strip()]
    scan_results = []
    
    with st.spinner("네이버 증권에서 데이터를 집계하고 있습니다..."):
        for code in code_list:
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
            
            # 행 데이터 조립
            scan_results.append({
                "종목코드": code,
                "종목명": stock_name,
                "현재가": f"{int(curr_price):,}원" if curr_price.isdigit() else curr_price,
                "시총": total_dict.get("시가총액", "-"),
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
        st.warning("유효한 종목코드를 찾을 수 없습니다. 종목 코드를 확인해 주세요.")
