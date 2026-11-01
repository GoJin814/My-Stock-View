import numpy as np
import requests
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Referer": "https://m.stock.naver.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

_session = requests.Session()
_session.headers.update(REQ_HEADERS)
_session.mount("https://", HTTPAdapter(pool_connections=16, pool_maxsize=64))

# 한 종목 안의 3개 요청을 병렬로 실행하는 전용 풀 (종목 단위 풀과 분리해 교착 방지)
_pool = ThreadPoolExecutor(max_workers=24)


def to_num(val):
    if val is None:
        return np.nan
    s = str(val).strip()
    if s in ("", "-", "N/A", "None", "nan"):
        return np.nan
    for ch in (",", "+", "%", "배", "원", " "):
        s = s.replace(ch, "")
    try:
        return float(s)
    except ValueError:
        return np.nan


def _get_json(url, timeout=4):
    try:
        r = _session.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def fetch_basic(code: str):
    return _get_json(f"https://m.stock.naver.com/api/stock/{code}/basic")


def fetch_integration(code: str):
    return _get_json(f"https://m.stock.naver.com/api/stock/{code}/integration")


def fetch_finance(code: str):
    """네이버 연간 요약 재무 (신규 엔드포인트 실패 시 구버전으로 대체)"""
    return (
        _get_json(f"https://m.stock.naver.com/front-api/stock/domestic/finance/annual?code={code}")
        or _get_json(f"https://m.stock.naver.com/api/stock/{code}/finance/annual")
    )


def fetch_all(code: str):
    """basic / integration / finance 를 병렬로 가져온다."""
    fb = _pool.submit(fetch_basic, code)
    fi = _pool.submit(fetch_integration, code)
    ff = _pool.submit(fetch_finance, code)
    return fb.result(), fi.result(), ff.result()


def extract_row_list(obj):
    """재무 JSON에서 rowList를 재귀적으로 찾는다."""
    if isinstance(obj, dict):
        if "rowList" in obj and isinstance(obj["rowList"], list):
            return obj["rowList"]
        for v in obj.values():
            found = extract_row_list(v)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = extract_row_list(item)
            if found:
                return found
    return []
