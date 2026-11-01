import streamlit as st

from styles import render_table
from data import build_watchlist
from store import (
    SAVE_FILE, WATCHLIST_FILE, read_codes, write_codes,
    qp_codes, qp_clear, load_text,
)

WATCH_COLS = [
    {"key": "종목명", "label": "종목명", "name": True, "link": True},
    {"key": "현재가", "label": "현재가"},
    {"key": "시총", "label": "시총"},
    {"key": "적용연도", "label": "적용연도"},
    {"key": "PER", "label": "PER"},
    {"key": "PBR", "label": "PBR"},
    {"key": "ROE", "label": "ROE"},
    {"key": "배당금", "label": "배당금"},
    {"key": "매출액", "label": "매출액"},
    {"key": "영업익", "label": "영업익"},
    {"key": "당기순이익", "label": "당기순이익"},
]


def _merge_into(target_file, new_codes, msg):
    current = read_codes(target_file)
    fresh = [c for c in dict.fromkeys(new_codes) if c not in current]
    if fresh:
        write_codes(target_file, current + fresh, msg)
    return len(fresh)


def render_tab_watchlist():
    codes = read_codes(WATCHLIST_FILE)

    if codes:
        df = build_watchlist(codes)
        sel = qp_codes("sel_wl")

        render_table(
            df, WATCH_COLS, "tab_watchlist",
            key_col="종목코드",
            has_checkbox=True,
            sel_param="sel_wl",
            selected=sel,
            merge_cols=["종목명", "현재가", "시총"],   # 종목 2줄을 한 칸으로 병합
            empty_msg="관심종목 시세를 불러오지 못했습니다.",
        )

        st.write("")
        _, c_r = st.columns([3, 1.8])
        with c_r:
            if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True, key="btn_del_wl"):
                if not sel:
                    st.warning("⚠️ 삭제할 종목의 체크박스를 먼저 선택해 주세요.")
                else:
                    remain = [c for c in codes if c not in sel]
                    write_codes(WATCHLIST_FILE, remain, f"Auto-commit watchlist ({len(remain)} stocks)")
                    qp_clear("sel_wl")
                    st.toast(f"선택한 종목({len(sel)}개) 삭제 완료")
                    st.rerun()
    else:
        st.info("등록된 관심종목이 없습니다. 아래 토글을 켜서 종목코드를 추가해 주세요.")

    st.write("---")

    show_manage = st.toggle("➕ 종목코드 추가 및 관리", value=False, key="toggle_watchlist_manage")
    if not show_manage:
        return

    with st.container(border=True):
        # 현재시세 탭에서 체크한 종목 가져오기
        if st.button("📥 현재시세 탭에서 체크된 종목 가져오기", use_container_width=True, key="btn_import_wl"):
            picked = qp_codes("sel_price")
            if not picked:
                st.warning("⚠️ 현재시세 탭에서 체크박스로 선택된 종목이 없습니다.")
            else:
                n = _merge_into(WATCHLIST_FILE, picked, "Auto-commit watchlist (import)")
                qp_clear("sel_price")
                if n:
                    st.toast(f"총 {n}개의 종목이 관심종목에 추가되었습니다!")
                    st.rerun()
                else:
                    st.info("선택한 종목이 이미 모두 관심종목에 등록되어 있습니다.")

        st.markdown("---")

        # 백업 / 복구
        st.caption("📂 관심종목 백업 파일(TXT) 관리")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="💾 백업 파일 다운로드",
                data="\n".join(codes).encode("utf-8") + (b"\n" if codes else b""),
                file_name="watchlist_codes.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_wl_backup",
            )
        with d_col2:
            up = st.file_uploader("백업 파일 업로드 (복구)", type=["txt"],
                                  label_visibility="collapsed", key="wl_upload")
            if up is not None and st.button("📥 업로드 파일로 복구", use_container_width=True, key="btn_wl_restore"):
                try:
                    lines = up.getvalue().decode("utf-8").splitlines()
                    restored = [l.strip().zfill(6) for l in lines if l.strip().isdigit()]
                    if restored:
                        write_codes(WATCHLIST_FILE, restored, f"Auto-commit watchlist (restore {len(restored)})")
                        st.toast(f"총 {len(restored)}개 종목 복구 완료!")
                        st.rerun()
                    else:
                        st.warning("⚠️ 업로드한 파일에 올바른 종목 코드가 없습니다.")
                except Exception as e:
                    st.error(f"⚠️ 파일 처리 중 오류 발생: {e}")

        st.markdown("---")

        # 직접 입력
        st.caption("6자리 종목코드를 직접 입력하여 관심종목에 추가할 수 있습니다.")
        a1, a2 = st.columns([3, 1])
        with a1:
            input_code = st.text_input("종목코드 입력", placeholder="예: 005930 (삼성전자)",
                                       label_visibility="collapsed", key="input_new_watchlist_code")
        with a2:
            if st.button("종목 추가", use_container_width=True, type="primary", key="btn_wl_add"):
                code = input_code.strip().zfill(6)
                if code.isdigit() and len(code) == 6:
                    n = _merge_into(WATCHLIST_FILE, [code], f"Auto-commit watchlist (+{code})")
                    if n:
                        st.toast(f"종목코드({code})가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.warning("⚠️ 이미 관심종목에 등록된 코드입니다.")
                else:
                    st.error("⚠️ 올바른 6자리 숫자 종목코드를 입력해주세요.")
