import streamlit as st
import pandas as pd

def render_tab_market(df_market: pd.DataFrame):
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
        # 문자열 또는 날짜형 데이터를 YYYY/MM/DD 형태로 변환
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y/%m/%d").fillna(df[date_col].astype(str))

    # 3 & 6. 컬럼 헤더명 2줄 줄바꿈 및 축약
    # st.dataframe에서는 개행문자(\n)를 컬럼 레이블에 주입하면 헤더가 자연스럽게 2단(2줄)으로 표시됩니다.
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

    # 4. 시가총액 컬럼 폭 충분히 확보 (1의 자리가 잘리지 않도록 medium으로 지정)
    market_cap_cols = [c for c in df.columns if "시가총액" in c]
    for c in market_cap_cols:
        column_config[c] = st.column_config.TextColumn(
            label="시가총액\n(억원)",
            width="medium"
        )

    # 5. PER, PBR 폭 최소화 (small 지정)
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
    deposit_ratio_cols = [c for c in df.columns if "고객예탁금" in c and ("비율" in c or "지수" in c or "%" in c)]
    for c in deposit_ratio_cols:
        column_config[c] = st.column_config.TextColumn(
            label="예탁금\n비율",
            width="small"
        )

    credit_ratio_cols = [c for c in df.columns if "신용잔고" in c and ("비율" in c or "지수" in c or "%" in c)]
    for c in credit_ratio_cols:
        column_config[c] = st.column_config.TextColumn(
            label="신용잔고\n비율",
            width="small"
        )

    # 3. 그 외 긴 헤더명(예탁금액, 신용잔고액)도 2줄로 표기
    deposit_amt_cols = [c for c in df.columns if "고객예탁금" in c and c not in deposit_ratio_cols]
    for c in deposit_amt_cols:
        column_config[c] = st.column_config.TextColumn(
            label="고객예탁금\n(억원)",
            width="small"
        )

    credit_amt_cols = [c for c in df.columns if "신용잔고" in c and c not in credit_ratio_cols]
    for c in credit_amt_cols:
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
