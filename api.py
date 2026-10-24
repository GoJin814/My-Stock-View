import requests
import numpy as np
import pandas as pd
import re

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

def normalize_date(val):
    if not val or pd.isna(val):
        return ""
    val_str = str(val).strip()
    parsed = pd.to_datetime(val_str, errors='coerce')
    if pd.notnull(parsed):
        return parsed.strftime('%Y-%m-%d')
    digits = re.sub(r'[^0-9]', '', val_str)
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return val_str

def fetch_basic(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_integration(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_finance(code: str):
    url = f"https://m.stock.naver.com/front-api/stock/domestic/finance/annual?code={code}"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_financial_statement(code: str):
    """재무상태표 및 현금흐름표 상세 API (순현금, 순차입금, FCF 산출용)"""
    url = f"https://m.stock.naver.com/front-api/stock/domestic/finance/annual/financialStatement?code={code}"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def extract_row_list(obj):
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
