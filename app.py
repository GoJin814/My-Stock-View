import streamlit as st
import requests
import pandas as pd

# 모바일 화면 최적화
st.set_page_config(page_title="주식 종목 밸류에이션", layout="wide")

# 1. 네이버 모바일 증권 시세/지표 수집
def get_stock_info(code):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

# 2. 기업 재무제표 요약 테이블 수집
def get_financial_table(code):
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        tables = pd.read_html(url, encoding="utf-8")
        for df in tables:
            first_col = str(df.columns[0])
            if "주요재무정보" in first_col or "Financial" in first_col:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [f"{c[1]}_{c[2]}" if c[2] else str(c[1]) for c in df.columns]
                return df
    except:
        pass
    return None

# UI 구성
st.title("📱 주식 종목 밸류에이션")

code = st.text_input("종목 코드 6자리를 입력하세요", value="178320")

if code:
    with st.spinner("네이버 증권에서 데이터를 불러오는 중..."):
        info = get_stock_info(code)
        fin_df = get_financial_table(code)

    if not info or "stockName" not in info:
        st.error("종목 정보를 찾을 수 없습니다. 종목 코드를 다시 확인해 주세요.")
    else:
        name = info.get("stockName", "")
        close_price = info.get("dealTrendInfos", [{}])[0].get("closePrice", "0")
        fluct_rate = info.get("dealTrendInfos", [{}])[0].get("fluctuationsRatio", "0.0")
        market_cap = info.get("totalInfos", [{}])[0].get("value", "-")
        
        st.subheader(f"{name} ({code})")
        
        c1, c2 = st.columns(2)
        c1.metric("현재가", f"{close_price}원", f"{fluct_rate}%")
        c2.metric("시가총액", market_cap)

        metrics = {item.get("key"): item.get("value") for item in info.get("totalInfos", [])}
        st.write("---")
        st.markdown(f"""
        * **PER**: `{metrics.get('PER', '-')}`배
        * **PBR**: `{metrics.get('PBR', '-')}`배
        * **배당수익률**: `{metrics.get('배당수익률', '-')}`
        * **외국인 소진율**: `{metrics.get('외국인소진율', '-')}`
        * **52주 최고/최저**: `{metrics.get('52주최고', '-')}` / `{metrics.get('52주최저', '-')}`
        """)

        st.write("---")
        st.subheader("📊 최근 재무 요약")
        if fin_df is not None:
            first_col = fin_df.columns[0]
            targets = ["매출액", "영업이익", "당기순이익", "영업이익률", "ROE(%)", "부채비율", "EPS(원)"]
            filtered = fin_df[fin_df[first_col].str.strip().isin(targets)]
            if not filtered.empty:
                st.dataframe(filtered.set_index(first_col), use_container_width=True)
            else:
                st.dataframe(fin_df.head(10), use_container_width=True)
        else:
            st.info("재무제표 상세 데이터를 가져올 수 없습니다.")
