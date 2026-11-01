import re
import streamlit as st
import pandas as pd

from styles import render_table
from store import SAVE_FILE, WATCHLIST_FILE, read_codes, write_codes, qp_codes, qp_clear

BASIC_COLS = [
    {"key": "종목명", "label": "종목명", "name": True, "link": True},
    {"key": "현재가", "label": "현재가"},
    {"key": "시총", "label": "시총"},
    {"key": "현재 PER", "label": "현재 PER"},
    {"key": "현재 PBR", "label": "현재 PBR"},
    {"key": "DPS(원)", "label": "DPS(원)"},
    {"key": "배당수익률", "label": "배당수익률"},
]


def _add_codes(new_codes, msg):
    current = read_codes(SAVE_FILE)
    fresh = [c for c in dict.fromkeys(new_codes) if c not in current]
    if fresh:
        write_codes(SAVE_FILE, current + fresh, msg)
    return len(fresh)


def render_tab_basic(df, master_full, current_codes):
    sel = qp_codes("sel_price")

    # 상단: 관심종목 추가
    _, c_add = st.columns([4.2, 1.8])
    with c_add:
        if st.button("⭐ 관심종목 추가", type="primary", use_container_width=True, key="btn_add_wl"):
            if not sel:
                st.warning("⚠️ 체크박스로 선택된 종목이 없습니다.")
            else:
                wl = read_codes(WATCHLIST_FILE)
                new = [c for c in sel if c not in wl]
                if new:
                    write_codes(WATCHLIST_FILE, wl + new, f"Auto-commit watchlist ({len(wl) + len(new)} stocks)")
                    qp_clear("sel_price")
                    st.toast(f"{len(new)}개 종목을 관심종목에 추가했습니다.")
                    st.rerun()
                else:
                    st.info("선택한 종목이 이미 모두 관심종목에 등록되어 있습니다.")

    render_table(df, BASIC_COLS, "tab_basic", has_checkbox=True,
                 sel_param="sel_price", selected=sel,
                 empty_msg="표시할 현재 시세 데이터가 없습니다.")

    # 하단: 삭제 / CSV / TXT 백업
    st.write("")
    c_del, c_csv, c_bak = st.columns([1.6, 2.2, 1.8])
    with c_del:
        if st.button("🗑️ 선택 종목 삭제", type="primary", use_container_width=True, key="btn_del_basic"):
            if not sel:
                st.warning("삭제할 종목의 체크박스를 먼저 선택해 주세요.")
            else:
                remain = [c for c in current_codes if c not in sel]
                write_codes(SAVE_FILE, remain, f"Auto-commit saved_codes.txt ({len(remain)} stocks)")
                qp_clear("sel_price")
                st.toast(f"종목 {len(sel)}개를 삭제했습니다.")
                st.rerun()
    with c_csv:
        export = master_full.drop(columns=[c for c in master_full.columns if c.startswith("_")])
        st.download_button(
            "📥 전체 결과 CSV 다운로드",
            data=export.to_csv(index=False).encode("utf-8-sig"),
            file_name="종목Scan_비교결과.csv",
            mime="text/csv",
            use_container_width=True,
            key="btn_down_csv_basic",
        )
    with c_bak:
        st.download_button(
            "📋 종목코드 백업(TXT)",
            data="\n".join(current_codes).encode("utf-8"),
            file_name="saved_codes_backup.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_down_txt_basic",
        )

    # 종목 추가 도구
    st.write("")
    show_add_box = st.toggle("➕ 종목코드 추가 및 일괄 등록 (파일 / 텍스트 입력)", value=False, key="tg_add_codes")
    if show_add_box:
        with st.container():
            tab_single, tab_text, tab_file = st.tabs(["단건 추가", "텍스트 일괄 붙여넣기", "파일 일괄 업로드(TXT/CSV/XLSX)"])

            with tab_single:
                c1, c2 = st.columns([3, 1])
                with c1:
                    new_code = st.text_input("종목코드 (6자리)", placeholder="예: 005930 (삼성전자)",
                                             max_chars=6, key="single_code_input")
                with c2:
                    st.write("")
                    if st.button("종목 추가", use_container_width=True, key="btn_single_add"):
                        code = new_code.strip().zfill(6)
                        if code.isdigit():
                            n = _add_codes([code], f"Auto-commit saved_codes.txt (+{code})")
                            if n:
                                st.toast(f"{code} 추가 완료")
                                st.rerun()
                            else:
                                st.info("이미 등록된 종목코드입니다.")

            with tab_text:
                bulk_text = st.text_area(
                    "종목코드 목록 붙여넣기 (줄바꿈, 쉼표, 공백 구분)",
                    placeholder="예시:\n005930\n000660, 035420 035720",
                    height=120, key="area_bulk_codes",
                )
                if st.button("📥 텍스트 목록 일괄 추가", type="primary", key="btn_bulk_text_add"):
                    found = [c.zfill(6) for c in re.findall(r"\d{1,6}", bulk_text)]
                    if not found:
                        st.warning("유효한 6자리 종목코드를 찾을 수 없습니다.")
                    else:
                        n = _add_codes(found, "Auto-commit saved_codes.txt (bulk text)")
                        if n:
                            st.toast(f"총 {n}개 종목이 추가되었습니다.")
                            st.rerun()
                        else:
                            st.info("입력된 종목코드가 이미 모두 등록되어 있습니다.")

            with tab_file:
                up_file = st.file_uploader("종목코드가 포함된 파일 업로드",
                                           type=["txt", "csv", "xlsx", "xls"],
                                           key="stock_code_file_uploader")
                if up_file is not None and st.button("📥 파일에서 종목코드 일괄 추출/추가",
                                                     type="primary", key="btn_bulk_file_add"):
                    try:
                        raw = up_file.getvalue()
                        extracted = []
                        if up_file.name.endswith(".txt"):
                            text = raw.decode("utf-8", errors="ignore")
                            extracted = [c.zfill(6) for c in re.findall(r"\d{1,6}", text)]
                        else:
                            import io
                            if up_file.name.endswith((".xlsx", ".xls")):
                                df_file = pd.read_excel(io.BytesIO(raw), dtype=str)
                            else:
                                df_file = pd.read_csv(io.BytesIO(raw), dtype=str)
                            for col in df_file.columns:
                                for val in df_file[col].dropna().astype(str):
                                    digits = re.sub(r"[^0-9]", "", val)
                                    if 1 <= len(digits) <= 6:
                                        extracted.append(digits.zfill(6))
                        if extracted:
                            n = _add_codes(extracted, "Auto-commit saved_codes.txt (file)")
                            if n:
                                st.toast(f"파일에서 {n}개 종목이 등록되었습니다.")
                                st.rerun()
                            else:
                                st.info("파일의 종목이 이미 모두 등록되어 있습니다.")
                        else:
                            st.warning("파일 내에서 유효한 종목코드를 추출하지 못했습니다.")
                    except Exception as e:
                        st.error(f"파일 처리 중 오류 발생: {e}")
