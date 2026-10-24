import streamlit as st
import requests
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Scanning_주식", layout="wide")

# 표 글자 크기 및 컴팩트 스타일 적용
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
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Referer": "https://m.stock.naver.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
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

# --- 1. 상단 타이틀 ---
st.title("Scanning_주식")

current_codes = load_codes()

# --- 2. 데이터 수집 ---
if current_codes:
    scan_results = []
    
    with st.spinner("네이버 증권 데이터를 동기화하고 있습니다..."):
        for code in current_codes:
            basic = fetch_basic(code)
            integration = fetch_integration(code)
            fin_json = fetch_finance(code)
            
            # 종목명 및 현재가 (/basic)
            stock_name = basic.get("stockName", "-")
            raw_close = basic.get("closePrice", "-")
            curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)
            
            # 시가총액 추출
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

            # 실시간 PER / PBR / 배당수익률
            raw_per = basic.get("per", integration_dict.get("PER", "-"))
            raw_pbr = basic.get("pbr", integration_dict.get("PBR", "-"))
            raw_div = basic.get("dividendYield", integration_dict.get("배당수익률", "-"))
            
            per_val = f"{str(raw_per).replace('배', '')}배" if raw_per not in ["-", "N/A", None] else "-"
            pbr_val = f"{str(raw_pbr).replace('배', '')}배" if raw_pbr not in ["-", "N/A", None] else "-"
            div_val = f"{raw_div}%" if (raw_div not in ["-", "N/A", None] and "%" not in str(raw_div)) else str(raw_div)

            # 재무제표 데이터 추출
            fin_data = {
                "기준연도": "-",
                "매출액": np.nan, "매출YoY": np.nan, "영업이익": np.nan,
                "당기순이익": np.nan, "DPS": np.nan, "EPS": np.nan, "BPS": np.nan
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
                        
                    latest_yr = sorted_years[-1]
                    prev_yr = sorted_years[-2] if len(sorted_years) >= 2 else None
                    
                    fin_data["기준연도"] = f"{latest_yr[:4]}년"
                    
                    latest_item = columns.get(latest_yr, {})
                    latest_val_str = latest_item.get("value") if isinstance(latest_item, dict) else latest_item
                    cur_v = to_num(latest_val_str)
                    
                    prev_item = columns.get(prev_yr, {}) if prev_yr else {}
                    prev_val_str = prev_item.get("value") if isinstance(prev_item, dict) else prev_item
                    prev_v = to_num(prev_val_str)

                    if raw_title in ["매출액", "수익"]:
                        fin_data["매출액"] = cur_v
                        if pd.notna(cur_v) and pd.notna(prev_v) and prev_v != 0:
                            fin_data["매출YoY"] = round(((cur_v - prev_v) / abs(prev_v)) * 100, 2)
                    elif raw_title == "영업이익":
                        fin_data["영업이익"] = cur_v
                    elif raw_title in ["당기순이익", "당기순익"]:
                        fin_data["당기순이익"] = cur_v
                    elif raw_title in ["주당배당금(원)", "주당배당금", "DPS"]:
                        fin_data["DPS"] = cur_v
                    elif raw_title in ["수정주당순이익(원)", "주당순이익(원)", "EPS"]:
                        fin_data["EPS"] = cur_v
                    elif raw_title in ["주당순자산(원)", "주당순자산가치(원)", "BPS"]:
                        fin_data["BPS"] = cur_v

            scan_results.append({
                "선택": False,
                "종목명": stock_name,
                "종목코드": code,
                "현재가": curr_price_str,
                "시총": market_cap,
                "기준실적": fin_data["기준연도"],
                "매출액(억)": f"{fin_data['매출액']:,.0f}억" if pd.notna(fin_data['매출액']) else "-",
                "매출 YoY": f"{fin_data['매출YoY']:+.1f}%" if pd.notna(fin_data['매출YoY']) else "-",
                "영업이익(억)": f"{fin_data['영업이익']:,.0f}억" if pd.notna(fin_data['영업이익']) else "-",
                "당기순익(억)": f"{fin_data['당기순이익']:,.0f}억" if pd.notna(fin_data['당기순이익']) else "-",
                "DPS(원)": f"{fin_data['DPS']:,.0f}원" if pd.notna(fin_data['DPS']) else "-",
                "배당수익률": div_val,
                "EPS(원)": f"{fin_data['EPS']:,.0f}원" if pd.notna(fin_data['EPS']) else "-",
                "현재 PER": per_val,
                "BPS(원)": f"{fin_data['BPS']:,.0f}원" if pd.notna(fin_data['BPS']) else "-",
                "현재 PBR": pbr_val
            })

    result_df = pd.DataFrame(scan_results)

    # --- 3. 탭(Tab) 기반 화면 분리 ---
    tab1, tab2, tab3 = st.tabs(["📊 기본 & 시세", "📈 실적 & 성장성", "💰 주당 가치"])

    with tab1:
        # 기본 및 밸류에이션 (체크박스 포함)
        df_basic = result_df[["선택", "종목명", "종목코드", "현재가", "시총", "현재 PER", "현재 PBR", "배당수익률"]]
        disabled_cols1 = [c for c in df_basic.columns if c != "선택"]
        
        edited_df = st.data_editor(
            df_basic,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", default=False, width="small", pinned=True),
                "종목명": st.column_config.TextColumn("종목명", pinned=True),
            },
            disabled=disabled_cols1,
            hide_index=True,
            use_container_width=True,
            key="tab1_editor"
        )

    with tab2:
        # 실적 및 성장성
        df_perf = result_df[["종목명", "기준실적", "매출액(억)", "매출 YoY", "영업이익(억)", "당기순익(억)"]]
        st.dataframe(df_perf, hide_index=True, use_container_width=True)

    with tab3:
        # 주당 지표 (EPS/BPS/DPS)
        df_share = result_df[["종목명", "기준실적", "EPS(원)", "BPS(원)", "DPS(원)", "배당수익률"]]
        st.dataframe(df_share, hide_index=True, use_container_width=True)

    # --- 4. 컨트롤 영역 (선택 삭제 & CSV 다운로드) ---
    btn_col1, btn_col2, _ = st.columns([1.5, 2, 4])
    with btn_col1:
        delete_btn = st.button("🗑️ 선택 종목 삭제", type="primary", use_container_width=True)
    with btn_col2:
        # 전체 통합 데이터 CSV 다운로드
        csv_data = result_df.drop(columns=["선택"]).to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 전체 결과 CSV 다운로드",
            data=csv_data,
            file_name="종목Scan_전체결과.csv",
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

# --- 5. 하단 종목 추가 영역 ---
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

# --- 6. 맨 하단 출처 안내 캡션 ---
st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 실시간 연동")
