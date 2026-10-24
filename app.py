import streamlit as st
import requests
import pandas as pd
import numpy as np
import os
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Scanning_주식", layout="wide")

# 표 글자 크기, 컴팩트 스타일 및 2단 헤더/구분선 스타일 적용
st.markdown("""
<style>
div[data-testid="stDataEditor"] {
    font-size: 13px !important;
}
div[data-testid="stDataEditor"] [role="gridcell"],
div[data-testid="stDataEditor"] [role="columnheader"] {
    font-size: 13px !important;
}
div[data-testid="stDataEditor"] .dvn-scroller {
    line-height: 1.2 !important;
}

/* 2단 헤더 및 국내지수 모니터 테이블 스타일 */
.styled-table-container {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #374151;
    border-radius: 8px;
    margin-bottom: 1.2rem;
    background-color: #1f2937;
}
.compare-table {
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
    text-align: center;
    white-space: nowrap;
    color: #f3f4f6;
}
.compare-table th, .compare-table td {
    padding: 8px 12px;
    border-bottom: 1px solid #374151;
    border-right: 1px solid #374151;
}
.compare-table th {
    background-color: #111827;
    font-weight: 600;
}
.compare-table th.group-header {
    background-color: #0f172a;
    font-size: 14px;
    color: #93c5fd;
    letter-spacing: 0.5px;
}
.compare-table tr:hover td {
    background-color: #374151;
}
/* 블록 경계선 (굵은 세로 구분선) */
.compare-table .year-divider {
    border-right: 3px solid #9ca3af !important;
}
/* 종목명 및 일시 열 고정(Sticky) */
.compare-table .sticky-col {
    position: sticky;
    left: 0;
    background-color: #1f2937;
    z-index: 2;
    font-weight: bold;
    border-right: 2px solid #4b5563;
}
.compare-table th.sticky-header {
    background-color: #111827;
    z-index: 3;
}
</style>
""", unsafe_allow_html=True)

SAVE_FILE = "saved_codes.txt"

def load_codes():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            codes = [line.strip().zfill(6) for line in f.readlines() if line.strip()]
            return list(dict.fromkeys(codes))
    return ["178320", "001130", "086450", "007690", "095660", "161890"]

def save_codes(codes):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        for c in codes:
            f.write(f"{c.strip().zfill(6)}\n")

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://finance.naver.com/",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 1. 실시간 시세 (/basic)
def fetch_basic(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

# 2. 통합 정보 (/integration)
def fetch_integration(code: str):
    url = f"https://m.stock.naver.com/api/stock/{code}/integration"
    try:
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

# 3. 연간 재무제표 (2단계 자동 폴백)
def fetch_finance(code: str):
    url_front = f"https://m.stock.naver.com/front-api/stock/domestic/finance/annual?code={code}"
    try:
        res = requests.get(url_front, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                return data
    except Exception:
        pass
        
    url_legacy = f"https://m.stock.naver.com/api/stock/{code}/finance/annual"
    try:
        res = requests.get(url_legacy, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def to_num(val):
    if val is None or val in ["", "-", "N/A"]:
        return np.nan
    try:
        return float(str(val).replace(",", "").strip())
    except:
        return np.nan

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

# --- [국내지수 모니터링 데이터 수집 함수군] ---

@st.cache_data(ttl=300)
def fetch_kospi_market_data():
    """
    1) 코스피 지수: https://stock.naver.com/domestic/index/KOSPI/price
    4) KRX 시총, PER, PBR: https://data.krx.co.kr/ 연동 API
    """
    records = []
    try:
        # 최근 일자별 코스피 히스토리 수신 (page 1, 10건)
        url = "https://api.stock.naver.com/index/KOSPI/price?page=1&pageSize=10"
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            items = res.json()
            for row in items:
                # 일자 정규화 (YYYY-MM-DD)
                raw_dt = row.get("localTradedAt", "")[:10].replace(".", "-")
                c_price = to_num(row.get("closePrice"))
                records.append({
                    "일시": raw_dt,
                    "KOSPI": c_price
                })
        
        # 현재 기준 시가총액(KRX), PER, PBR 정보 수신
        basic_url = "https://api.stock.naver.com/index/KOSPI/basic"
        b_res = requests.get(basic_url, headers=REQ_HEADERS, timeout=5)
        latest_market_sum, latest_per, latest_pbr = np.nan, np.nan, np.nan
        if b_res.status_code == 200:
            b_data = b_res.json()
            latest_market_sum = to_num(b_data.get("marketSum"))
            latest_per = to_num(b_data.get("per"))
            latest_pbr = to_num(b_data.get("pbr"))
            
        df = pd.DataFrame(records)
        if not df.empty:
            df["시가총액(억원)"] = np.nan
            df["PER"] = np.nan
            df["PBR"] = np.nan
            # 최신 행에 KRX 집계 시총/PER/PBR 매핑
            df.loc[0, "시가총액(억원)"] = latest_market_sum
            df.loc[0, "PER"] = latest_per
            df.loc[0, "PBR"] = latest_pbr
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def fetch_market_deposit_data():
    """
    2) 고객예탁금, 신용잔고 링크: https://stock.naver.com/market/stock/kr/deposit
    -> 원천 네이버 증시자금동향 페이지 파싱
    """
    records = []
    try:
        url = "https://finance.naver.com/sise/sise_deposit.naver"
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        res.encoding = "euc-kr"
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table", class_="type_1")
            if table:
                rows = table.find_all("tr")
                for tr in rows:
                    tds = tr.find_all("td")
                    if len(tds) >= 4:
                        date_str = tds[0].text.strip()
                        if not re.match(r"^\d{2,4}\.\d{2}\.\d{2}$", date_str):
                            continue
                        # YYYY-MM-DD 변환
                        clean_date = date_str.replace(".", "-")
                        if len(clean_date) == 8:
                            clean_date = "20" + clean_date
                            
                        # 고객예탁금 및 증감
                        dep_val = to_num(tds[1].text)
                        dep_diff = to_num(tds[2].text)
                        if "nv01" in str(tds[2]) or "하락" in str(tds[2]):
                            dep_diff = -abs(dep_diff) if pd.notna(dep_diff) else np.nan
                        elif "red01" in str(tds[2]) or "상승" in str(tds[2]):
                            dep_diff = abs(dep_diff) if pd.notna(dep_diff) else np.nan

                        # 신용융자 잔고 및 증감
                        credit_val = to_num(tds[3].text)
                        credit_diff = to_num(tds[4].text) if len(tds) > 4 else np.nan
                        if len(tds) > 4:
                            if "nv01" in str(tds[4]) or "하락" in str(tds[4]):
                                credit_diff = -abs(credit_diff) if pd.notna(credit_diff) else np.nan
                            elif "red01" in str(tds[4]) or "상승" in str(tds[4]):
                                credit_diff = abs(credit_diff) if pd.notna(credit_diff) else np.nan

                        records.append({
                            "일시": clean_date,
                            "고객예탁금(억원)": dep_val,
                            "증감(억원)": dep_diff,
                            "신용잔고(억원)": credit_val,
                            "증감(신용)(억원)": credit_diff
                        })
    except Exception:
        pass
    return pd.DataFrame(records)

@st.cache_data(ttl=300)
def fetch_exchange_rate():
    """
    3) 환율 링크: https://stock.naver.com/marketindex/exchange/FX_USDKRW/price
    """
    records = []
    try:
        url = "https://api.stock.naver.com/marketindex/exchange/FX_USDKRW/prices?page=1&pageSize=15"
        res = requests.get(url, headers=REQ_HEADERS, timeout=5)
        if res.status_code == 200:
            for row in res.json():
                raw_dt = row.get("localTradedAt", "")[:10].replace(".", "-")
                rate = to_num(row.get("closePrice"))
                records.append({
                    "일시": raw_dt,
                    "환율": rate
                })
    except Exception:
        pass
    return pd.DataFrame(records)

def get_domestic_market_monitor_df():
    df_kospi = fetch_kospi_market_data()
    df_dep = fetch_market_deposit_data()
    df_fx = fetch_exchange_rate()

    if df_dep.empty and df_kospi.empty:
        return pd.DataFrame()

    # 예탁금 일자를 기준으로 외부 조인 병합
    base_df = df_dep if not df_dep.empty else df_kospi
    merged = base_df.copy()

    if not df_kospi.empty and base_df is not df_kospi:
        merged = pd.merge(merged, df_kospi, on="일시", how="left")
    if not df_fx.empty:
        merged = pd.merge(merged, df_fx, on="일시", how="left")

    # 최근 날짜순 정렬
    merged = merged.sort_values(by="일시", ascending=False).reset_index(drop=True)

    # 파생 지표 연산: 고객예탁금/지수, 신용잔고/지수
    merged["고객예탁금/지수"] = np.where(
        (merged["KOSPI"].notna()) & (merged["KOSPI"] > 0),
        merged["고객예탁금(억원)"] / merged["KOSPI"],
        np.nan
    )
    merged["신용잔고/지수"] = np.where(
        (merged["KOSPI"].notna()) & (merged["KOSPI"] > 0),
        merged["신용잔고(억원)"] / merged["KOSPI"],
        np.nan
    )

    # 표시용 포맷팅 변환
    display_df = pd.DataFrame()
    display_df["일시"] = merged["일시"]
    display_df["KOSPI"] = merged["KOSPI"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "-")
    display_df["시가총액(억원)"] = merged["시가총액(억원)"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
    display_df["PER"] = merged["PER"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    display_df["PBR"] = merged["PBR"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    display_df["고객예탁금(억원)"] = merged["고객예탁금(억원)"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
    display_df["증감(억원)"] = merged["증감(억원)"].apply(lambda x: f"{x:+,.0f}" if pd.notna(x) else "-")
    display_df["신용잔고(억원)"] = merged["신용잔고(억원)"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
    display_df["증감(신용)(억원)"] = merged["증감(신용)(억원)"].apply(lambda x: f"{x:+,.0f}" if pd.notna(x) else "-")
    display_df["환율"] = merged["환율"].apply(lambda x: f"{x:,.1f}원" if pd.notna(x) else "-")
    display_df["고객예탁금/지수"] = merged["고객예탁금/지수"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "-")
    display_df["신용잔고/지수"] = merged["신용잔고/지수"].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "-")

    return display_df

# 상단 2단 헤더 테이블 렌더러
def render_multi_header_table(df: pd.DataFrame, top_headers: list, sub_headers: list, divider_indices: list):
    top_th_html = ""
    for title, colspan, is_divider in top_headers:
        divider_cls = " year-divider" if is_divider else ""
        if title in ["종목명", "일시"]:
            top_th_html += f'<th rowspan="2" class="sticky-col sticky-header">{title}</th>'
        else:
            top_th_html += f'<th colspan="{colspan}" class="group-header{divider_cls}">{title}</th>'

    sub_th_html = ""
    for idx, col_title in enumerate(sub_headers, start=1):
        divider_cls = " year-divider" if idx in divider_indices else ""
        sub_th_html += f'<th class="{divider_cls}">{col_title}</th>'

    num_cols = len(df.columns)
    tb_html = ""
    for row_idx in range(len(df)):
        tb_html += "<tr>"
        for col_idx in range(num_cols):
            val = df.iloc[row_idx, col_idx]
            classes = []
            if col_idx == 0:
                classes.append("sticky-col")
            if col_idx in divider_indices:
                classes.append("year-divider")
            cls_attr = f' class="{" ".join(classes)}"' if classes else ""
            tb_html += f"<td{cls_attr}>{val}</td>"
        tb_html += "</tr>"

    html_code = f"""
    <div class="styled-table-container">
        <table class="compare-table">
            <thead>
                <tr>{top_th_html}</tr>
                <tr>{sub_th_html}</tr>
            </thead>
            <tbody>{tb_html}</tbody>
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# 단일 헤더 테이블 렌더러 (구분선 지원)
def render_single_header_table(df: pd.DataFrame, divider_indices: list):
    th_html = ""
    for idx, col in enumerate(df.columns):
        classes = []
        if idx == 0:
            classes.append("sticky-col sticky-header")
        if idx in divider_indices:
            classes.append("year-divider")
        cls_attr = f' class="{" ".join(classes)}"' if classes else ""
        th_html += f"<th{cls_attr}>{col}</th>"

    tb_html = ""
    for row_idx in range(len(df)):
        tb_html += "<tr>"
        for col_idx in range(len(df.columns)):
            val = df.iloc[row_idx, col_idx]
            classes = []
            if col_idx == 0:
                classes.append("sticky-col")
            if col_idx in divider_indices:
                classes.append("year-divider")
            cls_attr = f' class="{" ".join(classes)}"' if classes else ""
            tb_html += f"<td{cls_attr}>{val}</td>"
        tb_html += "</tr>"

    html_code = f"""
    <div class="styled-table-container">
        <table class="compare-table">
            <thead><tr>{th_html}</tr></thead>
            <tbody>{tb_html}</tbody>
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# --- 1. 상단 타이틀 ---
st.title("Scanning_주식")

current_codes = load_codes()

# --- 2. 데이터 수집 및 지표 파싱 ---
if current_codes:
    scan_basic = []
    scan_perf = []
    scan_share = []
    full_csv_records = []
    
    prev_years = []
    latest_years = []

    with st.spinner("네이버 증권 데이터를 동기화하고 있습니다..."):
        for code in current_codes:
            basic = fetch_basic(code)
            integration = fetch_integration(code)
            fin_json = fetch_finance(code)
            
            stock_name = basic.get("stockName", "-")
            raw_close = basic.get("closePrice", "-")
            curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)
            
            total_infos = integration.get("totalInfos", [])
            market_cap = "-"
            integration_dict = {}
            for item in total_infos:
                item_code = str(item.get("code", "")).strip()
                item_key = str(item.get("key", "")).strip()
                item_val = str(item.get("value", "")).strip()
                if item_code == "marketValue" or item_key in ["시총", "시가총액"]:
                    market_cap = item_val
                integration_dict[item_key] = item_val

            raw_per = basic.get("per", integration_dict.get("PER", "-"))
            raw_pbr = basic.get("pbr", integration_dict.get("PBR", "-"))
            raw_div = basic.get("dividendYield", integration_dict.get("배당수익률", "-"))
            
            per_val = f"{str(raw_per).replace('배', '')}배" if raw_per not in ["-", "N/A", None] else "-"
            pbr_val = f"{str(raw_pbr).replace('배', '')}배" if raw_pbr not in ["-", "N/A", None] else "-"
            div_val = f"{raw_div}%" if (raw_div not in ["-", "N/A", None] and "%" not in str(raw_div)) else str(raw_div)

            fin_info = {
                "latest_yr": "-", "prev_yr": "-",
                "cur_rev": np.nan, "prev_rev": np.nan, "rev_yoy": np.nan,
                "cur_op": np.nan,  "prev_op": np.nan,  "op_yoy": np.nan,
                "cur_np": np.nan,  "prev_np": np.nan,  "np_yoy": np.nan,
                "cur_eps": np.nan, "prev_eps": np.nan,
                "cur_bps": np.nan, "prev_bps": np.nan,
                "cur_dps": np.nan, "prev_dps": np.nan,
                "cur_roe": np.nan, "prev_roe": np.nan,
                "cur_per": np.nan, "prev_per": np.nan,
                "cur_pbr": np.nan, "prev_pbr": np.nan,
            }

            row_list = extract_row_list(fin_json)
            if row_list:
                for row in row_list:
                    raw_title = row.get("title", "").strip()
                    columns = row.get("columns", {})
                    if not columns:
                        continue
                    
                    sorted_years = sorted(list(columns.keys()))
                    if not sorted_years:
                        continue
                        
                    latest_k = sorted_years[-1]
                    prev_k = sorted_years[-2] if len(sorted_years) >= 2 else None
                    
                    fin_info["latest_yr"] = f"{latest_k[:4]}년"
                    if prev_k:
                        fin_info["prev_yr"] = f"{prev_k[:4]}년"

                    c_item = columns.get(latest_k, {})
                    c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)
                    
                    p_val = np.nan
                    if prev_k:
                        p_item = columns.get(prev_k, {})
                        p_val = to_num(p_item.get("value") if isinstance(p_item, dict) else p_item)

                    if raw_title in ["매출액", "수익"]:
                        fin_info["cur_rev"] = c_val
                        fin_info["prev_rev"] = p_val
                        if pd.notna(c_val) and pd.notna(p_val) and p_val != 0:
                            fin_info["rev_yoy"] = round(((c_val - p_val) / abs(p_val)) * 100, 2)
                    elif raw_title == "영업이익":
                        fin_info["cur_op"] = c_val
                        fin_info["prev_op"] = p_val
                        if pd.notna(c_val) and pd.notna(p_val) and p_val != 0:
                            fin_info["op_yoy"] = round(((c_val - p_val) / abs(p_val)) * 100, 2)
                    elif raw_title in ["당기순이익", "당기순익"]:
                        fin_info["cur_np"] = c_val
                        fin_info["prev_np"] = p_val
                        if pd.notna(c_val) and pd.notna(p_val) and p_val != 0:
                            fin_info["np_yoy"] = round(((c_val - p_val) / abs(p_val)) * 100, 2)
                    elif raw_title in ["수정주당순이익(원)", "주당순이익(원)", "EPS"]:
                        fin_info["cur_eps"] = c_val
                        fin_info["prev_eps"] = p_val
                    elif raw_title in ["주당순자산(원)", "주당순자산가치(원)", "BPS"]:
                        fin_info["cur_bps"] = c_val
                        fin_info["prev_bps"] = p_val
                    elif raw_title in ["주당배당금(원)", "주당배당금", "DPS"]:
                        fin_info["cur_dps"] = c_val
                        fin_info["prev_dps"] = p_val
                    elif raw_title in ["ROE(%)", "ROE"]:
                        fin_info["cur_roe"] = c_val
                        fin_info["prev_roe"] = p_val
                    elif raw_title in ["PER(배)", "PER"]:
                        fin_info["cur_per"] = c_val
                        fin_info["prev_per"] = p_val
                    elif raw_title in ["PBR(배)", "PBR"]:
                        fin_info["cur_pbr"] = c_val
                        fin_info["prev_pbr"] = p_val

            if fin_info["prev_yr"] != "-":
                prev_years.append(fin_info["prev_yr"])
            if fin_info["latest_yr"] != "-":
                latest_years.append(fin_info["latest_yr"])

            dps_display = f"{fin_info['cur_dps']:,.0f}원" if pd.notna(fin_info['cur_dps']) else "-"

            scan_basic.append({
                "선택": False,
                "종목명": stock_name,
                "종목코드": code,
                "현재가": curr_price_str,
                "시총": market_cap,
                "현재 PER": per_val,
                "현재 PBR": pbr_val,
                "DPS(원)": dps_display,
                "배당수익률": div_val
            })

            scan_perf.append({
                "종목명": stock_name,
                "매출_직전": f"{fin_info['prev_rev']:,.0f}억" if pd.notna(fin_info['prev_rev']) else "-",
                "영업익_직전": f"{fin_info['prev_op']:,.0f}억" if pd.notna(fin_info['prev_op']) else "-",
                "순익_직전": f"{fin_info['prev_np']:,.0f}억" if pd.notna(fin_info['prev_np']) else "-",
                "매출_최근": f"{fin_info['cur_rev']:,.0f}억" if pd.notna(fin_info['cur_rev']) else "-",
                "영업익_최근": f"{fin_info['cur_op']:,.0f}억" if pd.notna(fin_info['cur_op']) else "-",
                "순익_최근": f"{fin_info['cur_np']:,.0f}억" if pd.notna(fin_info['cur_np']) else "-",
                "매출_YoY": f"{fin_info['rev_yoy']:+.1f}%" if pd.notna(fin_info['rev_yoy']) else "-",
                "영업익_YoY": f"{fin_info['op_yoy']:+.1f}%" if pd.notna(fin_info['op_yoy']) else "-",
                "순익_YoY": f"{fin_info['np_yoy']:+.1f}%" if pd.notna(fin_info['np_yoy']) else "-"
            })

            p_per_str = f"{fin_info['prev_per']:.2f}배" if pd.notna(fin_info['prev_per']) else "-"
            p_pbr_str = f"{fin_info['prev_pbr']:.2f}배" if pd.notna(fin_info['prev_pbr']) else "-"
            c_per_str = f"{fin_info['cur_per']:.2f}배" if pd.notna(fin_info['cur_per']) else "-"
            c_pbr_str = f"{fin_info['cur_pbr']:.2f}배" if pd.notna(fin_info['cur_pbr']) else "-"

            scan_share.append({
                "종목명": stock_name,
                "EPS_직전": f"{fin_info['prev_eps']:,.0f}원" if pd.notna(fin_info['prev_eps']) else "-",
                "BPS_직전": f"{fin_info['prev_bps']:,.0f}원" if pd.notna(fin_info['prev_bps']) else "-",
                "ROE_직전": f"{fin_info['prev_roe']:.2f}%" if pd.notna(fin_info['prev_roe']) else "-",
                "PER_직전": p_per_str,
                "PBR_직전": p_pbr_str,
                "EPS_최근": f"{fin_info['cur_eps']:,.0f}원" if pd.notna(fin_info['cur_eps']) else "-",
                "BPS_최근": f"{fin_info['cur_bps']:,.0f}원" if pd.notna(fin_info['cur_bps']) else "-",
                "ROE_최근": f"{fin_info['cur_roe']:.2f}%" if pd.notna(fin_info['cur_roe']) else "-",
                "PER_최근": c_per_str,
                "PBR_최근": c_pbr_str
            })

            full_csv_records.append({
                "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
                "직전연도": fin_info['prev_yr'], "최근연도": fin_info['latest_yr'],
                "매출액_직전": fin_info['prev_rev'], "매출액_최근": fin_info['cur_rev'], "매출_YoY": fin_info['rev_yoy'],
                "영업익_직전": fin_info['prev_op'], "영업익_최근": fin_info['cur_op'], "영업익_YoY": fin_info['op_yoy'],
                "순이익_직전": fin_info['prev_np'], "순이익_최근": fin_info['cur_np'], "순이익_YoY": fin_info['np_yoy'],
                "EPS_직전": fin_info['prev_eps'], "EPS_최근": fin_info['cur_eps'],
                "BPS_직전": fin_info['prev_bps'], "BPS_최근": fin_info['cur_bps'],
                "ROE_직전": fin_info['prev_roe'], "ROE_최근": fin_info['cur_roe'],
                "PER_직전": fin_info['prev_per'], "PER_최근": fin_info['cur_per'],
                "PBR_직전": fin_info['prev_pbr'], "PBR_최근": fin_info['cur_pbr'],
                "DPS": fin_info['cur_dps'], "현재PER": per_val, "현재PBR": pbr_val, "배당수익률": div_val
            })

    most_prev_yr = max(set(prev_years), key=prev_years.count) if prev_years else "2025년"
    most_latest_yr = max(set(latest_years), key=latest_years.count) if latest_years else "2026년"

    df_basic = pd.DataFrame(scan_basic)
    df_perf = pd.DataFrame(scan_perf)
    df_share = pd.DataFrame(scan_share)

    # --- 3. 탭 렌더링 ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 기본 & 시세", 
        "📈 실적 & 성장성 (2개년 비교)", 
        "💰 주당 가치 (2개년 비교)",
        "🌐 국내지수 Monitor"
    ])

    with tab1:
        disabled_cols = [c for c in df_basic.columns if c != "선택"]
        edited_df = st.data_editor(
            df_basic,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", default=False, width="small", pinned=True),
                "종목명": st.column_config.TextColumn("종목명", pinned=True),
            },
            disabled=disabled_cols,
            hide_index=True,
            use_container_width=True,
            key="tab1_editor"
        )

    with tab2:
        top_headers_perf = [
            ("종목명", 1, False),
            (most_prev_yr, 3, True),
            (most_latest_yr, 3, True),
            ("성장률 (YoY)", 3, False)
        ]
        sub_headers_perf = [
            "매출액", "영업이익", "당기순익",
            "매출액", "영업이익", "당기순익",
            "매출 YoY", "영업익 YoY", "순익 YoY"
        ]
        render_multi_header_table(
            df_perf,
            top_headers=top_headers_perf,
            sub_headers=sub_headers_perf,
            divider_indices=[3, 6]
        )

    with tab3:
        top_headers_share = [
            ("종목명", 1, False),
            (most_prev_yr, 5, True),
            (most_latest_yr, 5, False)
        ]
        sub_headers_share = [
            "EPS", "BPS", "ROE", "PER", "PBR",
            "EPS", "BPS", "ROE", "PER", "PBR"
        ]
        render_multi_header_table(
            df_share,
            top_headers=top_headers_share,
            sub_headers=sub_headers_share,
            divider_indices=[5]
        )

    with tab4:
        # [실시간 연동] 국내 주식시장 지수 및 유동성 모니터링 데이터 생성
        df_market = get_domestic_market_monitor_df()
        
        if not df_market.empty:
            # 블록별 세로 구분선: PBR 뒤(4열), 예탁금 증감 뒤(6열), 신용잔고 증감 뒤(8열)
            render_single_header_table(df_market, divider_indices=[4, 6, 8])
        else:
            st.warning("시장 지표 데이터를 불러오는 중 오류가 발생했습니다. 잠시 후 새로고침해 주세요.")

    # --- 4. 컨트롤 영역 (선택 삭제 & CSV 다운로드) ---
    btn_col1, btn_col2, _ = st.columns([1.5, 2, 4])
    with btn_col1:
        delete_btn = st.button("🗑️ 선택 종목 삭제", type="primary", use_container_width=True)
    with btn_col2:
        csv_data = pd.DataFrame(full_csv_records).to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 전체 결과 CSV 다운로드",
            data=csv_data,
            file_name="종목Scan_비교결과.csv",
            mime="text/csv",
            use_container_width=True
        )

    if delete_btn:
        selected_codes = edited_df[edited_df["선택"] == True]["종목코드"].tolist()
        if selected_codes:
            remaining_codes = [c for c in current_codes if c not in selected_codes]
            save_codes(remaining_codes)
            st.success(f"{len(selected_codes)}개 종목 삭제 완료")
            st.rerun()
        else:
            st.warning("삭제할 종목의 체크박스를 먼저 선택해 주세요. (기본 & 시세 탭)")
else:
    st.info("등록된 종목이 없습니다. 아래에서 종목코드를 추가해 주세요.")

# --- 5. 종목 추가 영역 ---
st.write("")
col_add, col_btn = st.columns([3, 1])
with col_add:
    new_code = st.text_input("➕ 추가할 종목코드 (6자리)", placeholder="예: 005930 (삼성전자)", max_chars=6)
with col_btn:
    st.write("")
    if st.button("종목 추가", use_container_width=True):
        if new_code.strip():
            formatted = new_code.strip().zfill(6)
            if formatted not in current_codes:
                current_codes.append(formatted)
                save_codes(current_codes)
                st.success(f"{formatted} 추가 완료")
                st.rerun()

# --- 6. 맨 하단 출처 안내 ---
st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 및 KRX 지표 실시간 연동")
