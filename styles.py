import streamlit as st
import pandas as pd

def apply_custom_styles():
    # 1. 디자인 스타일 및 모바일 터치 새로고침(Pull-to-Refresh) 자바스크립트 주입
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

        /* 좌측 고정 종목명 데이터 셀 (불투명 배경) */
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

        <script>
        (function() {
            let startY = 0;
            let isAtTop = false;

            const doc = window.parent.document || document;
            const container = doc.querySelector('[data-testid="stAppViewContainer"]') || window;

            doc.addEventListener('touchstart', function(e) {
                if (e.touches.length === 1) {
                    startY = e.touches[0].clientY;
                    // 최상단에 위치해 있는지 확인
                    const scrollTop = container.scrollTop !== undefined ? container.scrollTop : window.scrollY;
                    isAtTop = (scrollTop <= 5);
                }
            }, { passive: true });

            doc.addEventListener('touchend', function(e) {
                if (isAtTop && e.changedTouches.length === 1) {
                    const endY = e.changedTouches[0].clientY;
                    const diffY = endY - startY;

                    // 화면 최상단에서 아래로 75px 이상 시원하게 당겼을 때 새로고침 실행
                    if (diffY > 75) {
                        // 새로고침 표시용 토스트 메시지 생성
                        const toast = doc.createElement('div');
                        toast.innerText = '🔄 새로고침 중...';
                        toast.style.position = 'fixed';
                        toast.style.top = '20px';
                        toast.style.left = '50%';
                        toast.style.transform = 'translateX(-50%)';
                        toast.style.backgroundColor = '#1f2937';
                        toast.style.color = '#ffffff';
                        toast.style.padding = '8px 16px';
                        toast.style.borderRadius = '20px';
                        toast.style.fontSize = '14px';
                        toast.style.zIndex = '999999';
                        toast.style.boxShadow = '0 4px 6px rgba(0,0,0,0.2)';
                        doc.body.appendChild(toast);

                        setTimeout(function() {
                            window.parent.location.reload();
                        }, 250);
                    }
                }
            }, { passive: true });
        })();
        </script>
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
