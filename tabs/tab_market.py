import streamlit as st
import pandas as pd
import json
import os

# ⚡ 기존 저장 파일 후보들을 순서대로 탐색 (CSV 우선 -> JSON)
POSSIBLE_FILES = [
    "market_history.csv",
    "market_data.csv",
    "data/market_history.csv",
    "data/market_data.csv",
    "market_cache.json",
    "market_data.json"
]

def get_cache_file():
    for f in POSSIBLE_FILES:
        if os.path.exists(f):
            return f
    return "market_history.csv"

def load_market_cache():
    """기존 파일에서 국내지수 히스토리 데이터 로드"""
    # 1. 존재하는 파일 탐색
    for f in POSSIBLE_FILES:
        if os.path.exists(f):
            try:
                if f.endswith(".csv"):
                    return pd.read_csv(f)
                elif f.endswith(".json"):
                    with open(f, "r", encoding="utf-8") as jf:
                        return pd.DataFrame(json.load(jf))
            except Exception:
                continue
    return pd.DataFrame()

def save_market_cache(df: pd.DataFrame):
    """국내지수 데이터 저장"""
    if df is not None:
        target_file = get_cache_file()
        try:
            if target_file.endswith(".csv"):
                df.to_csv(target_file, index=False, encoding="utf-8-sig")
            else:
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"저장 실패: {e}")

def render_market_inputs(df_market: pd.DataFrame = None):
    """입력 폼 함수 호환 유지"""
    return None

def render_tab_market(df_market: pd.DataFrame = None):
    """국내지수 탭 렌더링"""
    if df_market is None or (isinstance(df_market, pd.DataFrame) and df_market.empty):
        df_market = load_market_cache()

    if df_market is None or df_market.empty:
        st.info("표시할 국내지수 데이터가 없습니다.")
        return df_market

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

    # 4. 시가총액 컬럼 폭 확보 (1의 자리가 안 잘리도록 medium)
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

    # 편집 가능한 data_editor 렌더링 및 반환
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="market_data_editor"
    )

    return edited_df
