import streamlit as st
import pandas as pd

def render_tab_basic(df_basic: pd.DataFrame):
    if df_basic.empty:
        return df_basic

    # 세션 상태 키 초기화
    if "select_all_basic" not in st.session_state:
        st.session_state["select_all_basic"] = False

    # 1. 전체 선택 토글 체크박스
    c_all, _ = st.columns([2, 5])
    with c_all:
        select_all = st.checkbox("☑️ 전체 선택 / 해제", key="select_all_basic_checkbox")

    if select_all != st.session_state["select_all_basic"]:
        st.session_state["select_all_basic"] = select_all
        df_basic["선택"] = select_all
    else:
        if st.session_state["select_all_basic"]:
            df_basic["선택"] = True

    # 2. LinkColumn용 데이터프레임 가공
    # URL 끝에 #종목명을 붙여서 display_text 정규식 그룹으로 종목명을 추출해 화면에 표시
    display_df = df_basic.copy()
    display_df["종목명_링크"] = display_df.apply(
        lambda row: f"https://stock.naver.com/domestic/stock/{row['종목코드']}/info/company#{row['종목명']}",
        axis=1
    )

    # 종목명 열의 위치에 링크 열 배치
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
                help="클릭 시 네이버 증권 기업정보 페이지로 이동합니다.",
                display_text=r"#(.+)$",  # URL 뒤에 붙은 '#종목명'에서 순수 종목명만 추출하여 표에 표시
                pinned=True
            ),
            "종목명": None,  # 원본 종목명 텍스트 열은 숨김 처리
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key=f"tab1_editor_{st.session_state['select_all_basic']}"
    )

    # 반환 시 임시 컬럼 정리
    return edited_df.drop(columns=["종목명_링크"], errors="ignore")
