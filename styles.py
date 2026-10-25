import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        /* ⚡ 1. 모바일 아래로 당겨 새로고침(Pull-to-refresh) 정상 작동 */
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            overscroll-behavior-y: auto !important;
            touch-action: pan-y pinch-zoom !important;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 2. 태블릿 브라우저 Expander 깨짐 문자열(_arrow_right) 완전 제거 */
        [data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"] {
            font-size: 0px !important;
            line-height: 0 !important;
            width: 1.2rem !important;
            height: 1.2rem !important;
            color: transparent !important;
            user-select: none !important;
        }

        [data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"] svg {
            display: inline-block !important;
            width: 1.2rem !important;
            height: 1.2rem !important;
            color: #fafafa !important;
            fill: currentColor !important;
        }

        [data-testid="stExpander"] summary {
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 8px 12px !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
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
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(*args, **kwargs):
    pass
