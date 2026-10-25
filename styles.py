import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        :root {
            color-scheme: dark light;
        }

        /* HTML 테이블 다크 테마 바인딩 */
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
            padding: 6px 8px !important;
            text-align: center !important;
        }

        td {
            background-color: var(--background-color, #0e1117) !important;
            color: var(--text-color, #fafafa) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            padding: 6px 8px !important;
            text-align: center !important;
        }

        /* Streamlit 내장 Data Editor/Frame 다크 테마 강제 동기화 */
        [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
            background-color: var(--background-color, #0e1117) !important;
        }

        div[data-testid="stDataEditor"] > div {
            background-color: var(--background-color, #0e1117) !important;
        }

        /* 모바일/태블릿 OS 다크 모드 감지 대응 */
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

        /* 탭 간격 최적화 */
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

def render_multi_header_table(header_html: str, df, display_cols: list):
    """주당 가치 및 실적 탭에서 복합 다단 헤더와 데이터를 렌더링하는 공용 함수"""
    rows_html = []
    for _, row in df.iterrows():
        tds = []
        for col in display_cols:
            val = str(row.get(col, "-"))
            # 수치별 증감 색상 스타일링
            if "%" in val and not val.startswith("-"):
                if val.startswith("+"):
                    tds.append(f'<td style="color: #ff4b4b; font-weight: 500;">{val}</td>')
                else:
                    tds.append(f'<td>{val}</td>')
            elif val.startswith("-") and "%" in val:
                tds.append(f'<td style="color: #3182ce; font-weight: 500;">{val}</td>')
            else:
                tds.append(f'<td>{val}</td>')
        rows_html.append(f"<tr>{''.join(tds)}</tr>")

    full_table_html = f"""
    <div style="overflow-x: auto; margin-bottom: 1rem;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
            {header_html}
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
    """
    st.markdown(full_table_html, unsafe_allow_html=True)
