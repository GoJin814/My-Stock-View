import requests
import numpy as np
import pandas as pd
import re
from bs4 import BeautifulSoup

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finance.naver.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
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
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_integration(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_finance(code: str):
    url_front = f"https://m.stock.naver.com/front-api/stock/domestic/finance/annual?code={code}"
    try:
        res = requests.get(url_front, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://m.stock.naver.com/"}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                return data
    except Exception:
        pass
    return {}

def fetch_balance_sheet(code: str):
    url = f"https://m.stock.naver.com/front-api/stock/domestic/finance/annual/financialStatement?code={code}"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://m.stock.naver.com/"}, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def fetch_fcf_from_fnguide(code: str):
    """
    네이버 증권 PC 웹 -> 종목분석 -> 기업현황 -> Financial Summary 표에서 FCF 추출
    반환값: {'2022/12': 1234, '2023/12': 5678, ...}
    """
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"
    fcf_dict = {}
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Financial Summary 연간 헤더(연도) 추출
            # 헤더는 th 내에 2022/12, 2023/12, 2024/12(E) 형태로 존재
            tables = soup.find_all("table", class_="gHead01")
            for tbl in tables:
                rows = tbl.find_all("tr")
                # FCF 행 찾기
                target_row = None
                for r in rows:
                    th = r.find("th")
                    if th and "FCF" in th.get_text():
                        target_row = r
                        break
                
                if target_row:
                    # 상단 연도 헤더 파싱
                    header_tr = tbl.find("thead").find_all("tr")[-1]
                    year_ths = header_tr.find_all("th")
                    # 연간 데이터 컬럼 (보통 0~7번째)
                    year_keys = [re.sub(r'[^0-9]', '', th.get_text()[:7])[:4] for th in year_ths if re.search(r'\d{4}', th.get_text())]
                    
                    # td 값 추출
                    tds = target_row.find_all("td")
                    for i, td in enumerate(tds):
                        if i < len(year_keys):
                            val = to_num(td.get_text())
                            if pd.notna(val):
                                fcf_dict[year_keys[i]] = val
                    if fcf_dict:
                        break
    except Exception:
        pass
    return fcf_dict

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
