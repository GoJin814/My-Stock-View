import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        /* 모바일(웨일/크롬) 아래로 당겨 새로고침(Pull-to-refresh) 정상 작동 */
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            overscroll-behavior-y: auto !important;
            touch-action: pan-y pinch-zoom !important;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* 탭 버튼 스타일 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
        }

        /* Expander 기본 라벨 스타일 정돈 */
        [data-testid="stExpander"] summary {
            font-size: 0.92rem !important;
            font-weight: 500 !important;
        }
        </style>
    """, unsafe_allow_html=True)
