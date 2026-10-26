import streamlit as st
import pandas as pd

def render_tab_basic(df_basic):
    if df_basic is None or df_basic.empty:
        st.info("표시할 현재 시세 데이터가 없습니다.")
        return None

    df_display = df_basic.copy()

    # 1. 다른 탭에서 정렬된 순서(sort_codes)가 있다면 동일한 행 순서로 재정렬
    sort_codes_param = st.query_params.get("sort_codes", "")
    if sort_codes_param and "종목코드" in df_display.columns:
        code_order = [c.strip().zfill(6) for c in str(sort_codes_param).split(",") if c.strip()]
        if code_order:
            order_map = {code: idx for idx, code in enumerate(code_order)}
            df_display["_sort_rank"] = df_display["종목코드"].astype(str).str.strip().str.zfill(6).map(order_map).fillna(9999)
            df_display = df_display.sort_values(by="_sort_rank").drop(columns=["_sort_rank"]).reset_index(drop=True)

    # 2. 전체 선택 체크박스
    c_all, _ = st.columns([1.5, 8.5])
    with c_all:
        select_all = st.checkbox("전체 선택", value=False, key="chk_basic_select_all")

    if select_all:
        df_display["선택"] = True

    # 3. 네이버 증권 링크 URL 구성 (정규식 #종목명 추출용)
    code_series = df_display["종목코드"].astype(str).str.strip().str.zfill(6)
    name_series = df_display["종목명"].astype(str).str.strip()
    df_display["종목명"] = "https://finance.naver.com/item/main.naver?code=" + code_series + "#" + name_series

    # '선택' 열만 체크/해제 가능하도록 열어두고 나머지는 읽기 전용 보호
    disabled_cols = [c for c in df_display.columns if c != "선택"]

    # 4. 체크박스 테이블 렌더링
    edited_df = st.data_editor(
        df_display,
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "",
                help="삭제할 종목 선택",
                default=False,
                width=38
            ),
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
        key=f"basic_editor_{select_all}_{sort_codes_param}"
    )

    return edited_df
