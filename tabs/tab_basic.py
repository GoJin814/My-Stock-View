import html as _html

import pandas as pd
import streamlit as st

from tabs.sel_table import selectable_table

BASIC_CSS = (
    "<style>"
    ".bs-wrap{overflow-x:auto;margin-bottom:1rem;border:1px solid #334155;border-radius:4px;background:#0e1117;}"
    "table.bs-table{border-collapse:separate;border-spacing:0;width:max-content;min-width:100%;"
    "font-size:0.82rem;color:#f3f4f6;background:#0e1117;"
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;}"
    "table.bs-table th{position:sticky;top:0;z-index:10;background:#161a22;color:#9ca3af;"
    "font-weight:500;font-size:0.81rem;padding:6px 10px;border-bottom:2px solid #334155;"
    "border-right:1px solid #262c36;text-align:center;white-space:nowrap;vertical-align:middle;}"
    "table.bs-table td{background:#0e1117;padding:8px 10px;border-right:1px solid #1e242c;"
    "border-bottom:1px solid #1e242c;text-align:right;white-space:nowrap;vertical-align:middle;"
    "font-variant-numeric:tabular-nums;}"
    "table.bs-table .c-chk{position:sticky;left:0;z-index:5;width:34px;min-width:34px;max-width:34px;"
    "padding:6px 0;text-align:center;background:#0e1117;}"
    "table.bs-table th.c-chk{z-index:100;background:#161a22;}"
    "table.bs-table .c-name{position:sticky;left:34px;z-index:5;background:#0e1117;"
    "width:calc(5em + 14px);min-width:calc(5em + 14px);max-width:calc(5em + 14px);"
    "text-align:left;padding:8px 6px 8px 8px;white-space:normal;word-break:break-all;line-height:1.3;}"
    "table.bs-table th.c-name{z-index:100;background:#161a22;text-align:center;}"
    "table.bs-table a.naver-link{color:#58a6ff !important;text-decoration:none !important;}"
    "table.bs-table .c-code{color:#94a3b8;font-family:monospace;font-size:0.72rem;margin-top:2px;}"
    "table.bs-table input[type=checkbox]{cursor:pointer;width:16px;height:16px;accent-color:#3b82f6;vertical-align:middle;}"
    "</style>"
)

# 표에서 따로 그리는 열(체크박스, 종목명 링크, 종목코드)은 제외한다
EXCLUDE_COLS = {"선택", "종목명", "종목코드"}


def _build_html(df):
    cols = [c for c in df.columns if c not in EXCLUDE_COLS and not str(c).startswith("_")]

    head = (
        '<th class="c-chk"><input type="checkbox" class="header-select-all" title="전체 선택"></th>'
        '<th class="c-name">종목명</th>'
        + "".join(f"<th>{_html.escape(str(c))}</th>" for c in cols)
    )

    body = []
    for _, row in df.iterrows():
        code = str(row.get("종목코드", "")).strip().zfill(6)
        name = _html.escape(str(row.get("종목명", "-")))
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        body.append("<tr>")
        body.append(
            f'<td class="c-chk"><input type="checkbox" class="stock-checkbox" data-code="{code}"></td>'
        )
        body.append(
            f'<td class="c-name"><a class="naver-link" target="_blank" href="{url}">{name}</a>'
            f'<div class="c-code">{code}</div></td>'
        )
        for c in cols:
            v = row.get(c, "-")
            s = "-" if pd.isna(v) else str(v)
            # 배당금 등 <br>이 들어 있는 셀은 이스케이프하지 않는다
            cell = s if "<br>" in s else _html.escape(s)
            body.append(f"<td>{cell}</td>")
        body.append("</tr>")

    return (
        BASIC_CSS
        + '<div class="bs-wrap">'
        + f'<table class="bs-table"><thead><tr>{head}</tr></thead>'
        + f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def render_tab_basic(df: pd.DataFrame):
    """현재시세 표를 그리고, 체크된 종목코드 목록(list)을 반환한다."""
    if df is None or df.empty:
        st.info("표시할 종목 데이터가 없습니다.")
        return []

    html = _build_html(df)
    return selectable_table(html, key="basic_sel", frame_h=200) or []
