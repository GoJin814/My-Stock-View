import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        /* ⚡ 태블릿 머티리얼 심볼 오류 텍스트(_arrow_right) 완전 제거 */
        [data-testid="stExpanderToggleIcon"],
        summary span[class*="material-symbols"],
        summary span[class*="material-icons"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            font-size: 0 !important;
        }

        [data-testid="stExpander"] summary {
            font-weight: 500 !important;
            padding: 8px 12px !important;
        }

        /* 탭 바 간격 */
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
    # 이전 호환성 유지용 빈 함수
    pass
