import streamlit as st
import pandas as pd

def render_tab_basic(df_basic):
    if df_basic is None or df_basic.empty:
        st.info("표시할 현재 시세 데이터가 없습니다.")
        return None

    # 1. 탭 간 정렬 동기화 (주당가치/실적 탭에서 정렬한 종목 순서 반영)
    sort_codes_param = st.query_params.get("sort_codes", "")
    if sort_codes_param:
        code_order = [c.strip().zfill(6) for c in str(sort_codes_param).split(",") if c.strip()]
        if code_order and "종목코드" in df_basic.columns:
            order_map = {code: idx for idx, code in enumerate(code_order)}
            df_basic = df_basic.copy()
            df_basic["_sort_rank"] = df_basic["종목코드"].astype(str).str.strip().str.zfill(6).map(order_map).fillna(9999)
            df_basic = df_basic.sort_values(by="_sort_rank").drop(columns=["_sort_rank"]).reset_index(drop=True)

    # 2. 전체 선택 체크박스
    c_all, _ = st.columns([1.5, 8.5])
    with c_all:
        select_all = st.checkbox("전체 선택", value=False, key="chk_basic_select_all")

    df_display = df_basic.copy()
    if select_all:
        df_display["선택"] = True

    # ⚡ LinkColumn용 URL 구성 (URL 뒤에 #종목명을 붙여 display_text 정규식으로 안전하게 추출)
    code_series = df_display["종목코드"].astype(str).str.strip().str.zfill(6)
    name_series = df_display["종목명"].astype(str).str.strip()
    df_display["종목명"] = "https://finance.naver.com/item/main.naver?code=" + code_series + "#" + name_series

    disabled_cols = [c for c in df_display.columns if c != "선택"]

    edited_df = st.data_editor(
        df_display,
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "",
                help="삭제할 종목 선택",
                default=False,
                width=38
            ),
            # ⚡ URL 뒤의 #종목명 텍스트만 추출하여 화면에 선명하게 출력
            "종목명": st.column_config.LinkColumn(
                "종목명",
                help="클릭 시 네이버 증권 페이지로 이동합니다.",
                display_text=r"#(.+)$",
                width=110
            ),
            "종목코드": st.column_config.TextColumn("종목코드", width=75),
            "현재가": st.column_config.TextColumn("현재가", width=90),
            "시총": st.column_config.TextColumn("시총", width=105),
            "현재 PER": st.column_config.TextColumn("현재 PER", width=75),
            "현재 PBR": st.column_config.TextColumn("현재 PBR", width=75),
            "DPS(원)": st.column_config.TextColumn("DPS(원)", width=80),
            "배당수익률": st.column_config.TextColumn("배당수익률", width=85),
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key=f"basic_table_editor_{select_all}_{sort_codes_param}"
    )

    return edited_df
