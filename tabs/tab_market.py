import streamlit as st
import pandas as pd
import json
import os

CACHE_FILE = "market_cache.json"

def load_market_cache():
    """국내지수 캐시 데이터 로드"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_market_cache(df: pd.DataFrame):
    """국내지수 캐시 데이터 저장"""
    if df is not None:
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"캐시 저장 실패: {e}")

def render_market_inputs(df_market: pd.DataFrame = None):
    """국내지수 신규 데이터 입력 폼 (필요 시 app.py에서 호출)"""
    return None

def render_tab_market(df_market: pd.DataFrame):
    """국내지수 테이블 렌더링 함수"""
    if df_market is None or df_market.empty:
        st.info("표시할 국내지수 데이터가 없습니다.")
        return

    df = df_market.copy()

    # 2. 일시 형식을 YYYY/MM/DD 형식으로 통일
    date_col = None
    for c in ["일시", "날짜", "date", "Date"]:
        if c in df.columns:
            date_col = c
            break

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y/%m/%d").fillna(df[date_col].astype(str))

    column_config = {}

    # 1. 선택 열 폭 최소화
    if "선택" in df.columns:
        column_config["선택"] = st.column_config.CheckboxColumn(
            label="선택",
            width="small",
            help="선택"
        )

    # 일시 컬럼
    if date_col:
        column_config[date_col] = st.column_config.TextColumn(
            label="일시",
            width="small"
        )

    # 4. 시가총액 컬럼 폭 충분히 확보 (1의 자리가 잘리지 않도록 medium)
    for c in df.columns:
        if "시가총액" in c:
            column_config[c] = st.column_config.TextColumn(
                label="시가총액\n(억원)",
                width="medium"
            )

    # 5. PER, PBR 폭 최소화
    if "PER" in df.columns:
        column_config["PER"] = st.column_config.TextColumn(
            label="PER",
            width="small"
        )
    if "PBR" in df.columns:
        column_config["PBR"] = st.column_config.TextColumn(
            label="PBR",
            width="small"
        )

    # 6 & 3. 고객예탁금 비율, 신용잔고 비율 축약 및 2줄 표기
    for c in df.columns:
        if "고객예탁금" in c and ("비율" in c or "지수" in c or "%" in c):
            column_config[c] = st.column_config.TextColumn(
                label="예탁금\n비율",
                width="small"
            )
        elif "신용잔고" in c and ("비율" in c or "지수" in c or "%" in c):
            column_config[c] = st.column_config.TextColumn(
                label="신용잔고\n비율",
                width="small"
            )
        elif "고객예탁금" in c:
            column_config[c] = st.column_config.TextColumn(
                label="고객예탁금\n(억원)",
                width="small"
            )
        elif "신용잔고" in c:
            column_config[c] = st.column_config.TextColumn(
                label="신용잔고\n(억원)",
                width="small"
            )

    if "환율" in df.columns:
        column_config["환율"] = st.column_config.TextColumn(
            label="환율",
            width="small"
        )

    # 테이블 렌더링
    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )
