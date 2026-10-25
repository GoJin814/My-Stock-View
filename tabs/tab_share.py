import streamlit as st
import pandas as pd

def render_tab_share(df_share: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_share is None or df_share.empty:
        st.info("표시할 주당 가치 데이터가 없습니다.")
        return

    # 네이버 PC 링크 생성
    df_temp = df_share.copy()
    df_temp["link"] = "https://finance.naver.com/item/main.naver?code=" + df_temp["종목코드"].astype(str).str.zfill(6)

    # 기본 탭과 100% 동일한 판다스 멀티인덱스 2단 구조
    cols = [
        ("종목정보", "종목명"),
        ("종목정보", "종목코드"),
        (f"{prev_yr}", "PER"),
        (f"{prev_yr}", "PBR"),
        (f"{prev_yr}", "ROE"),
        (f"{prev_yr}", "EPS"),
        (f"{prev_yr}", "BPS"),
        (f"{latest_yr}", "PER"),
        (f"{latest_yr}", "PBR"),
        (f"{latest_yr}", "ROE"),
        (f"{latest_yr}", "EPS"),
        (f"{latest_yr}", "BPS"),
    ]

    source_cols = [
        "종목명", "종목코드",
        "PER_직전", "PBR_직전", "ROE_직전", "EPS_직전", "BPS_직전",
        "PER_최근", "PBR_최근", "ROE_최근", "EPS_최근", "BPS_최근"
    ]

    display_df = df_temp[source_cols].copy()
    display_df.columns = pd.MultiIndex.from_tuples(cols)
    display_df[("종목정보", "링크")] = df_temp["link"]

    # 기본 탭과 동일한 공식 엔진으로 렌더링
    st.dataframe(
        display_df,
        column_config={
            ("종목정보", "종목명"): st.column_config.LinkColumn(
                "종목명",
                display_text=r"https://finance\.naver\.com/item/main\.naver\?code=(\d+)",
                width="small"
            ),
            ("종목정보", "종목코드"): st.column_config.TextColumn("종목코드", width="small"),
            ("종목정보", "링크"): None,  # 숨김
        },
        hide_index=True,
        use_container_width=True
    )
