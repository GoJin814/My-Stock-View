import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def apply_custom_styles():
    st.markdown("""
        <meta name="color-scheme" content="dark">
        <meta name="supported-color-schemes" content="dark">

        <style>
        :root {
            color-scheme: dark !important;
        }

        html, body {
            color-scheme: dark !important;
            background-color: #0e1117 !important;
            overscroll-behavior-y: auto !important;
            touch-action: pan-x pan-y pinch-zoom !important;
            height: auto !important;
            min-height: 100% !important;
        }

        .stApp, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stMain"],
        section.main {
            background-color: #0e1117 !important;
            overscroll-behavior-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 100% !important;
        }

        div[data-testid="stToggle"] {
            margin-bottom: 0.5rem !important;
        }

        div[data-testid="stToggle"] label p {
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            color: #fafafa !important;
        }

        .filter-container-box {
            background-color: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            padding: 12px 14px !important;
            margin-bottom: 1.2rem !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-left: 14px;
            padding-right: 14px;
            white-space: nowrap;
            font-size: 0.92rem !important;
        }

        .custom-grid-wrapper {
            overflow-x: auto !important;
            overflow-y: auto !important;
            max-height: 70vh !important;
            margin-bottom: 1.2rem;
            border-radius: 4px;
            border: 1px solid #334155;
            background-color: #0e1117;
            width: 100%;
            -webkit-overflow-scrolling: touch;
            position: relative;
        }

        .custom-grid-table {
            width: max-content !important;
            min-width: 100% !important;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            font-size: 0.82rem;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #f3f4f6;
            background-color: #0e1117;
        }

        .custom-grid-table thead {
            position: sticky !important;
            top: 0 !important;
            z-index: 10 !important;
        }

        .custom-grid-table th {
            background-color: #161a22 !important;
            color: #9ca3af !important;
            font-weight: 500 !important;
            font-size: 0.81rem !important;
            padding: 6px 10px !important;
            border-bottom: 2px solid #334155 !important; /* 헤더 하단 구분선 강조 */
            border-right: 1px solid #262c36 !important;
            text-align: center !important;
            white-space: normal !important;
            word-break: keep-all !important;
            line-height: 1.2 !important;
            user-select: none !important;
            box-sizing: border-box !important;
            vertical-align: middle !important;
        }

        .custom-grid-table thead tr:first-child th {
            top: 0 !important;
            z-index: 10 !important;
        }

        .custom-grid-table thead tr:nth-child(2) th {
            top: 2.15rem !important;
            z-index: 10 !important;
        }

        .custom-grid-table th.col-chk-th,
        .custom-grid-table td.col-chk {
            position: sticky !important;
            left: 0 !important;
            width: 40px !important;
            min-width: 40px !important;
            max-width: 40px !important;
            text-align: center !important;
            background-color: #161a22 !important;
            border-right: 1px solid #262c36 !important;
            padding: 6px 0 !important;
        }
        .custom-grid-table th.col-chk-th {
            top: 0 !important;
            z-index: 100 !important;
        }
        .custom-grid-table td.col-chk {
            z-index: 5 !important;
            background-color: #0e1117 !important;
        }

        .custom-grid-table th.col-name-th {
            position: sticky !important;
            top: 0 !important;
            z-index: 100 !important;
            background-color: #161a22 !important;
            width: 120px !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: left !important;
            padding-left: 12px !important;
            border-right: none !important;
            vertical-align: middle !important;
        }

        .custom-grid-table td.col-name {
            position: sticky !important;
            z-index: 5 !important;
            background-color: #0e1117 !important;
            width: 120px !important;
            min-width: 120px !important;
            max-width: 120px !important;
            text-align: left !important;
            padding-left: 12px !important;
            padding-right: 8px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            border-right: none !important;
        }

        .table-has-chk th.col-name-th,
        .table-has-chk td.col-name {
            left: 40px !important;
        }
        .table-no-chk th.col-name-th,
        .table-no-chk td.col-name {
            left: 0 !important;
        }

        .custom-grid-table th.col-name-th::after,
        .custom-grid-table td.col-name::after {
            content: "" !important;
            position: absolute !important;
            top: 0 !important;
            right: 0 !important;
            width: 2.5px !important;
            height: 100% !important;
            background-color: #ffffff !important;
            pointer-events: none !important;
            z-index: 101 !important;
        }

        .custom-grid-table th.year-divider,
        .custom-grid-table td.year-divider {
            border-right: 2.5px solid #ffffff !important;
        }

        /* 💡 종목(행) 간의 구분선 굵기 및 색상 강조 설정 */
        .custom-grid-table td {
            background-color: #0e1117 !important;
            color: #f3f4f6 !important;
            padding: 9px 10px !important; /* 패딩을 살짝 늘려 행 간격을 쾌적하게 조정 */
            border-bottom: 2px solid #2d3748 !important; /* 기존 1px에서 2px 굵기로 변경하여 구분감 강화 */
            border-right: 1px solid #1e242c !important;
            white-space: nowrap !important;
            text-align: center !important;
            font-variant-numeric: tabular-nums !important;
            position: relative;
        }

        .custom-grid-table th.sortable-th {
            cursor: pointer !important;
            transition: background-color 0.15s ease, color 0.15s ease;
        }
        .custom-grid-table th.sortable-th:hover {
            background-color: #1f242e !important;
            color: #60a5fa !important;
        }

        .sort-indicator {
            display: inline-block;
            margin-left: 2px;
            font-size: 0.72rem;
            color: #60a5fa;
            vertical-align: middle;
        }

        .custom-grid-table tr:hover td {
            background-color: rgba(255, 255, 255, 0.03) !important;
        }
        .custom-grid-table tr:hover td.col-name,
        .custom-grid-table tr:hover td.col-chk {
            background-color: #161a22 !important;
        }

        .naver-pc-link {
            color: #58a6ff !important;
            text-decoration: none !important;
        }
        .naver-pc-link:hover {
            text-decoration: underline !important;
            color: #79b8ff !important;
        }

        .stock-checkbox,
        .header-select-all {
            cursor: pointer;
            width: 16px;
            height: 16px;
            accent-color: #3b82f6;
            vertical-align: middle;
        }
        </style>
    """, unsafe_allow_html=True)

def render_multi_header_table(df, *args, **kwargs):
    # (이하 기존 함수 및 렌더링 코드 유지)
