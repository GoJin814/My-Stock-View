import re
import json
import html as _html

import numpy as np
import pandas as pd
import streamlit as st

from store import (
    MARKET_CACHE_FILE, THRESHOLDS_FILE,
    load_json, save_json,
)
from tabs.sel_table import selectable_table

DEFAULT_TH = {"use_pbr": True, "pbr": 0.90, "use_dep": True, "dep": 2.50, "use_crd": True, "crd": 0.85}

MARKET_CSS = (
    "<style>"
    "table.mk-table{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;"
    "font-size:0.82rem;color:#f3f4f6;background:#0e1117;"
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;}"
    "table.mk-table th{position:sticky;top:0;z-index:10;background:#161a22;color:#9ca3af;font-weight:500;"
    "font-size:0.81rem;padding:6px 10px;border-bottom:2px solid #334155;border-right:1px solid #262c36;"
    "text-align:center;white-space:nowrap;vertical-align:middle;}"
    "table.mk-table td{background:#0e1117;padding:8px 10px;border-right:1px solid #1e242c;"
    "border-bottom:1px solid #1e242c;text-align:right;white-space:nowrap;vertical-align:middle;"
    "font-variant-numeric:tabular-nums;}"
    "table.mk-table .c-chk{position:sticky;left:0;z-index:5;width:34px;min-width:34px;max-width:34px;"
    "padding:6px 0;text-align:center;}"
    "table.mk-table th.c-chk{z-index:100;background:#161a22;}"
    "table.mk-table .c-date{position:sticky;left:34px;z-index:5;text-align:center;}"
    "table.mk-table th.c-date{z-index:100;background:#161a22;}"
    "table.mk-table td.hl{color:#ff4b4b !important;font-weight:700;}"
    "table.mk-table input[type=checkbox]{cursor:pointer;width:16px;height:16px;accent-color:#3b82f6;vertical-align:middle;}"
    "</style>"
)

MARKET_COLS = ["일시", "KOSPI", "시가총액 (억원)", "PER", "PBR", "예탁금 비율",
               "신용잔고 비율", "고객예탁금 (억원)", "신용잔고 (억원)", "환율"]


def to_clean_num(val):
    if val is None or str(val).strip() in ("", "-", "N/A", "nan", "None"):
        return np.nan
    try:
        cleaned = re.sub(r"[^0-9.-]", "", str(val))
        return float(cleaned) if cleaned else np.nan
    except Exception:
        return np.nan


def format_with_commas(val, is_float=False, decimal_places=2):
    if val is None or str(val).strip() in ("", "-", "N/A", "nan", "None"):
        return "-"
    num = to_clean_num(val)
    if pd.isna(num):
        return str(val).strip()
    if is_float:
        return f"{num:,.{decimal_places}f}"
    return f"{int(round(num)):,}"


def normalize_date(val):
    if not val or pd.isna(val):
        return ""
    val_str = str(val).strip()
    parsed = pd.to_datetime(val_str, errors="coerce")
    if pd.notnull(parsed):
        return parsed.strftime("%Y-%m-%d")
    digits = re.sub(r"[^0-9]", "", val_str)
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return val_str


def load_market_cache():
    return load_json(MARKET_CACHE_FILE, {})


def save_market_cache(cache):
    save_json(MARKET_CACHE_FILE, cache, "Auto-commit market_indices_cache.json")


def load_market_thresholds():
    saved = load_json(THRESHOLDS_FILE, {})
    out = dict(DEFAULT_TH)
    out.update({k: v for k, v in saved.items() if k in DEFAULT_TH})
    return out


def save_market_thresholds(th):
    save_json(THRESHOLDS_FILE, th, "Auto-commit market_thresholds.json")


def _market_html(df, prev_sel, hl):
    head = (
        '<th class="c-chk"><input type="checkbox" class="header-select-all" title="전체 선택"></th>'
        + "".join(
            f'<th class="{"c-date" if c == "일시" else ""}">{_html.escape(c)}</th>'
            for c in MARKET_COLS
        )
    )
    body = []
    for _, r in df.iterrows():
        key = str(r["_key"])
        chk = " checked" if key in prev_sel else ""
        body.append("<tr>")
        body.append(
            f'<td class="c-chk"><input type="checkbox" class="stock-checkbox" '
            f'data-code="{_html.escape(key)}"{chk}></td>'
        )
        for c in MARKET_COLS:
            cls = []
            if c == "일시":
                cls.append("c-date")
            if hl(r, c):
                cls.append("hl")
            body.append(f'<td class="{" ".join(cls)}">{_html.escape(str(r[c]))}</td>')
        body.append("</tr>")

    return (
        MARKET_CSS
        + '<div class="mk-wrap"><table class="mk-table">'
        + f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    )


def render_tab_market():
    m_cache = load_market_cache()
    if not m_cache:
        st.info("기록된 국내지수 데이터가 없습니다. 아래 패널에서 수기로 등록하거나 CSV/Excel 파일을 업로드해 주세요.")
        return

    saved = load_market_thresholds()
    th = dict(saved)

    show_hl = st.toggle("🚨 주요 지표 범위", value=False, key="tg_market_hl")
    if show_hl:
        with st.container():
            st.markdown('<div class="filter-container-box">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                th["use_pbr"] = st.checkbox("PBR", value=saved["use_pbr"], key="cfg_use_pbr")
                th["pbr"] = st.number_input("상한선", value=float(saved["pbr"]), step=0.05,
                                            format="%.2f", disabled=not th["use_pbr"], key="cfg_val_pbr")
            with c2:
                th["use_dep"] = st.checkbox("예탁금", value=saved["use_dep"], key="cfg_use_dep")
                th["dep"] = st.number_input("하한선 (%)", value=float(saved["dep"]), step=0.10,
                                            format="%.2f", disabled=not th["use_dep"], key="cfg_val_dep")
            with c3:
                th["use_crd"] = st.checkbox("신용잔고", value=saved["use_crd"], key="cfg_use_crd")
                th["crd"] = st.number_input("하한선 (%)", value=float(saved["crd"]), step=0.05,
                                            format="%.2f", disabled=not th["use_crd"], key="cfg_val_crd")
            st.markdown('</div>', unsafe_allow_html=True)

    new_th = {k: (bool(v) if k.startswith("use_") else round(float(v), 2)) for k, v in th.items()}
    if new_th != saved:
        save_market_thresholds(new_th)
    th = new_th

    recs = []
    for d in sorted(m_cache.keys(), reverse=True):
        item = m_cache[d]
        raw_mcap = item.get("시가총액(억원)", "-")
        raw_dep = item.get("고객예탁금(억원)", "-")
        raw_crd = item.get("신용잔고(억원)", "-")
        raw_kospi = item.get("KOSPI", "-")
        raw_fx = item.get("환율", item.get("환율(원)", "-"))
        raw_pbr = item.get("PBR", item.get("pbr", item.get("KOSPI_PBR_최근", "-")))

        num_mcap = to_clean_num(raw_mcap)
        num_dep = to_clean_num(raw_dep)
        num_crd = to_clean_num(raw_crd)
        num_pbr = to_clean_num(raw_pbr)

        if pd.notna(num_dep) and pd.notna(num_mcap) and num_mcap > 0:
            dep_ratio = round(num_dep / num_mcap * 100.0, 2)
            dep_str = f"{dep_ratio:.2f}%"
        else:
            dep_ratio, dep_str = np.nan, "-"

        if pd.notna(num_crd) and pd.notna(num_mcap) and num_mcap > 0:
            crd_ratio = round(num_crd / num_mcap * 100.0, 2)
            crd_str = f"{crd_ratio:.2f}%"
        else:
            crd_ratio, crd_str = np.nan, "-"

        recs.append({
            "_key": d,
            "일시": str(d).replace("-", "/"),
            "KOSPI": format_with_commas(raw_kospi, is_float=True, decimal_places=2),
            "시가총액 (억원)": format_with_commas(raw_mcap),
            "PER": str(item.get("PER", item.get("per", item.get("KOSPI_PER_최근", "-")))),
            "PBR": str(raw_pbr),
            "예탁금 비율": dep_str,
            "신용잔고 비율": crd_str,
            "고객예탁금 (억원)": format_with_commas(raw_dep),
            "신용잔고 (억원)": format_with_commas(raw_crd),
            "환율": format_with_commas(raw_fx, is_float=True, decimal_places=1),
            "_num_pbr": num_pbr,
            "_num_dep": dep_ratio,
            "_num_crd": crd_ratio,
        })
    df = pd.DataFrame(recs)

    def hl(r, col):
        if col == "PBR" and th["use_pbr"] and pd.notna(r["_num_pbr"]) \
                and 0 <= r["_num_pbr"] <= th["pbr"]:
            return True
        if col == "예탁금 비율" and th["use_dep"] and pd.notna(r["_num_dep"]) \
                and r["_num_dep"] >= th["dep"]:
            return True
        if col == "신용잔고 비율" and th["use_crd"] and pd.notna(r["_num_crd"]) \
                and r["_num_crd"] >= th["crd"]:
            return True
        return False

    prev_sel = set(st.session_state.get("mkt_sel", []) or [])
    html = _market_html(df, prev_sel, hl)
    selected = selectable_table(html, key="mkt_sel", frame_h=620) or []

    st.write("")
    c_del, c_dl = st.columns([1, 1.3])
    with c_del:
        if st.button("🗑️ 선택 일자 지수 삭제", type="primary", use_container_width=True, key="btn_del_market"):
            targets = [k for k in dict.fromkeys(selected) if k in m_cache]
            if not targets:
                st.warning("삭제할 일자의 체크박스를 먼저 선택해 주세요.")
            else:
                for k in targets:
                    del m_cache[k]
                save_market_cache(m_cache)
                st.toast(f"{len(targets)}개 일자 지수 삭제 완료")
                st.rerun()
    with c_dl:
        st.download_button(
            "💾 국내지수 전체 백업(JSON 다운로드)",
            data=json.dumps(m_cache, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="market_indices_backup.json",
            mime="application/json",
            use_container_width=True,
            key="dl_market_backup",
        )


def render_market_inputs():
    show_input = st.toggle("🌐 국내지수 데이터 수기 등록 / 파일 업로드(CSV / Excel) / 복원",
                           value=False, key="tg_market_input")
    if not show_input:
        return

    with st.container():
        t_manual, t_upload, t_restore = st.tabs(
            ["✍️ 개별 수기 입력", "📊 CSV / Excel 파일 일괄 업로드", "📂 백업 파일(JSON) 복원"]
        )

        # ---- 수기 입력 ----
        with t_manual:
            c_date, _ = st.columns([2, 4])
            with c_date:
                input_date = st.date_input("기준 일자", key="market_input_date")
            date_str = str(input_date)

            st.write("**KOSPI 및 시장 매크로 데이터 입력**")
            r1 = st.columns(3)
            with r1[0]:
                in_kospi = st.text_input("KOSPI 지수", placeholder="예: 2528.92", key="man_kospi")
            with r1[1]:
                in_mcap = st.text_input("시가총액(억원)", placeholder="예: 20,712,779", key="man_mcap")
            with r1[2]:
                in_fx = st.text_input("환율", placeholder="예: 1455.5", key="man_fx")

            r2 = st.columns(4)
            with r2[0]:
                in_per = st.text_input("PER", placeholder="예: 13.32", key="man_per")
            with r2[1]:
                in_pbr = st.text_input("PBR", placeholder="예: 0.89", key="man_pbr")
            with r2[2]:
                in_deposit = st.text_input("고객예탁금(억원)", placeholder="예: 572,328", key="man_deposit")
            with r2[3]:
                in_credit = st.text_input("신용잔고(억원)", placeholder="예: 181,786", key="man_credit")

            if st.button("📌 수기 데이터 저장", type="primary", key="btn_save_market"):
                cache = load_market_cache()
                cache.setdefault(date_str, {})
                cache[date_str].update({
                    "KOSPI": format_with_commas(in_kospi, is_float=True, decimal_places=2),
                    "시가총액(억원)": format_with_commas(in_mcap),
                    "PER": str(in_per).strip() or "-",
                    "PBR": str(in_pbr).strip() or "-",
                    "고객예탁금(억원)": format_with_commas(in_deposit),
                    "신용잔고(억원)": format_with_commas(in_credit),
                    "환율": format_with_commas(in_fx, is_float=True, decimal_places=1),
                })
                save_market_cache(cache)
                st.toast(f"{date_str} KOSPI 데이터 저장 완료")
                st.rerun()

        # ---- CSV / Excel 업로드 ----
        with t_upload:
            st.write("보유하고 계신 **CSV 또는 Excel(.xlsx)** 파일을 업로드하면 날짜별 데이터가 자동으로 병합/추가됩니다.")
            market_file = st.file_uploader(
                "지수 데이터 파일 선택 (일시, KOSPI, 시가총액, PER, PBR 등)",
                type=["csv", "xlsx", "xls"], key="market_csv_excel_uploader",
            )
            if market_file is not None and st.button("📥 파일 데이터 읽어서 추가하기",
                                                    type="primary", key="btn_apply_market_file"):
                try:
                    if market_file.name.endswith(".csv"):
                        try:
                            df_up = pd.read_csv(market_file, encoding="utf-8")
                        except UnicodeDecodeError:
                            market_file.seek(0)
                            df_up = pd.read_csv(market_file, encoding="cp949")
                    else:
                        df_up = pd.read_excel(market_file)

                    df_up.columns = [str(c).replace(" ", "").strip() for c in df_up.columns]
                    date_col = next((c for c in df_up.columns
                                     if any(k in c for k in ["일시", "날짜", "Date", "DATE"])), None)
                    if not date_col:
                        st.error("파일에서 '일시' 또는 '날짜' 컬럼을 찾을 수 없습니다.")
                    else:
                        cache = load_market_cache()
                        added = 0
                        for _, r in df_up.iterrows():
                            d_str = normalize_date(str(r[date_col]).strip())
                            if not d_str:
                                continue
                            cache.setdefault(d_str, {})
                            for col in df_up.columns:
                                if col == date_col:
                                    continue
                                val_str = str(r[col]).strip()
                                if val_str in ("nan", "None", ""):
                                    val_str = "-"
                                if "시가총액" in col:
                                    cache[d_str]["시가총액(억원)"] = format_with_commas(val_str)
                                elif "예탁금" in col:
                                    cache[d_str]["고객예탁금(억원)"] = format_with_commas(val_str)
                                elif "신용잔고" in col or "신용융자" in col:
                                    cache[d_str]["신용잔고(억원)"] = format_with_commas(val_str)
                                elif "환율" in col:
                                    cache[d_str]["환율"] = format_with_commas(val_str, is_float=True, decimal_places=1)
                                elif col.upper() == "PER":
                                    cache[d_str]["PER"] = val_str
                                elif col.upper() == "PBR":
                                    cache[d_str]["PBR"] = val_str
                                elif col in ("KOSPI", "코스피"):
                                    cache[d_str]["KOSPI"] = format_with_commas(val_str, is_float=True, decimal_places=2)
                                else:
                                    cache[d_str][col] = val_str
                            added += 1
                        save_market_cache(cache)
                        st.toast(f"총 {added}개 일자의 지수 데이터가 반영되었습니다!")
                        st.rerun()
                except Exception as e:
                    st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")

        # ---- JSON 복원 ----
        with t_restore:
            up_json = st.file_uploader("백업받은 market_indices_backup.json 업로드",
                                       type=["json"], key="json_backup_restore")
            if up_json is not None and st.button("📥 백업 데이터 즉시 복원", type="primary", key="btn_restore_json"):
                try:
                    content = json.loads(up_json.getvalue().decode("utf-8"))
                    if isinstance(content, dict):
                        cache = load_market_cache()
                        cache.update(content)
                        save_market_cache(cache)
                        st.toast(f"총 {len(content)}일자의 지수 데이터가 복원되었습니다.")
                        st.rerun()
                    else:
                        st.error("올바른 JSON 형식의 백업 파일이 아닙니다.")
                except Exception as e:
                    st.error(f"복원 중 오류 발생: {e}")
