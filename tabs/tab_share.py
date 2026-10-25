import streamlit as st
import pandas as pd

def render_tab_share(df_share: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_share is None or df_share.empty:
        st.info("표시할 주당 가치 데이터가 없습니다.")
        return

    # 1. 2단 복합 헤더 멀티인덱스 튜플 정의 (상단 연도 대분류 / 하단 세부 지표)
    multi_cols = [
        ("종목정보", "종목명"),
        ("종목정보", "종목코드"),
        (f"{prev_yr}년", "PER"),
        (f"{prev_yr}년", "PBR"),
        (f"{prev_yr}년", "ROE"),
        (f"{prev_yr}년", "EPS"),
        (f"{prev_yr}년", "BPS"),
        (f"{latest_yr}년", "PER"),
        (f"{latest_yr}년", "PBR"),
        (f"{latest_yr}년", "ROE"),
        (f"{latest_yr}년", "EPS"),
        (f"{latest_yr}년", "BPS"),
    ]

    source_cols = [
        "종목명", "종목코드",
        "PER_직전", "PBR_직전", "ROE_직전", "EPS_직전", "BPS_직전",
        "PER_최근", "PBR_최근", "ROE_최근", "EPS_최근", "BPS_최근"
    ]

    # 데이터 추출 및 멀티인덱스 컬럼 적용
    display_df = df_share[[c for c in source_cols if c in df_share.columns]].copy()
    display_df.columns = pd.MultiIndex.from_tuples(multi_cols[:len(display_df.columns)])

    # 기본 탭과 100% 동일한 서식의 2단 헤더 그리드 출력
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True
    )
