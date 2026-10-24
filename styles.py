import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        /* 테이블 감싸는 가로 스크롤 래퍼 */
        .custom-multi-table-wrapper {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-bottom: 1rem;
            border: 1px solid rgba(250, 250, 250, 0.1);
            border-radius: 6px;
            background-color: var(--background-color);
        }
        /* 기본 탭(st.data_editor)과 100% 일치하는 시스템 테마 테이블 */
        .custom-multi-table {
            width: max-content;
            border-collapse: collapse;
            font-size: 0.82rem;
            color: var(--text-color);
            background-color: var(--background-color);
            font-family: var(--font, sans-serif);
        }
        /* 셀 테두리 및 패딩 (기본 탭 그리드 선 규격) */
        .custom-multi-table th, .custom-multi-table td {
            padding: 6px 12px;
            border: 1px solid rgba(250, 250, 250, 0.08);
            white-space: nowrap !important;
            word-break: keep-all !important;
            text-align: right;
        }
        /* 기본 탭 헤더 색상 (반투명 서브 헤더 배경) */
        .custom-multi-table thead th {
            background-color: var(--secondary-background-color);
            color: var(--text-color);
            text-align: center;
            font-weight: 600;
            border-bottom: 1px solid rgba(250, 250, 250, 0.15);
        }
        /* 행 호버 효과 */
        .custom-multi-table tbody tr:hover {
            background-color: rgba(255, 255, 255, 0.03);
        }
        /* 종목명 고정 컬럼 (기본 탭과 동일한 고정 컬럼 효과) */
        .custom-multi-table .stock-name-cell {
            text-align: left;
            font-weight: 600;
            position: sticky;
            left: 0;
            background-color: var(--background-color);
            z-index: 2;
            min-width: 85px !important;
            border-right: 1px solid rgba(250, 250, 250, 0.15) !important;
        }
        .custom-multi-table thead th.stock-name-cell {
            background-color: var(--secondary-background-color) !important;
        }
        /* 기본 탭의 종목명 링크와 정확히 동일한 파란색 (방문 후에도 색상 불변) */
        .custom-multi-table .stock-link,
        .custom-multi-table .stock-link:visited,
        .custom-multi-table .stock-link:active,
        .custom-multi-table .stock-link:hover {
            color: #58a6ff !important;
            text-decoration: underline;
            cursor: pointer;
            white-space: nowrap !important;
        }
        /* 연도 간 구분선 */
        .custom-multi-table .divider-col {
            border-right: 2px solid rgba(250, 250, 250, 0.25) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df: pd.DataFrame, top_headers: list, sub_headers: list, divider_indices: list = None):
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    divider_indices = divider_indices or []
    
    html = ['<div class="custom-multi-table-wrapper"><table class="custom-multi-table"><thead><tr>']
    
    # 1층 상단 헤더: 종목명은 rowspan="2"로 2개 층을 병합하여 깔끔하게 정렬
    for title, colspan, has_border in top_headers:
        border_cls = ' class="divider-col"' if has_border else ''
        if title == "종목명":
            html.append(f'<th rowspan="2" class="stock-name-cell"{border_cls}>{title}</th>')
        else:
            html.append(f'<th colspan="{colspan}"{border_cls}>{title}</th>')
    html.append('</tr><tr>')
    
    # 2층 서브 헤더
    for idx, sub in enumerate(sub_headers):
        border_cls = ' class="divider-col"' if idx in divider_indices else ''
        html.append(f'<th{border_cls}>{sub}</th>')
    html.append('</tr></thead><tbody>')
    
    # 본문 데이터 행
    for _, row in df.iterrows():
        html.append('<tr>')
        code = str(row.get("종목코드", "")).strip()
        stock_name = str(row.get("종목명", "-"))
        
        # PC 버전 네이버 증권 링크
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
