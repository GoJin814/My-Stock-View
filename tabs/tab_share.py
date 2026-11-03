from datetime import datetime

from styles import render_table


def _year_label(v, offset):
    s = str(v).strip() if v is not None else ""
    if len(s) >= 4 and s[:4].isdigit():
        return f"{s[:4]}년"
    return f"{datetime.now().year + offset}년"


def render_tab_share(df, most_prev_yr, most_latest_yr):
    prev_label = _year_label(most_prev_yr, -1)
    latest_label = _year_label(most_latest_yr, 0)

    cols = [
        {"key": "종목명", "label": "종목명", "name": True, "link": True},
        {"key": "PER_직전", "label": "PER", "group": prev_label},
        {"key": "PBR_직전", "label": "PBR", "group": prev_label},
        {"key": "ROE_직전", "label": "ROE", "group": prev_label},
        {"key": "EPS_직전", "label": "EPS", "group": prev_label},
        {"key": "BPS_직전", "label": "BPS", "group": prev_label, "divider": True},
        {"key": "PER_최근", "label": "PER", "group": latest_label},
        {"key": "PBR_최근", "label": "PBR", "group": latest_label},
        {"key": "ROE_최근", "label": "ROE", "group": latest_label},
        {"key": "EPS_최근", "label": "EPS", "group": latest_label},
        {"key": "BPS_최근", "label": "BPS", "group": latest_label},
    ]
    render_table(df, cols, "tab_share", key_col="종목코드",
                 empty_msg="표시할 주당 가치 데이터가 없습니다.")
