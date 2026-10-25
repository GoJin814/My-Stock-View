import streamlit as st
import pandas as pd

def render_tab_perf(df_perf: pd.DataFrame, prev_yr: str, latest_yr: str):
    if df_perf is None or df_perf.empty:
        st.info("표시할 실적 데이터가 없습니다.")
        return None

    df_display = df_perf.copy()

    # 네이버 PC 웹 링크 컬럼 생성
    codes = df_display["종목코드"].astype(str).str.zfill(6)
    df_display["링크"] = "https://finance.naver.com/item/main.naver?code=" + codes

    # 컬럼명 매핑
    rename_dict = {
        "매출_직전": f"{prev_yr} 매출액",
        "영업익_직전": f"{prev_yr} 영업익",
        "순익_직전": f"{prev_yr} 순이익",
        "매출_최근": f"{latest_yr} 매출액",
        "영업익_최근": f"{latest_yr} 영업익",
        "순익_최근": f"{latest_yr} 순이익",
        "매출_YoY": "매출 YoY",
        "영업익_YoY": "영업익 YoY",
        "순익_YoY": "순익 YoY"
    }
    df_display = df_display.rename(columns=rename_dict)

    target_cols = [
        "종목명", "종목코드", "링크",
        f"{prev_yr} 매출액", f"{prev_yr} 영업익", f"{prev_yr} 순이익",
        f"{latest_yr} 매출액", f"{latest_yr} 영업익", f"{latest_yr} 순이익",
        "매출 YoY", "영업익 YoY", "순익 YoY"
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
            "링크": None,
            f"{prev_yr} 매출액": st.column_config.TextColumn(f"{prev_yr} 매출액", width="small"),
            f"{prev_yr} 영업익": st.column_config.TextColumn(f"{prev_yr} 영업익", width="small"),
            f"{prev_yr} 순이익": st.column_config.TextColumn(f"{prev_yr} 순이익", width="small"),
            f"{latest_yr} 매출액": st.column_config.TextColumn(f"{latest_yr} 매출액", width="small"),
            f"{latest_yr} 영업익": st.column_config.TextColumn(f"{latest_yr} 영업익", width="small"),
            f"{latest_yr} 순이익": st.column_config.TextColumn(f"{latest_yr} 순이익", width="small"),
            "매출 YoY": st.column_config.TextColumn("매출 YoY", width="small"),
            "영업익 YoY": st.column_config.TextColumn("영업익 YoY", width="small"),
            "순익 YoY": st.column_config.TextColumn("순익 YoY", width="small"),
        },
        disabled=df_result.columns.tolist(),
        hide_index=True,
        use_container_width=True,
        key="tab_perf_editor"
    )
    return edited_df
