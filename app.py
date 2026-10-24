import streamlit as st
import requests
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Scanning_주식", layout="wide")

# 표 글자 크기, 컴팩트 스타일 및 연도 구분 굵은 경계선 스타일 적용
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

/* HTML 테이블 스타일: 직전/마지막 연도 구분선 */
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
.compare-table tr:hover td {
    background-color: #374151;
}
/* 연도 블록 경계선 (굵은 구분선) */
.compare-table .year-divider {
    border-right: 3px solid #9ca3af !important;
}
/* 종목명 고정 스타일 */
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

# HTML 렌더링 헬퍼 (굵은 세로 구분선 포함)
def render_styled_table(df: pd.DataFrame, divider_col: str):
    cols = list(df.columns)
    th_html = ""
    for i, col in enumerate(cols):
        classes = []
        if i == 0:
            classes.append("sticky-col sticky-header")
        if col == divider_col:
            classes.append("year-divider")
        class_str = f' class="{" ".join(classes)}"' if classes else ""
        th_html += f"<th{class_str}>{col}</th>"

    tb_html = ""
    for _, row in df.iterrows():
        tb_html += "<tr>"
        for i, col in enumerate(cols):
            val = row[col]
            classes = []
            if i == 0:
                classes.append("sticky-col")
            if col == divider_col:
                classes.append("year-divider")
            class_str = f' class="{" ".join(classes)}"' if classes else ""
            tb_html += f"<td{class_str}>{val}</td>"
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

# --- 2. 데이터 수집 및 2개 연도 비교 파싱 ---
if current_codes:
    scan_basic = []
    scan_perf = []
    scan_share = []
    full_csv_records = []
    
    with st.spinner("네이버 증권 데이터를 동기화하고 있습니다..."):
        for code in current_codes:
            basic = fetch_basic(code)
            integration = fetch_integration(code)
            fin_json = fetch_finance(code)
            
            stock_name = basic.get("stockName", "-")
            raw_close = basic.get("closePrice", "-")
            curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)
            
            # 시총 추출
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

            # 재무제표: 직전 연도(prev)와 마지막 연도(latest) 동시 추출
            fin_info = {
                "latest_yr": "-", "prev_yr": "-",
                "cur_rev": np.nan, "prev_rev": np.nan, "rev_yoy": np.nan,
                "cur_op": np.nan,  "prev_op": np.nan,  "op_yoy": np.nan,
                "cur_np": np.nan,  "prev_np": np.nan,
                "cur_eps": np.nan, "prev_eps": np.nan,
                "cur_bps": np.nan, "prev_bps": np.nan,
                "cur_dps": np.nan, "prev_dps": np.nan
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

                    # 최신값 및 직전값
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
                    elif raw_title in ["수정주당순이익(원)", "주당순이익(원)", "EPS"]:
                        fin_info["cur_eps"] = c_val
                        fin_info["prev_eps"] = p_val
                    elif raw_title in ["주당순자산(원)", "주당순자산가치(원)", "BPS"]:
                        fin_info["cur_bps"] = c_val
                        fin_info["prev_bps"] = p_val
                    elif raw_title in ["주당배당금(원)", "주당배당금", "DPS"]:
                        fin_info["cur_dps"] = c_val
                        fin_info["prev_dps"] = p_val

            # 1) 기본 탭 데이터
            scan_basic.append({
                "선택": False,
                "종목명": stock_name,
                "종목코드": code,
                "현재가": curr_price_str,
                "시총": market_cap,
                "현재 PER": per_val,
                "현재 PBR": pbr_val,
                "배당수익률": div_val
            })

            # 2) 실적 비교 탭 데이터 (좌: 직전연도, 우: 마지막연도)
            prev_label = f"({fin_info['prev_yr']})" if fin_info['prev_yr'] != "-" else "(직전)"
            latest_label = f"({fin_info['latest_yr']})" if fin_info['latest_yr'] != "-" else "(마지막)"

            scan_perf.append({
                "종목명": stock_name,
                f"매출액 {prev_label}": f"{fin_info['prev_rev']:,.0f}억" if pd.notna(fin_info['prev_rev']) else "-",
                f"영업익 {prev_label}": f"{fin_info['prev_op']:,.0f}억" if pd.notna(fin_info['prev_op']) else "-",
                f"순이익 {prev_label}": f"{fin_info['prev_np']:,.0f}억" if pd.notna(fin_info['prev_np']) else "-",
                # 우측 마지막 연도
                f"매출액 {latest_label}": f"{fin_info['cur_rev']:,.0f}억" if pd.notna(fin_info['cur_rev']) else "-",
                "매출 YoY": f"{fin_info['rev_yoy']:+.1f}%" if pd.notna(fin_info['rev_yoy']) else "-",
                f"영업익 {latest_label}": f"{fin_info['cur_op']:,.0f}억" if pd.notna(fin_info['cur_op']) else "-",
                "영업익 YoY": f"{fin_info['op_yoy']:+.1f}%" if pd.notna(fin_info['op_yoy']) else "-",
                f"순이익 {latest_label}": f"{fin_info['cur_np']:,.0f}억" if pd.notna(fin_info['cur_np']) else "-"
            })

            # 3) 주당 가치 비교 탭 데이터 (좌: 직전연도, 우: 마지막연도)
            scan_share.append({
                "종목명": stock_name,
                f"EPS {prev_label}": f"{fin_info['prev_eps']:,.0f}원" if pd.notna(fin_info['prev_eps']) else "-",
                f"BPS {prev_label}": f"{fin_info['prev_bps']:,.0f}원" if pd.notna(fin_info['prev_bps']) else "-",
                f"DPS {prev_label}": f"{fin_info['prev_dps']:,.0f}원" if pd.notna(fin_info['prev_dps']) else "-",
                # 우측 마지막 연도
                f"EPS {latest_label}": f"{fin_info['cur_eps']:,.0f}원" if pd.notna(fin_info['cur_eps']) else "-",
                f"BPS {latest_label}": f"{fin_info['cur_bps']:,.0f}원" if pd.notna(fin_info['cur_bps']) else "-",
                f"DPS {latest_label}": f"{fin_info['cur_dps']:,.0f}원" if pd.notna(fin_info['cur_dps']) else "-",
                "배당수익률": div_val
            })

            # 통합 CSV 레코드
            full_csv_records.append({
                "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
                "직전연도": fin_info['prev_yr'], "최근연도": fin_info['latest_yr'],
                "매출액_직전": fin_info['prev_rev'], "매출액_최근": fin_info['cur_rev'], "매출_YoY": fin_info['rev_yoy'],
                "영업익_직전": fin_info['prev_op'], "영업익_최근": fin_info['cur_op'], "영업익_YoY": fin_info['op_yoy'],
                "순이익_직전": fin_info['prev_np'], "순이익_최근": fin_info['cur_np'],
                "EPS_직전": fin_info['prev_eps'], "EPS_최근": fin_info['cur_eps'],
                "BPS_직전": fin_info['prev_bps'], "BPS_최근": fin_info['cur_bps'],
                "DPS_직전": fin_info['prev_dps'], "DPS_최근": fin_info['cur_dps'],
                "PER": per_val, "PBR": pbr_val, "배당수익률": div_val
            })

    df_basic = pd.DataFrame(scan_basic)
    df_perf = pd.DataFrame(scan_perf)
    df_share = pd.DataFrame(scan_share)

    # --- 3. 탭 렌더링 ---
    tab1, tab2, tab3 = st.tabs(["📊 기본 & 시세", "📈 실적 & 성장성 (2개년 비교)", "💰 주당 가치 (2개년 비교)"])

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
        # 직전 연도 블록의 마지막 열 뒤에 굵은 구분선 적용
        divider_col_perf = df_perf.columns[3]  # 순이익 (직전) 컬럼
        render_styled_table(df_perf, divider_col=divider_col_perf)

    with tab3:
        # 직전 연도 블록의 마지막 열 뒤에 굵은 구분선 적용
        divider_col_share = df_share.columns[3]  # DPS (직전) 컬럼
        render_styled_table(df_share, divider_col=divider_col_share)

    # --- 4. 컨트롤 영역 ---
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
st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 실시간 연동")
