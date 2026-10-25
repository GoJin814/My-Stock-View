import streamlit as st
import pandas as pd

def render_tab_share(df_share: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_share is None or df_share.empty:
        st.info("표시할 주당 가치 데이터가 없습니다.")
        return None

    df_display = df_share.copy()

    # 네이버 PC 웹 링크 컬럼 생성
    codes = df_display["종목코드"].astype(str).str.zfill(6)
    df_display["링크"] = "https://finance.naver.com/item/main.naver?code=" + codes

    # 컬럼명 매핑 (연도를 헤더에 명확히 표기)
    rename_dict = {
        "PER_직전": f"{prev_yr} PER",
        "PBR_직전": f"{prev_yr} PBR",
        "ROE_직전": f"{prev_yr} ROE",
        "EPS_직전": f"{prev_yr} EPS",
        "BPS_직전": f"{prev_yr} BPS",
        "PER_최근": f"{latest_yr} PER",
        "PBR_최근": f"{latest_yr} PBR",
        "ROE_최근": f"{latest_yr} ROE",
        "EPS_최근": f"{latest_yr} EPS",
        "BPS_최근": f"{latest_yr} BPS",
    }
    df_display = df_display.rename(columns=rename_dict)

    target_cols = [
        "종목명", "종목코드", "링크",
        f"{prev_yr} PER", f"{prev_yr} PBR", f"{prev_yr} ROE", f"{prev_yr} EPS", f"{prev_yr} BPS",
        f"{latest_yr} PER", f"{latest_yr} PBR", f"{latest_yr} ROE", f"{latest_yr} EPS", f"{latest_yr} BPS"
    ]
    cols_to_use = [c for c in target_cols if c in df_display.columns]
    df_result = df_display[cols_to_use].copy()

    # 기본 탭과 100% 동일한 st.data_editor 사용
    edited_df = st.data_editor(
        df_result,
        column_config={
            "종목명": st.column_config.LinkColumn(
                "종목명",
                display_text=r"https://finance\.naver\.com/item/main\.naver\?code=(\d+)",
                width="small"
            ),
            "종목코드": st.column_config.TextColumn("종목코드", width="small"),
            "링크": None,  # 링크 주소 열 숨김
            f"{prev_yr} PER": st.column_config.TextColumn(f"{prev_yr} PER", width="small"),
            f"{prev_yr} PBR": st.column_config.TextColumn(f"{prev_yr} PBR", width="small"),
            f"{prev_yr} ROE": st.column_config.TextColumn(f"{prev_yr} ROE", width="small"),
            f"{prev_yr} EPS": st.column_config.TextColumn(f"{prev_yr} EPS", width="small"),
            f"{prev_yr} BPS": st.column_config.TextColumn(f"{prev_yr} BPS", width="small"),
            f"{latest_yr} PER": st.column_config.TextColumn(f"{latest_yr} PER", width="small"),
            f"{latest_yr} PBR": st.column_config.TextColumn(f"{latest_yr} PBR", width="small"),
            f"{latest_yr} ROE": st.column_config.TextColumn(f"{latest_yr} ROE", width="small"),
            f"{latest_yr} EPS": st.column_config.TextColumn(f"{latest_yr} EPS", width="small"),
            f"{latest_yr} BPS": st.column_config.TextColumn(f"{latest_yr} BPS", width="small"),
        },
        disabled=df_result.columns.tolist(),
        hide_index=True,
        use_container_width=True,
        key="tab_share_editor"
    )
    return edited_df
