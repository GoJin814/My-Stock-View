import re
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import streamlit as st

from api import fetch_all, extract_row_list, to_num
from styles import html

YEAR_RE = re.compile(r"(20\d{2})")
FIELDS = ("rev", "op", "np", "eps", "bps", "dps", "roe", "per", "pbr")

# 정렬 옵션: 표시 이름 -> 정렬에 쓸 숫자/문자 컬럼
SORT_OPTIONS = {
    "등록순": None,
    "종목명": "종목명",
    "현재가": "_close",
    "시총": "_mcap",
    "현재 PER": "_cur_per",
    "현재 PBR": "_cur_pbr",
    "배당수익률": "_div_yield",
    "매출 YoY": "_rev_yoy",
    "영업익 YoY": "_op_yoy",
    "순익 YoY": "_np_yoy",
    "최근 ROE": "_num_ROE_최근",
    "최근 PER": "_num_PER_최근",
    "최근 PBR": "_num_PBR_최근",
}


# ---------- 원시 데이터 캐시 (app / 관심종목이 공유) ----------
@st.cache_data(ttl=3600, show_spinner=False)
def get_raw(code: str):
    basic, integ, fin = fetch_all(code)
    if not basic:
        # 예외를 던지면 st.cache_data가 결과를 캐시하지 않는다
        raise RuntimeError(f"{code}: 시세 조회 실패")
    return basic, integ, fin


def load_raw(code: str):
    try:
        return get_raw(code)
    except Exception:
        return {}, {}, {}


# ---------- 포맷 / 계산 ----------
def _isna(v):
    if v is None:
        return True
    if isinstance(v, float) and np.isnan(v):
        return True
    return str(v).strip() in ("", "-", "None", "nan", "N/A")


def _fmt_num(v, suffix=""):
    return "-" if _isna(v) else f"{float(v):,.0f}{suffix}"


def _fmt_x(v):
    return "-" if _isna(v) else f"{float(v):.2f}배"


def _fmt_pct(v, signed=False):
    if _isna(v):
        return "-"
    return f"{float(v):+.1f}%" if signed else f"{float(v):.2f}%"


def _yoy(cur, prev):
    if _isna(cur) or _isna(prev) or float(prev) == 0:
        return np.nan
    return (float(cur) - float(prev)) / abs(float(prev)) * 100


def _div_yield(dps, close):
    if _isna(dps) or _isna(close) or float(close) <= 0:
        return np.nan
    return float(dps) / float(close) * 100


def _val(item):
    return item.get("value") if isinstance(item, dict) else item


def _match_field(t):
    if t in ("매출액", "수익"):
        return "rev"
    if t == "영업이익":
        return "op"
    if t in ("당기순이익", "당기순익"):
        return "np"
    if "ROE" in t:
        return "roe"
    if "PER" in t:
        return "per"
    if "PBR" in t:
        return "pbr"
    if any(k in t for k in ("수정주당순이익", "주당순이익", "EPS")):
        return "eps"
    if any(k in t for k in ("주당순자산", "BPS")):
        return "bps"
    if any(k in t for k in ("주당배당금", "DPS")):
        return "dps"
    return None


def parse_eok(s):
    """'400조 1,234억' 같은 문자열을 억원 단위 숫자로 변환"""
    s = str(s).replace(",", "").replace(" ", "")
    total, found = 0.0, False
    m = re.search(r"([\d.]+)조", s)
    if m:
        total += float(m.group(1)) * 10000
        found = True
    m = re.search(r"([\d.]+)억", s)
    if m:
        total += float(m.group(1))
        found = True
    return total if found else np.nan


def parse_finance(fin_json):
    out = {"yr_prev": "", "yr_cur": ""}
    for f in FIELDS:
        out[f + "_prev"] = np.nan
        out[f + "_cur"] = np.nan

    for row in extract_row_list(fin_json):
        field = _match_field(str(row.get("title", "")).strip().replace(" ", ""))
        cols = row.get("columns") or {}
        if not field or not cols:
            continue

        by_year = {}
        for k in cols:
            m = YEAR_RE.search(str(k))
            if m:
                by_year[m.group(1)] = k
        if not by_year:
            continue

        years = sorted(by_year)
        cur_y = years[-1]
        prev_y = years[-2] if len(years) >= 2 else None

        if not out["yr_cur"]:
            out["yr_cur"] = f"{cur_y}년"
        if prev_y and not out["yr_prev"]:
            out["yr_prev"] = f"{prev_y}년"

        out[field + "_cur"] = to_num(_val(cols[by_year[cur_y]]))
        if prev_y:
            out[field + "_prev"] = to_num(_val(cols[by_year[prev_y]]))
    return out


def _base_info(basic, integ):
    integ_map, mcap = {}, ""
    for it in (integ.get("totalInfos") or []):
        ck = str(it.get("code", "")).strip()
        key = str(it.get("key", "")).strip()
        val = str(it.get("value", "")).strip()
        if not mcap and (ck == "marketValue" or key in ("시총", "시가총액")) and val not in ("", "-"):
            mcap = val
        integ_map[key] = val

    name = str(basic.get("stockName") or "").strip()
    raw_close = basic.get("closePrice")
    close = to_num(raw_close)
    if _isna(raw_close):
        price = "-"
    else:
        price = str(raw_close) if "원" in str(raw_close) else f"{raw_close}원"

    return {
        "name": name or "-",
        "price": price,
        "close": close,
        "mcap": mcap or "-",
        "mcap_eok": parse_eok(mcap),
        "integ": integ_map,
    }


def _dps_cell(v, close, suffix=""):
    if _isna(v):
        return "-"
    s = f"{float(v):,.0f}원{suffix}"
    if not _isna(close) and float(close) > 0:
        return Html(f"{s}<br>({float(v) / float(close) * 100:.1f}%)")
    return s


# ---------- 종목 1개 = 시세 탭 레코드 (숫자 컬럼은 _ 접두어) ----------
def build_stock_record(code):
    basic, integ, fin_json = load_raw(code)
    info = _base_info(basic, integ)
    close = info["close"]

    cur_per = to_num(basic.get("per", info["integ"].get("PER", "-")))
    cur_pbr = to_num(basic.get("pbr", info["integ"].get("PBR", "-")))
    f = parse_finance(fin_json)

    dy = _div_yield(f["dps_cur"], close)
    rev_y = _yoy(f["rev_cur"], f["rev_prev"])
    op_y = _yoy(f["op_cur"], f["op_prev"])
    np_y = _yoy(f["np_cur"], f["np_prev"])

    return {
        "종목코드": code,
        "종목명": info["name"],
        "현재가": info["price"],
        "시총": info["mcap"],
        "현재 PER": _fmt_x(cur_per),
        "현재 PBR": _fmt_x(cur_pbr),
        "DPS(원)": _fmt_num(f["dps_cur"], "원"),
        "배당수익률": _fmt_pct(dy),
        "_close": close,
        "_mcap": info["mcap_eok"],
        "_cur_per": cur_per,
        "_cur_pbr": cur_pbr,
        "_div_yield": dy,
        "직전연도": f["yr_prev"] or "-",
        "최근연도": f["yr_cur"] or "-",
        "매출_직전": _fmt_num(f["rev_prev"], "억"),
        "영업익_직전": _fmt_num(f["op_prev"], "억"),
        "순익_직전": _fmt_num(f["np_prev"], "억"),
        "매출_최근": _fmt_num(f["rev_cur"], "억"),
        "영업익_최근": _fmt_num(f["op_cur"], "억"),
        "순익_최근": _fmt_num(f["np_cur"], "억"),
        "매출_YoY": _fmt_pct(rev_y, signed=True),
        "영업익_YoY": _fmt_pct(op_y, signed=True),
        "순익_YoY": _fmt_pct(np_y, signed=True),
        "_rev_yoy": rev_y,
        "_op_yoy": op_y,
        "_np_yoy": np_y,
        "PER_직전": _fmt_x(f["per_prev"]),
        "PBR_직전": _fmt_x(f["pbr_prev"]),
        "ROE_직전": _fmt_pct(f["roe_prev"]),
        "EPS_직전": _fmt_num(f["eps_prev"], "원"),
        "BPS_직전": _fmt_num(f["bps_prev"], "원"),
        "PER_최근": _fmt_x(f["per_cur"]),
        "PBR_최근": _fmt_x(f["pbr_cur"]),
        "ROE_최근": _fmt_pct(f["roe_cur"]),
        "EPS_최근": _fmt_num(f["eps_cur"], "원"),
        "BPS_최근": _fmt_num(f["bps_cur"], "원"),
        "_num_PER_직전": f["per_prev"],
        "_num_PBR_직전": f["pbr_prev"],
        "_num_PER_최근": f["per_cur"],
        "_num_PBR_최근": f["pbr_cur"],
        "_num_ROE_최근": f["roe_cur"],
    }


def _watch_rows(code):
    basic, integ, fin_json = load_raw(code)
    info = _base_info(basic, integ)
    f = parse_finance(fin_json)
    if not f["yr_prev"] and not f["yr_cur"]:
        return []

    close = info["close"]
    base = {"종목코드": code, "종목명": info["name"], "현재가": info["price"], "시총": info["mcap"]}
    rows = []

    if f["yr_prev"]:
        rows.append({
            **base,
            "적용연도": f["yr_prev"],
            "PER": _fmt_x(f["per_prev"]),
            "PBR": _fmt_x(f["pbr_prev"]),
            "ROE": _fmt_pct(f["roe_prev"]),
            "배당금": _dps_cell(f["dps_prev"], None),
            "매출액": _fmt_num(f["rev_prev"], "억"),
            "영업익": _fmt_num(f["op_prev"], "억"),
            "당기순이익": _fmt_num(f["np_prev"], "억"),
        })

    if f["yr_cur"]:
        if _isna(f["dps_cur"]):
            dps = _dps_cell(f["dps_prev"], close, " (예)")
        else:
            dps = _dps_cell(f["dps_cur"], close)
        rows.append({
            **base,
            "적용연도": f["yr_cur"],
            "PER": _fmt_x(f["per_cur"]),
            "PBR": _fmt_x(f["pbr_cur"]),
            "ROE": _fmt_pct(f["roe_cur"]),
            "배당금": dps,
            "매출액": _fmt_num(f["rev_cur"], "억"),
            "영업익": _fmt_num(f["op_cur"], "억"),
            "당기순이익": _fmt_num(f["np_cur"], "억"),
        })
    return rows


def build_master(codes):
    if not codes:
        return pd.DataFrame()
    with ThreadPoolExecutor(max_workers=12) as ex:
        recs = list(ex.map(build_stock_record, codes))
    return pd.DataFrame(recs)


def build_watchlist(codes):
    if not codes:
        return pd.DataFrame()
    with ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(_watch_rows, codes))
    return pd.DataFrame([r for rows in results for r in rows])


def apply_sort(df, col, asc):
    if df.empty or not col or col not in df.columns:
        return df
    if df[col].dtype == object:
        return df.sort_values(col, ascending=asc, kind="stable",
                              key=lambda s: s.astype(str).str.lower()).reset_index(drop=True)
    return df.sort_values(col, ascending=asc, na_position="last", kind="stable").reset_index(drop=True)
