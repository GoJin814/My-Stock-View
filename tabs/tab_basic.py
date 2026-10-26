import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from styles import render_multi_header_table

def render_tab_basic(df_basic):
    if df_basic is None or df_basic.empty:
        st.info("표시할 현재 시세 데이터가 없습니다.")
        return None

    df_display = df_basic.copy()

    # 1. HTML 그리드 렌더링 (전 탭 정렬 연동 + 네이버 증권 링크 + 체크박스)
    render_multi_header_table(
        df_display,
        tab_name="tab_basic",
        has_naver_link=True,
        has_checkbox=True
    )

    # 2. ⚡ 체크된 종목 코드를 삭제 버튼 클릭 즉시 Python 세션으로 가로채는 자바스크립트 엔진
    components.html("""
    <script>
    (function setupDeleteBridge() {
        const doc = window.parent.document;
        const win = window.parent;
        if (!doc || !win) return;

        // 전체 선택 체크박스 동작 바인딩
        const headChk = doc.querySelector('#table_tab_basic .header-select-all');
        if (headChk) {
            headChk.onclick = function() {
                const checked = this.checked;
                doc.querySelectorAll('#table_tab_basic .stock-checkbox').forEach(cb => {
                    cb.checked = checked;
                });
            };
        }

        // 삭제 버튼을 눌렀을 때 현재 체크된 data-code 값들을 URL에 심어 Python으로 직결
        doc.addEventListener('click', function(e) {
            const btn = e.target.closest('button');
            if (btn && btn.innerText.includes('선택 종목 삭제')) {
                const checkedCodes = [];
                doc.querySelectorAll('#table_tab_basic .stock-checkbox:checked').forEach(cb => {
                    const c = cb.getAttribute('data-code');
                    if (c && c.length === 6) {
                        checkedCodes.push(c);
                    }
                });

                if (checkedCodes.length > 0) {
                    try {
                        const url = new URL(win.location.href);
                        url.searchParams.set('del_targets', checkedCodes.join(','));
                        win.history.replaceState(null, '', url.toString());
                    } catch (err) {}
                }
            }
        }, true);
    })();
    </script>
    """, height=0, width=0)

    return df_display
