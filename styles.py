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
            border-radius: 4px;
            /* 라이트/다크 양쪽에서 확실히 보이는 테두리 */
            border: 1px solid rgba(128, 128, 128, 0.25);
            background-color: var(--background-color);
        }
        /* 기본 탭(st.data_editor)과 일치하는 표 본체 */
        .custom-multi-table {
            width: max-content;
            border-collapse: collapse;
            font-size: 0.82rem;
            color: var(--text-color);
            background-color: var(--background-color);
            font-family: var(--font, sans-serif);
        }
        /* 모든 셀 테두리: 라이트 모드에서도 또렷하게 보이는 회색 격자선 */
        .custom-multi-table th, .custom-multi-table td {
            padding: 6px 12px;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            white-space: nowrap !important;
            word-break: keep-all !important;
            text-align: right;
        }
        /* 헤더 스타일: 기본 탭의 헤더 배경 톤 일치 */
        .custom-multi-table thead th {
            background-color: rgba(128, 128, 128, 0.08) !important;
            color: var(--text-color);
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid rgba(128, 128, 128, 0.3) !important;
        }
        /* 마우스 호버 효과 */
        .custom-multi-table tbody tr:hover {
            background-color: rgba(128, 128, 128, 0.05);
        }
        /* 종목명 고정 컬럼 */
        .custom-multi-table .stock-name-cell {
            text-align: left;
            font-weight: 600;
            position: sticky;
            left: 0;
            background-color: var(--background-color) !important;
            z-index: 2;
            min-width: 85px !important;
            border-right: 2px solid rgba(128, 128, 128, 0.3) !important;
        }
        .custom-multi-table thead th.stock-name-cell {
            background-color: rgba(128, 128, 128, 0.08) !important;
        }
        /* 링크: 라이트/다크 모두 선명한 블루 유지 */
        .custom-multi-table .stock-link,
        .custom-multi-table .stock-link:visited,
        .custom-multi-table .stock-link:active,
        .custom-multi-table .stock-link:hover {
            color: #1a73e8 !important;
            text-decoration: underline;
            cursor: pointer;
            white-space: nowrap !important;
        }
        /* 연도 구분선: 굵은 회색선 */
        .custom-multi-table .divider-col {
            border-right: 2px solid rgba(128, 128, 128, 0.45) !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df: pd.DataFrame, top_headers: list, sub_headers: list, divider_indices: list = None):
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    divider_indices = divider_indices or []
    
    html = ['<div class="custom-multi-table-wrapper"><table class="custom-multi-table"><thead><tr>']
    
    # 1층 상단 헤더: 종목명은 rowspan="2"로 병합
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
    
    # 본문 데이터
    for _, row in df.iterrows():
        html.append('<tr>')
        code = str(row.get("종목코드", "")).strip()
        stock_name = str(row.get("종목명", "-"))
        
        # PC 버전 링크 연결
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
