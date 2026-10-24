import streamlit as st
import pandas as pd

CUSTOM_CSS = """
<style>
div[data-testid="stDataEditor"] { font-size: 13px !important; }
div[data-testid="stDataEditor"] [role="gridcell"],
div[data-testid="stDataEditor"] [role="columnheader"] { font-size: 13px !important; }
div[data-testid="stDataEditor"] .dvn-scroller { line-height: 1.2 !important; }

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
.compare-table th { background-color: #111827; font-weight: 600; }
.compare-table th.group-header {
    background-color: #0f172a;
    font-size: 14px;
    color: #93c5fd;
    letter-spacing: 0.5px;
}
.compare-table tr:hover td { background-color: #374151; }
.compare-table .year-divider { border-right: 3px solid #9ca3af !important; }
.compare-table .sticky-col {
    position: sticky;
    left: 0;
    background-color: #1f2937;
    z-index: 2;
    font-weight: bold;
    border-right: 2px solid #4b5563;
}
.compare-table th.sticky-header { background-color: #111827; z-index: 3; }
</style>
"""

def apply_custom_styles():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_multi_header_table(df: pd.DataFrame, top_headers: list, sub_headers: list, divider_indices: list):
    top_th_html = ""
    for title, colspan, is_divider in top_headers:
        divider_cls = " year-divider" if is_divider else ""
        if title in ["종목명", "일시"]:
            top_th_html += f'<th rowspan="2" class="sticky-col sticky-header">{title}</th>'
        else:
            top_th_html += f'<th colspan="{colspan}" class="group-header{divider_cls}">{title}</th>'

    sub_th_html = "".join([
        f'<th class="{" year-divider" if idx in divider_indices else ""}">{col_title}</th>'
        for idx, col_title in enumerate(sub_headers, start=1)
    ])

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
            <thead>
                <tr>{top_th_html}</tr>
                <tr>{sub_th_html}</tr>
            </thead>
            <tbody>{tb_html}</tbody>
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

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
