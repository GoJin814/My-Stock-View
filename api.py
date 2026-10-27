import requests
import numpy as np

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Referer": "https://m.stock.naver.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def to_num(val):
    if val is None or val in ["", "-", "N/A"]:
        return np.nan
    try:
        return float(str(val).replace(",", "").replace("+", "").replace("%", "").strip())
    except Exception:
        return np.nan

def fetch_basic(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=4)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_integration(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=4)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_finance(code: str):
    """네이버 연간 요약 재무"""
    url_front = f"https://m.stock.naver.com/front-api/stock/domestic/finance/annual?code={code}"
    try:
        res = requests.get(url_front, headers=REQ_HEADERS, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data:
                return data
    except Exception:
        pass
        
    url_legacy = f"https://m.stock.naver.com/api/stock/{code}/finance/annual"
    try:
        res = requests.get(url_legacy, headers=REQ_HEADERS, timeout=4)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def extract_row_list(obj):
    """재무 JSON 구조에서 rowList를 가볍게 추출"""
    if isinstance(obj, dict):
        if "rowList" in obj and isinstance(obj["rowList"], list):
            return obj["rowList"]
        # 딕셔너리 내부를 한 뎁스만 빠르게 탐색
        for v in obj.values():
            if isinstance(v, dict) and "rowList" in v and isinstance(v["rowList"], list):
                return v["rowList"]
    return []
