import streamlit as st
import pandas as pd

def render_tab_basic(df_basic: pd.DataFrame):
    if df_basic.empty:
        return df_basic

    if "select_all_basic" not in st.session_state:
        st.session_state["select_all_basic"] = False

    # 1. 전체 선택 체크박스
    c_all, _ = st.columns([2, 5])
    with c_all:
        select_all = st.checkbox("☑️ 전체 선택 / 해제", key="select_all_basic_checkbox")

    if select_all != st.session_state["select_all_basic"]:
        st.session_state["select_all_basic"] = select_all
        df_basic["선택"] = select_all
    else:
        if st.session_state["select_all_basic"]:
            df_basic["선택"] = True

    # 2. PC 버전 네이버 증권 기업정보 URL 매핑
    display_df = df_basic.copy()
    display_df["종목명_링크"] = display_df.apply(
        lambda row: f"https://finance.naver.com/item/coinfo.naver?code={row['종목코드']}#{row['종목명']}",
        axis=1
    )

    cols = list(display_df.columns)
    name_idx = cols.index("종목명")
    cols.insert(name_idx, cols.pop(cols.index("종목명_링크")))
    display_df = display_df[cols]

    disabled_cols = [c for c in display_df.columns if c != "선택"]

    edited_df = st.data_editor(
        display_df,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width="small", pinned=True),
            "종목명_링크": st.column_config.LinkColumn(
                "종목명",
                help="클릭 시 네이버 증권 PC 버전 기업정보 페이지로 이동합니다.",
                display_text=r"#(.+)$",
                pinned=True
            ),
            "종목명": None,
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key=f"tab1_editor_{st.session_state['select_all_basic']}"
    )

    return edited_df.drop(columns=["종목명_링크"], errors="ignore")
