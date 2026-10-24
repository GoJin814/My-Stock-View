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
        /* 테이블 감싸는 가로 스크롤 영역 */
        .custom-multi-table-wrapper {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            margin-bottom: 1rem;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background-color: #ffffff;
        }
        /* 기본 탭과 일치하는 화이트 모드 스타일 */
        .custom-multi-table {
            width: max-content; /* 값이 모두 보이는 최소 너비로 컴팩트하게 설정 */
            border-collapse: collapse;
            font-size: 0.82rem;
            color: #31333F;
            background-color: #ffffff;
        }
        /* 셀 테두리 및 패딩 (타이트하게 유지) */
        .custom-multi-table th, .custom-multi-table td {
            padding: 6px 10px;
            border: 1px solid #f0f2f6;
            white-space: nowrap !important;
            word-break: keep-all !important;
            text-align: right;
        }
        /* 헤더 스타일: 연한 그레이 배경 (기본 탭 data_editor 헤더 색상) */
        .custom-multi-table thead th {
            background-color: #f8f9fa;
            color: #555867;
            text-align: center;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }
        /* 짝수 행 은은한 줄무늬 */
        .custom-multi-table tbody tr:nth-child(even) {
            background-color: #fafbfc;
        }
        .custom-multi-table tbody tr:hover {
            background-color: #f1f3f5;
        }
        /* 종목명 고정 컬럼 (화이트 배경으로 본문 통일) */
        .custom-multi-table .stock-name-cell {
            text-align: left;
            font-weight: 600;
            position: sticky;
            left: 0;
            background-color: #ffffff;
            z-index: 2;
            min-width: 80px !important;
            border-right: 1px solid #e0e0e0 !important;
        }
        .custom-multi-table thead th.stock-name-cell {
            background-color: #f8f9fa !important;
        }
        .custom-multi-table tbody tr:nth-child(even) .stock-name-cell {
            background-color: #fafbfc;
        }
        .custom-multi-table tbody tr:hover .stock-name-cell {
            background-color: #f1f3f5;
        }
        /* 링크 클릭 전/후(visited) 모두 선명한 블루 색상 유지 */
        .custom-multi-table .stock-link,
        .custom-multi-table .stock-link:visited,
        .custom-multi-table .stock-link:active,
        .custom-multi-table .stock-link:hover {
            color: #0969da !important;
            text-decoration: underline;
            cursor: pointer;
        }
        /* 연도 구분선 */
        .custom-multi-table .divider-col {
            border-right: 2px solid #d0d7de !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df: pd.DataFrame, top_headers: list, sub_headers: list, divider_indices: list = None):
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    divider_indices = divider_indices or []
    
    html = ['<div class="custom-multi-table-wrapper"><table class="custom-multi-table"><thead><tr>']
    
    # 1층 상단 헤더
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
        
        # 종목명 링크
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
