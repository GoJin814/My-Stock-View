import streamlit as st
import pandas as pd

def render_tab_basic(df_basic: pd.DataFrame):
    """현재 시세 탭 렌더링 함수"""
    if df_basic is None or df_basic.empty:
        st.info("표시할 시세 데이터가 없습니다.")
        return None

    df_display = df_basic.copy()

    if "선택" not in df_display.columns:
        df_display.insert(0, "선택", False)
    else:
        df_display["선택"] = df_display["선택"].fillna(False).astype(bool)

    codes = df_display["종목코드"].astype(str).str.zfill(6)
    df_display["종목코드"] = codes
    df_display["링크"] = "https://finance.naver.com/item/main.naver?code=" + codes

    target_cols = [
        "선택", "종목명", "종목코드", "현재가", "시총",
        "현재 PER", "현재 PBR", "DPS(원)", "배당수익률", "링크"
    ]
    cols_to_use = [c for c in target_cols if c in df_display.columns]
    df_render = df_display[cols_to_use].copy()
    disabled_cols = [c for c in df_render.columns if c != "선택"]

    edited_df = st.data_editor(
        df_render,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width="small"),
            "종목명": st.column_config.LinkColumn(
                "종목명",
                display_text=r"https://finance\.naver\.com/item/main\.naver\?code=(\d+)",
                width=120  # 120px 고정
            ),
            "종목코드": st.column_config.TextColumn("종목코드", width="small"),
            "현재가": st.column_config.TextColumn("현재가", width="small"),
            "시총": st.column_config.TextColumn("시총", width="small"),
            "현재 PER": st.column_config.TextColumn("현재 PER", width="small"),
            "현재 PBR": st.column_config.TextColumn("현재 PBR", width="small"),
            "DPS(원)": st.column_config.TextColumn("DPS(원)", width="small"),
            "배당수익률": st.column_config.TextColumn("배당수익률", width="small"),
            "링크": None
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key="basic_market_data_editor"
    )

    return edited_df
