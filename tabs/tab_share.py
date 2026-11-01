from styles import render_table


def render_tab_share(df, prev_yr, latest_yr):
    cols = [
        {"key": "종목명", "label": "종목명", "name": True, "link": True},
        {"key": "PER_직전", "label": "PER", "group": prev_yr},
        {"key": "PBR_직전", "label": "PBR", "group": prev_yr},
        {"key": "ROE_직전", "label": "ROE", "group": prev_yr},
        {"key": "EPS_직전", "label": "EPS", "group": prev_yr},
        {"key": "BPS_직전", "label": "BPS", "group": prev_yr, "divider": True},
        {"key": "PER_최근", "label": "PER", "group": latest_yr},
        {"key": "PBR_최근", "label": "PBR", "group": latest_yr},
        {"key": "ROE_최근", "label": "ROE", "group": latest_yr},
        {"key": "EPS_최근", "label": "EPS", "group": latest_yr},
        {"key": "BPS_최근", "label": "BPS", "group": latest_yr},
    ]
    render_table(df, cols, "tab_share", key_col="종목코드",
                 empty_msg="표시할 주당 가치 데이터가 없습니다.")
