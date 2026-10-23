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
            # 멀티 인덱스 정리
            if isinstance(target_df.columns, pd.MultiIndex):
                # 연간 실적 컬럼만 추출 (보통 앞쪽 4~5개 컬럼이 연간 실적)
                cols = [f"{c[1]}_{c[2]}" if c[2] else str(c[1]) for c in target_df.columns]
                target_df.columns = cols
            
            # 연간 실적 중 가장 최근 결산(IFRS연결/확정) 컬럼 찾기 (추정치 E 제외 우선)
            first_col_name = target_df.columns[0]
            year_cols = [c for c in target_df.columns[1:] if ("20" in str(c) and "/12" in str(c) or "결산" in str(c))]
            
            # 실적 확정 컬럼 선정 (E(추정) 표시가 안 붙은 마지막 컬럼)
            actual_cols = [c for c in year_cols if "(E)" not in str(c)]
            recent_col = actual_cols[-1] if actual_cols else (year_cols[0] if year_
