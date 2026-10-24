import pandas as pd
from styles import render_multi_header_table

def render_tab_share(df_share: pd.DataFrame, prev_yr: str, latest_yr: str):
    top_headers_share = [
        ("종목명", 1, False),
        (prev_yr, 5, True),
        (latest_yr, 5, False)
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
