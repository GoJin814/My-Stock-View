@st.cache_data(ttl=3600, show_spinner=False)
def fetch_watchlist_item(code: str):
    """관심종목 코드를 받아 실시간으로 기본정보 및 최근/직전연도 실적을 파싱합니다."""
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

    total_infos = integration.get("totalInfos", [])
    market_cap = ""
    for item in total_infos:
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
    }

    row_list = extract_row_list(fin_json)
    if row_list:
        for row in row_list:
            raw_title = row.get("title", "").strip().replace(" ", "")
            columns = row.get("columns", {})
            if not columns:
                continue
            
            clean_years = []
            for k in columns.keys():
                yr_match = re.search(r'(20\d{2})', str(k))
                if yr_match:
                    clean_years.append((yr_match.group(1), k))
            clean_years = sorted(clean_years, key=lambda x: x[0])
            sorted_keys = [item[1] for item in clean_years]
            
            if not sorted_keys:
                continue
                
            latest_k = sorted_keys[-1]
            prev_k = sorted_keys[-2] if len(sorted_keys) >= 2 else None
            
            fin_info["latest_yr"] = f"{re.search(r'(20\d{2})', str(latest_k)).group(1)}년" if re.search(r'(20\d{2})', str(latest_k)) else ""
            fin_info["prev_yr"] = f"{re.search(r'(20\d{2})', str(prev_k)).group(1)}년" if prev_k and re.search(r'(20\d{2})', str(prev_k)) else ""

            c_item = columns.get(latest_k, {})
            c_val = to_num(c_item.get("value") if isinstance(c_item, dict) else c_item)
            p_val = np.nan
            if prev_k:
                p_item = columns.get(prev_k, {})
                p_val = to_num(p_item.get("value") if isinstance(p_item, dict) else p_item)

            if raw_title in ["매출액", "수익"]:
                fin_info["cur_rev"] = c_val
                fin_info["prev_rev"] = p_val
            elif raw_title == "영업이익":
                fin_info["cur_op"] = c_val
                fin_info["prev_op"] = p_val
            elif raw_title in ["당기순이익", "당기순익"]:
                fin_info["cur_np"] = c_val
                fin_info["prev_np"] = p_val
            elif "ROE" in raw_title:
                fin_info["cur_roe"] = c_val
                fin_info["prev_roe"] = p_val
            elif "PER" in raw_title:
                fin_info["cur_per"] = c_val
                fin_info["prev_per"] = p_val
            elif "PBR" in raw_title:
                fin_info["cur_pbr"] = c_val
                fin_info["prev_pbr"] = p_val

    def fmt_val(v, suffix=""):
        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
            return "-"
        if isinstance(v, (int, float)):
            return f"{v:,.0f}{suffix}"
        return f"{str(v).strip()}{suffix}"

    def fmt_rate(v):
        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
            return "-"
        if isinstance(v, (int, float)):
            return f"{v:.2f}%"
        return f"{str(v).strip()}%"

    def fmt_multi(v):
        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
            return "-"
        return f"{str(v).strip()}배"

    items = []
    empty_space = "\u3164"  # 렌더링 함수가 강제로 '-'로 바꾸는 것을 우회하기 위한 유니코드 공백
    
    if fin_info["prev_yr"]:
        items.append({
            "종목코드": code, 
            "종목명": stock_name if stock_name else empty_space, 
            "현재가": curr_price_str if curr_price_str else empty_space, 
            "시총": market_cap if market_cap else empty_space,
            "적용연도": fin_info["prev_yr"],
            "PER": fmt_multi(fin_info["prev_per"]),
            "PBR": fmt_multi(fin_info["prev_pbr"]),
            "ROE": fmt_rate(fin_info["prev_roe"]),
            "매출액": fmt_val(fin_info["prev_rev"], "억"),
            "영업익": fmt_val(fin_info["prev_op"], "억"),
            "당기순이익": fmt_val(fin_info["prev_np"], "억")
        })

    if fin_info["latest_yr"]:
        is_second_row = (len(items) > 0)
        items.append({
            "종목코드": code, 
            "종목명": empty_space if is_second_row else (stock_name if stock_name else empty_space), 
            "현재가": empty_space if is_second_row else (curr_price_str if curr_price_str else empty_space), 
            "시총": empty_space if is_second_row else (market_cap if market_cap else empty_space),
            "적용연도": fin_info["latest_yr"],
            "PER": fmt_multi(fin_info["cur_per"]),
            "PBR": fmt_multi(fin_info["cur_pbr"]),
            "ROE": fmt_rate(fin_info["cur_roe"]),
            "매출액": fmt_val(fin_info["cur_rev"], "억"),
            "영업익": fmt_val(fin_info["cur_op"], "억"),
            "당기순이익": fmt_val(fin_info["cur_np"], "억")
        })

    return items
