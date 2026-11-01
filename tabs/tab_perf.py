from styles import render_table


def render_tab_perf(df, prev_yr, latest_yr):
    cols = [
        {"key": "종목명", "label": "종목명", "name": True, "link": True},
        {"key": "매출_직전", "label": "매출액", "group": prev_yr},
        {"key": "영업익_직전", "label": "영업이익", "group": prev_yr},
        {"key": "순익_직전", "label": "당기순익", "group": prev_yr, "divider": True},
        {"key": "매출_최근", "label": "매출액", "group": latest_yr},
        {"key": "영업익_최근", "label": "영업이익", "group": latest_yr},
        {"key": "순익_최근", "label": "당기순익", "group": latest_yr, "divider": True},
        {"key": "매출_YoY", "label": "매출액", "group": "YoY 성장률"},
        {"key": "영업익_YoY", "label": "영업이익", "group": "YoY 성장률"},
        {"key": "순익_YoY", "label": "당기순익", "group": "YoY 성장률"},
    ]
    render_table(df, cols, "tab_perf", key_col="종목코드",
                 empty_msg="표시할 실적 데이터가 없습니다.")
