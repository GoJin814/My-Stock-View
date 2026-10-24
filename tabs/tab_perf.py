import pandas as pd
from styles import render_multi_header_table

def render_tab_perf(df_perf: pd.DataFrame, prev_yr: str, latest_yr: str):
    top_headers_perf = [
        ("종목명", 1, False),
        (prev_yr, 3, True),
        (latest_yr, 3, True),
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
