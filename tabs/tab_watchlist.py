import os
import re
import base64
import html as _html
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests
import streamlit as st
from firebase_admin import db

from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num
from tabs.sel_table import selectable_table

WATCHLIST_FILE = "watchlist_codes.txt"
FB_WATCHLIST_PATH = "my_stock_view/watchlist_codes"

# 종목 1개당 행은 2개(직전/최근). 종목명·현재가(시총)·선택박스는 rowspan으로 한 칸만 그린다.
DATA_COLS = ["적용연도", "PER", "PBR", "ROE", "배당금", "매출액", "영업익", "당기순이익"]

GROUP_END_STYLE = "border-bottom:3px solid #64748b;"

WL_CSS = "".join([
    "<style>",
    ".wl-wrap{overflow:auto;max-height:70vh;margin-bottom:1.2rem;border:1px solid #334155;",
    "border-radius:4px;background:#0e1117;-webkit-overflow-scrolling:touch;}",
    "table.wl-table{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;",
    "font-size:0.82rem;color:#f3f4f6;background:#0e1117;",
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;}",
    # 일반 헤더/셀
    "table.wl-table th{position:sticky;top:0;z-index:10;background:#161a22;color:#9ca3af;",
    "font-weight:500;font-size:0.81rem;padding:6px 10px;border-bottom:2px solid #334155;",
    "border-right:1px solid #262c36;text-align:center;white-space:nowrap;vertical-align:middle;}",
    "table.wl-table td{background:#0e1117;padding:8px 10px;border-right:1px solid #1e242c;",
    "border-bottom:1px solid #1e242c;text-align:center;white-space:nowrap;vertical-align:middle;",
    "font-variant-numeric:tabular-nums;}",
    # 고정 열 공통
    "table.wl-table .c-chk,table.wl-table .c-name,table.wl-table .c-price{",
    "position:sticky;z-index:5;background:#0e1117;box-sizing:border-box;}",
    "table.wl-table th.c-chk,table.wl-table th.c-name,table.wl-table th.c-price{z-index:100;background:#161a22;}",
    # 체크박스: 34px (left 0)
    "table.wl-table .c-chk{left:0;width:34px;min-width:34px;max-width:34px;padding:6px 0;}",
    # 종목명: 한글 5글자 폭 (left 34px), 넘치면 글자 단위로 줄바꿈
    "table.wl-table .c-name{left:34px;width:calc(5em + 14px);min-width:calc(5em + 14px);",
    "max-width:calc(5em + 14px);padding:8px 6px 8px 8px;text-align:left;",
    "white-space:normal;word-break:break-all;line-height:1.3;}",
    # 현재가/시총: 값 폭에 맞춤 (left = 체크박스 34px + 종목명 폭)
    "table.wl-table .c-price{left:calc(34px + 5em + 14px);width:calc(6em + 12px);",
    "min-width:calc(6em + 12px);max-width:calc(6em + 12px);padding:8px 6px;",
    "box-shadow:2px 0 0 #334155;}",
    "table.wl-table .c-code{color:#94a3b8;font-family:monospace;font-size:0.72rem;margin-top:2px;}",
    "table.wl-table .c-mcap{color:#94a3b8;font-size:inherit;margin-top:3px;}",
    "table.wl-table a.naver-link{color:#58a6ff !important;text-decoration:none !important;}",
    "table.wl-table a.naver-link:hover{text-decoration:underline !important;}",
    "table.wl-table input[type=checkbox]{cursor:pointer;width:16px;height:16px;accent-color:#3b82f6;vertical-align:middle;}",
    "</style>",
])


def _dedupe(codes):
    out = []
    for c in codes:
        s = str(c).strip()
        if s.isdigit():
            z = s.zfill(6)
            if z not in out:
                out.append(z)
    return out


def commit_to_github(filename, content_str, commit_message="Auto-update watchlist from Streamlit"):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    if not token or not repo:
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        res = requests.get(url, headers=headers, params={"ref": branch}, timeout=7)
        sha = res.json().get("sha") if res.status_code == 200 else None
        payload = {
            "message": commit_message,
            "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        put_res = requests.put(url, headers=headers, json=payload, timeout=7)
        return put_res.status_code in [200, 201]
    except Exception:
        return False


def load_watchlist_codes():
    """Firebase를 우선으로 읽고, 없으면 로컬 파일을 사용한다."""
    try:
        v = db.reference(FB_WATCHLIST_PATH).get()
        if isinstance(v, list):
            return _dedupe(v)
    except Exception:
        pass

    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return _dedupe(f.readlines())
        except Exception:
            pass
    return []


def save_watchlist_codes(codes):
    cleaned = _dedupe(codes)
    try:
        db.reference(FB_WATCHLIST_PATH).set(cleaned if cleaned else None)
    except Exception as e:
        st.error(f"⚠️ Firebase 저장 실패: {e}")

    content = "\n".join(cleaned) + ("\n" if cleaned else "")
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    commit_to_github(WATCHLIST_FILE, content, f"Auto-commit watchlist_codes.txt ({len(cleaned)} stocks)")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_watchlist_item(code: str):
    """종목 1개에 대해 최근 2개년 행을 반환한다. [직전연도행, 최근연도행]"""
    basic = fetch_basic(code)
    integration = fetch_integration(code)
    fin_json = fetch_finance(code)

    stock_name = basic.get("stockName", "")
    if not stock_name or stock_name == "-":
        stock_name = ""

    raw_close = basic.get("closePrice", "")
    if not raw_close or raw_close == "-":
        curr_price_str = ""
    else:
        curr_price_str = f"{raw_close}원" if "원" not in str(raw_close) else str(raw_close)

    market_cap = ""
    for item in integration.get("totalInfos", []):
        if str(item.get("code", "")).strip() == "marketValue" or str(item.get("key", "")).strip() in ["시총", "시가총액"]:
            val = str(item.get("value", "")).strip()
            if val and val != "-":
                market_cap = val
            break

    fin_info = {
        "prev_yr": "", "latest_yr": "",
        "prev_per": np.nan, "cur_per": np.nan,
        "prev_pbr": np.nan, "cur_pbr": np.nan,
        "prev_roe": np.nan, "cur_roe": np.nan,
        "prev_rev": np.nan, "cur_rev": np.nan,
        "prev_op": np.nan, "cur_op": np.nan,
        "prev_np": np.nan, "cur_np": np.nan,
        "prev_dps": np.nan, "cur_dps": np.nan,
    }

    def _yr(k):
        m = re.search(r"(20\d{2})", str(k))
        return f"{m.group(1)}년" if m else ""

    for row in extract_row_list(fin_json) or []:
        raw_title = str(row.get("title", "")).strip().replace(" ", "")
        columns = row.get("columns", {}) or {}
        if not columns:
            continue

        by_year = {}
        for k in columns.keys():
            m = re.search(r"(20\d{2})", str(k))
            if m:
                by_year[m.group(1)] = k
        if not by_year:
            continue

        years = sorted(by_year)
        latest_k = by_year[years[-1]]
        prev_k = by_year[years[-2]] if len(years) >= 2 else None

        fin_info["latest_yr"] = _yr(latest_k)
        fin_info["prev_yr"] = _yr(prev_k) if prev_k else ""

        c_item = columns.get(latest_k, {})
        c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)
        p_val = np.nan
        if prev_k:
            p_item = columns.get(prev_k, {})
            p_val = to_num(p_item.get("value") if isinstance(p_item, dict) else p_item)

        if raw_title in ["매출액", "수익"]:
            fin_info["cur_rev"], fin_info["prev_rev"] = c_val, p_val
        elif raw_title == "영업이익":
            fin_info["cur_op"], fin_info["prev_op"] = c_val, p_val
        elif raw_title in ["당기순이익", "당기순익"]:
            fin_info["cur_np"], fin_info["prev_np"] = c_val, p_val
        elif "ROE" in raw_title:
            fin_info["cur_roe"], fin_info["prev_roe"] = c_val, p_val
        elif "PER" in raw_title:
            fin_info["cur_per"], fin_info["prev_per"] = c_val, p_val
        elif "PBR" in raw_title:
            fin_info["cur_pbr"], fin_info["prev_pbr"] = c_val, p_val
        elif any(k in raw_title for k in ["주당배당금", "DPS"]):
            fin_info["cur_dps"], fin_info["prev_dps"] = c_val, p_val

    def fmt_val(v, suffix=""):
        if v is None or pd.isna(v):
            return "-"
        return f"{v:,.0f}{suffix}"

    def fmt_rate(v):
        if v is None or pd.isna(v):
            return "-"
        return f"{v:.2f}%"

    def fmt_multi(v):
        if v is None or pd.isna(v):
            return "-"
        return f"{v:.2f}배"

    numeric_close = to_num(raw_close)

    def fmt_dps(v, fallback=False):
        if v is None or pd.isna(v):
            return "-"
        s = f"{v:,.0f}원"
        if numeric_close is not None and not pd.isna(numeric_close) and numeric_close > 0:
            s += f"<br>({v / numeric_close * 100:.1f}%)"
        return s + (" (예)" if fallback else "")

    base = {
        "종목코드": code,
        "종목명": stock_name or "-",
        "현재가": curr_price_str or "-",
        "시총": market_cap or "-",
    }

    items = []
    if fin_info["prev_yr"]:
        items.append({
            **base,
            "적용연도": fin_info["prev_yr"],
            "PER": fmt_multi(fin_info["prev_per"]),
            "PBR": fmt_multi(fin_info["prev_pbr"]),
            "ROE": fmt_rate(fin_info["prev_roe"]),
            "배당금": fmt_dps(fin_info["prev_dps"]),
            "매출액": fmt_val(fin_info["prev_rev"], "억"),
            "영업익": fmt_val(fin_info["prev_op"], "억"),
            "당기순이익": fmt_val(fin_info["prev_np"], "억"),
        })

    if fin_info["latest_yr"]:
        if pd.isna(fin_info["cur_dps"]):
            dps_cell = fmt_dps(fin_info["prev_dps"], fallback=True)
        else:
            dps_cell = fmt_dps(fin_info["cur_dps"])
        items.append({
            **base,
            "적용연도": fin_info["latest_yr"],
            "PER": fmt_multi(fin_info["cur_per"]),
            "PBR": fmt_multi(fin_info["cur_pbr"]),
            "ROE": fmt_rate(fin_info["cur_roe"]),
            "배당금": dps_cell,
            "매출액": fmt_val(fin_info["cur_rev"], "억"),
            "영업익": fmt_val(fin_info["cur_op"], "억"),
            "당기순이익": fmt_val(fin_info["cur_np"], "억"),
        })

    return items


def _build_table(rows, selected=frozenset()):
    """종목별로 tbody를 하나씩 만든다. 공통 값은 rowspan으로 병합하고,
    종목 구분선은 인라인 스타일로 넣는다. HTML은 한 줄로 만들어
    st.markdown이 코드블록으로 해석하지 않게 한다."""
    head = (
        '<th class="c-chk"><input type="checkbox" class="header-select-all" title="전체 선택"></th>'
        '<th class="c-name">종목명</th>'
        '<th class="c-price">현재가 / 시총</th>'
        + "".join(f"<th>{c}</th>" for c in DATA_COLS)
    )

    groups = {}
    for r in rows:
        groups.setdefault(r["종목코드"], []).append(r)

    body = []
    for code, g in groups.items():
        first = g[0]
        n = len(g)
        rs = f' rowspan="{n}"' if n > 1 else ""
        name = _html.escape(str(first["종목명"]))
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        price = _html.escape(str(first["현재가"]))
        mcap = _html.escape(str(first["시총"]))
        checked = " checked" if code in selected else ""

        body.append("<tbody>")
        for i, r in enumerate(g):
            last = i == n - 1
            row_style = f' style="{GROUP_END_STYLE}"' if last else ""
            body.append(f"<tr{row_style}>")

            if i == 0:
                body.append(
                    f'<td class="c-chk"{rs} style="{GROUP_END_STYLE}">'
                    f'<input type="checkbox" class="stock-checkbox" data-code="{code}"{checked}></td>'
                )
                body.append(
                    f'<td class="c-name"{rs} style="{GROUP_END_STYLE}">'
                    f'<a class="naver-link" target="_blank" href="{url}">{name}</a>'
                    f'<div class="c-code">{code}</div></td>'
                )
                body.append(
                    f'<td class="c-price"{rs} style="{GROUP_END_STYLE}">'
                    f'<div>{price}</div>'
                    f'<div class="c-mcap">{mcap}</div></td>'
                )

            for col in DATA_COLS:
                val = r[col]
                # 배당금 셀만 <br>을 포함하므로 이스케이프하지 않는다
                cell = val if col == "배당금" else _html.escape(str(val))
                body.append(f"<td>{cell}</td>")
            body.append("</tr>")
        body.append("</tbody>")

    return (
        '<div class="wl-wrap"><table class="wl-table" id="table_tab_watchlist">'
        f'<thead><tr>{head}</tr></thead>{"".join(body)}</table></div>'
    )


def _watch_table(codes):
    """관심종목 표를 컴포넌트로 그리고, 체크된 종목코드 목록을 반환한다."""
    rows = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(fetch_watchlist_item, codes))
    for info_list in results:
        rows.extend(info_list or [])

    if not rows:
        st.info("관심종목 시세를 불러오지 못했습니다.")
        return []

    prev_selected = set(st.session_state.get("wl_sel", []) or [])
    html = WL_CSS + _build_table(rows, prev_selected)
    frame_h = min(640, 120 + len(codes) * 60)
    return selectable_table(html, key="wl_sel", frame_h=frame_h) or []


def render_tab_watchlist(full_csv_records_map=None):
    watchlist_codes = load_watchlist_codes()

    if watchlist_codes:
        selected = _watch_table(watchlist_codes)
        st.caption(f"선택됨: {len(selected)}개 {selected}")   # 확인용

        st.write("")
        _, col_r = st.columns([3, 1.8])
        with col_r:
            if st.button("🗑️ 선택 항목 삭제", type="primary", use_container_width=True, key="btn_wl_delete"):
                # 현재 목록에 있는 종목만 삭제 대상으로 본다 (이미 지운 종목 제외)
                codes_to_delete = [c for c in dict.fromkeys(selected) if c in watchlist_codes]
                if not codes_to_delete:
                    st.warning("⚠️ 삭제할 종목의 체크박스를 먼저 선택해 주세요.")
                else:
                    new_codes = [c for c in watchlist_codes if c not in codes_to_delete]
                    save_watchlist_codes(new_codes)
                    st.success(f"🗑️ 선택한 종목({len(codes_to_delete)}개) 삭제 완료")
                    st.rerun()
    else:
        st.info("등록된 관심종목이 없습니다. 아래 토글을 켜서 종목코드를 추가해 주세요.")

    st.write("---")

    show_manage_box = st.toggle("➕ 종목코드 추가 및 관리", value=False, key="toggle_watchlist_manage")
    if not show_manage_box:
        return

    with st.container(border=True):
        if st.button("📥 현재시세 탭에서 체크된 종목 가져오기", use_container_width=True,
                     type="secondary", key="btn_wl_import"):
            raw = st.query_params.get("sel_price", "") or st.query_params.get("del_codes", "")
            picked = _dedupe(str(raw).split(","))
            if not picked:
                st.warning("⚠️ 현재시세 탭에서 체크박스로 선택된 종목이 없습니다.")
            else:
                current = load_watchlist_codes()
                new = [c for c in picked if c not in current]
                if new:
                    save_watchlist_codes(current + new)
                    st.success(f"🎉 총 {len(new)}개의 종목이 관심종목에 추가되었습니다!")
                    st.rerun()
                else:
                    st.info("ℹ️ 선택한 종목이 이미 모두 관심종목에 등록되어 있습니다.")

        st.markdown("---")

        st.caption("📂 관심종목 백업 파일(TXT) 관리")
        d_col1, d_col2 = st.columns(2)

        with d_col1:
            current = load_watchlist_codes()
            file_content = "\n".join(current) + ("\n" if current else "")
            st.download_button(
                label="💾 백업 파일 다운로드",
                data=file_content,
                file_name="watchlist_codes.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_wl_backup",
            )

        with d_col2:
            uploaded_file = st.file_uploader("백업 파일 업로드 (복구)", type=["txt"],
                                             label_visibility="collapsed", key="wl_restore_upload")
            if uploaded_file is not None and st.button("📥 업로드 파일로 복구", use_container_width=True,
                                                       key="btn_wl_restore"):
                try:
                    decoded = uploaded_file.getvalue().decode("utf-8")
                    restored = _dedupe(decoded.splitlines())
                    if restored:
                        save_watchlist_codes(restored)
                        st.success(f"🎉 총 {len(restored)}개 종목 복구 완료!")
                        st.rerun()
                    else:
                        st.warning("⚠️ 업로드한 파일에 올바른 종목 코드가 없습니다.")
                except Exception as e:
                    st.error(f"⚠️ 파일 처리 중 오류 발생: {e}")

        st.markdown("---")

        st.caption("6자리 종목코드를 직접 입력하여 관심종목에 추가할 수 있습니다.")
        add_col1, add_col2 = st.columns([3, 1])
        with add_col1:
            input_code = st.text_input("종목코드 입력", placeholder="예: 005930 (삼성전자)",
                                       label_visibility="collapsed", key="input_new_watchlist_code")
        with add_col2:
            if st.button("종목 추가", use_container_width=True, type="primary", key="btn_wl_add"):
                cleaned = input_code.strip().zfill(6)
                if cleaned.isdigit() and len(cleaned) == 6:
                    current = load_watchlist_codes()
                    if cleaned not in current:
                        save_watchlist_codes(current + [cleaned])
                        st.success(f"🎉 종목코드({cleaned})가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.warning("⚠️ 이미 관심종목에 등록된 코드입니다.")
                else:
                    st.error("⚠️ 올바른 6자리 숫자 종목코드를 입력해주세요.")
