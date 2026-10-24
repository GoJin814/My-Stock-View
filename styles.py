import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        /* 모바일 브라우저의 기본 pull-to-refresh 제스처 허용 */
        html, body, [data-testid="stAppViewContainer"] {
            overscroll-behavior-y: auto !important;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }

        /* 테이블 감싸는 가로 스크롤 래퍼: 세로 방향 당김 제스처는 브라우저로 통과 */
        .custom-multi-table-wrapper {
            width: 100%;
            overflow-x: auto;
            overflow-y: visible; /* 세로 스크롤 가둠 해제 */
            overscroll-behavior-x: contain; /* 가로는 테이블 내부만 스크롤 */
            overscroll-behavior-y: auto;    /* 세로는 브라우저 당겨서 새로고침 허용 */
            -webkit-overflow-scrolling: touch;
            margin-bottom: 1rem;
            border-radius: 4px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            background-color: var(--background-color, #ffffff);
        }

        /* 테이블 기본 */
        .custom-multi-table {
            width: max-content;
            border-collapse: collapse;
            font-size: 0.82rem;
            color: var(--text-color, #31333F);
            background-color: var(--background-color, #ffffff);
            font-family: var(--font, sans-serif);
        }

        /* 셀 테두리 및 패딩 */
        .custom-multi-table th, .custom-multi-table td {
            padding: 6px 12px;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            white-space: nowrap !important;
            word-break: keep-all !important;
            text-align: right;
            background-color: var(--background-color, #ffffff);
        }

        /* 상단 일반 헤더 */
        .custom-multi-table thead th {
            background-color: #f0f2f6 !important;
            color: var(--text-color, #31333F);
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid rgba(128, 128, 128, 0.3) !important;
        }

        /* 좌측 고정 종목명 헤더 */
        .custom-multi-table thead th.stock-name-cell {
            position: sticky;
            left: 0;
            z-index: 10;
            background-color: #f0f2f6 !important;
            border-right: 2px solid rgba(128, 128, 128, 0.4) !important;
        }

        /* 좌측 고정 종목명 데이터 셀 */
        .custom-multi-table tbody td.stock-name-cell {
            text-align: left;
            font-weight: 600;
            position: sticky;
            left: 0;
            z-index: 5;
            background-color: #ffffff !important;
            min-width: 85px !important;
            border-right: 2px solid rgba(128, 128, 128, 0.4) !important;
        }

        /* 링크 색상 */
        .custom-multi-table .stock-link,
        .custom-multi-table .stock-link:visited,
        .custom-multi-table .stock-link:active,
        .custom-multi-table .stock-link:hover {
            color: #1a73e8 !important;
            text-decoration: underline;
            cursor: pointer;
            white-space: nowrap !important;
        }

        /* 연도 구분선 */
        .custom-multi-table .divider-col {
            border-right: 2px solid rgba(128, 128, 128, 0.45) !important;
        }

        /* 다크 모드 스타일 */
        @media (prefers-color-scheme: dark) {
            .custom-multi-table-wrapper {
                background-color: #0e1117 !important;
            }
            .custom-multi-table {
                background-color: #0e1117 !important;
                color: #fafafa !important;
            }
            .custom-multi-table th, .custom-multi-table td {
                background-color: #0e1117 !important;
                border-color: rgba(250, 250, 250, 0.12) !important;
            }
            .custom-multi-table thead th {
                background-color: #1a1c24 !important;
                border-bottom-color: rgba(250, 250, 250, 0.25) !important;
            }
            .custom-multi-table thead th.stock-name-cell {
                background-color: #1a1c24 !important;
                border-right-color: rgba(250, 250, 250, 0.3) !important;
            }
            .custom-multi-table tbody td.stock-name-cell {
                background-color: #0e1117 !important;
                border-right-color: rgba(250, 250, 250, 0.3) !important;
            }
            .custom-multi-table .stock-link,
            .custom-multi-table .stock-link:visited,
            .custom-multi-table .stock-link:active,
            .custom-multi-table .stock-link:hover {
                color: #58a6ff !important;
            }
            .custom-multi-table .divider-col {
                border-right-color: rgba(250, 250, 250, 0.35) !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df: pd.DataFrame, top_headers: list, sub_headers: list, divider_indices: list = None):
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    divider_indices = divider_indices or []
    
    html = ['<div class="custom-multi-table-wrapper"><table class="custom-multi-table"><thead><tr>']
    
    for title, colspan, has_border in top_headers:
        border_cls = ' class="divider-col"' if has_border else ''
        if title == "종목명":
            html.append(f'<th rowspan="2" class="stock-name-cell"{border_cls}>{title}</th>')
        else:
            html.append(f'<th colspan="{colspan}"{border_cls}>{title}</th>')
    html.append('</tr><tr>')
    
    for idx, sub in enumerate(sub_headers):
        border_cls = ' class="divider-col"' if idx in divider_indices else ''
        html.append(f'<th{border_cls}>{sub}</th>')
    html.append('</tr></thead><tbody>')
    
    for _, row in df.iterrows():
        html.append('<tr>')
        code = str(row.get("종목코드", "")).strip()
        stock_name = str(row.get("종목명", "-"))
        
        if code and code != "-":
            link_url = f"https://finance.naver.com/item/coinfo.naver?code={code}"
            name_cell = f'<td class="stock-name-cell"><a class="stock-link" href="{link_url}" target="_blank">{stock_name}</a></td>'
        else:
            name_cell = f'<td class="stock-name-cell">{stock_name}</td>'
        html.append(name_cell)
        
        val_cols = [c for c in df.columns if c not in ["종목명", "종목코드"]]
        for idx, col in enumerate(val_cols):
            border_cls = ' class="divider-col"' if idx in divider_indices else ''
            val = str(row[col])
            html.append(f'<td{border_cls}>{val}</td>')
        html.append('</tr>')
        
    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)
