import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        /* 1. 다크모드/라이트모드 공통 컨테이너 및 테이블 테마 바인딩 */
        :root {
            color-scheme: dark light;
        }

        /* 2. 모든 HTML Table에 대해 다크 테마 배경 및 텍스트 강제 상속 */
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            background-color: var(--secondary-background-color, #1a1c24) !important;
            color: var(--text-color, #fafafa) !important;
        }

        th {
            background-color: var(--secondary-background-color, #262730) !important;
            color: var(--text-color, #fafafa) !important;
            border: 1px solid rgba(128, 128, 128, 0.25) !important;
        }

        td {
            background-color: var(--background-color, #0e1117) !important;
            color: var(--text-color, #fafafa) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
        }

        /* 3. Streamlit Data Editor / DataFrame 캔버스 배경 다크 동기화 */
        [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
            background-color: var(--background-color, #0e1117) !important;
        }

        div[data-testid="stDataEditor"] > div {
            background-color: var(--background-color, #0e1117) !important;
        }

        /* 4. 모바일/태블릿 OS 다크 모드 감지 시 강제 다크 배경 */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background-color: #0e1117 !important;
                color: #fafafa !important;
            }
            table {
                background-color: #161a23 !important;
                color: #fafafa !important;
            }
            th {
                background-color: #1f2430 !important;
                color: #fafafa !important;
            }
            td {
                background-color: #0e1117 !important;
                color: #fafafa !important;
            }
            div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
                background-color: #0e1117 !important;
            }
        }

        /* 5. 모바일 화면 가로 스크롤 및 탭 최적화 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 12px;
            padding-right: 12px;
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)
