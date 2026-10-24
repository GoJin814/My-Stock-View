import streamlit as st
import pandas as pd

def apply_custom_styles():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .custom-multi-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            text-align: right;
            margin-bottom: 1rem;
        }
        .custom-multi-table th, .custom-multi-table td {
            padding: 8px 10px;
            border: 1px solid #333842;
        }
        .custom-multi-table thead th {
            background-color: #1e222b;
            color: #d1d5db;
            text-align: center;
            font-weight: 600;
        }
        .custom-multi-table tbody tr:nth-child(even) {
            background-color: #161920;
        }
        .custom-multi-table tbody tr:hover {
            background-color: #262c38;
        }
        .custom-multi-table .stock-name-cell {
            text-align: left;
            font-weight: 600;
            position: sticky;
            left: 0;
            background-color: #1e222b;
            z-index: 1;
        }
        .custom-multi-table .stock-link {
            color: #58a6ff;
            text-decoration: none;
        }
        .custom-multi-table .stock-link:hover {
            text-decoration: underline;
        }
        .custom-multi-table .divider-col {
            border-right: 2px solid #6b7280 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df: pd.DataFrame, top_headers: list, sub_headers: list, divider_indices: list = None):
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    divider_indices = divider_indices or []
    
    # HTML 구성
    html = ['<div style="overflow-x: auto;"><table class="custom-multi-table"><thead><tr>']
    
    # 1층 상단 헤더
    for title, colspan, has_border in top_headers:
        border_cls = ' class="divider-col"' if has_border else ''
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
        
        # 종목명 열: PC 버전 링크 적용
        if code and code != "-":
            link_url = f"https://finance.naver.com/item/coinfo.naver?code={code}"
            name_cell = f'<td class="stock-name-cell"><a class="stock-link" href="{link_url}" target="_blank">{stock_name}</a></td>'
        else:
            name_cell = f'<td class="stock-name-cell">{stock_name}</td>'
        html.append(name_cell)
        
        # 나머지 데이터 열
        val_cols = [c for c in df.columns if c not in ["종목명", "종목코드"]]
        for idx, col in enumerate(val_cols):
            border_cls = ' class="divider-col"' if idx in divider_indices else ''
            val = str(row[col])
            html.append(f'<td{border_cls}>{val}</td>')
        html.append('</tr>')
        
    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)
