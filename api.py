import requests
import numpy as np
import pandas as pd
import re
from bs4 import BeautifulSoup

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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
    반환값: {'2023': 1234.0, '2024': 5678.0, '2025': 9101.0, '2026': ...}
    """
    url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={code}"
    fcf_dict = {}
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=7)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # 1. Financial Summary 테이블 찾기 (class="gHead01" 중 연간/분기 실적 표)
            tables = soup.find_all("table", class_="gHead01")
            for tbl in tables:
                thead = tbl.find("thead")
                if not thead:
                    continue
                
                # 상단 헤더에서 연도(4자리) 컬럼 위치 파악
                # thead의 두 번째 tr(보통 날짜 행) 확인
                header_rows = thead.find_all("tr")
                target_tr = header_rows[-1] if header_rows else None
                if not target_tr:
                    continue
                
                year_cols = []
                for th in target_tr.find_all("th"):
                    th_text = th.get_text().strip()
                    # 2024/12, 2025/12(E) 등 4자리 연도 추출
                    match = re.search(r'(20\d{2})', th_text)
                    if match:
                        year_cols.append(match.group(1))
                    else:
                        # 주요재무정보 같은 텍스트 행 제외용
                        if year_cols: # 이미 연도가 시작되었는데 연도가 없으면 종료
                            break

                if not year_cols:
                    continue

                # 본문(tbody)에서 FCF 행 탐색
                tbody = tbl.find("tbody")
                if not tbody:
                    continue

                for r in tbody.find_all("tr"):
                    # th 또는 첫 번째 td에서 제목 확인
                    row_title = ""
                    th = r.find(["th", "td"])
                    if th:
                        row_title = th.get_text().replace(" ", "").upper()

                    if "FCF" in row_title:
                        tds = r.find_all("td")
                        for idx, y in enumerate(year_cols):
                            if idx < len(tds):
                                raw_val = tds[idx].get_text()
                                num = to_num(raw_val)
                                if pd.notna(num):
                                    fcf_dict[y] = num
                        if fcf_dict:
                            return fcf_dict
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
