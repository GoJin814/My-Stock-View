import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import re
import base64
import requests
from tabs.tab_returns_pension import to_num, fmt_won, fmt_pct, render_input_panel

CACHE_FILE = "returns_jinwoo.json"

def load_data():
    defaults = {"cash_balance": 0, "years": {}}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict) and "years" in saved: return saved
        except Exception: pass
    return defaults

def save_data(data):
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(CACHE_FILE, "w", encoding="utf-8") as f: f.write(json_text)
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    if token and repo:
        url = f"https://api.github.com/repos/{repo}/contents/{CACHE_FILE}"
        headers = {"Authorization": f"Bearer {token.strip()}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        try:
            res = requests.get(url, headers=headers, params={"ref": branch}, timeout=7)
            sha = res.json().get("sha") if res.status_code == 200 else None
            content_b64 = base64.b64encode(json_text.encode("utf-8")).decode("utf-8")
            payload = {"message": "Auto-update returns jinwoo", "content": content_b64, "branch": branch}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload, timeout=7)
        except Exception: pass

def render_tab_returns_jinwoo():
    data = load_data()
    cash_bal = float(data.get("cash_balance", 0))
    years_data = data.get("years", {})

    st.markdown("##### 📌 잔여 예수금 설정 (셀 B1)")
    c_cash, _ = st.columns([2, 5])
    with c_cash:
        new_cash = st.number_input("잔여 예수금 (원)", value=int(cash_bal), step=1000, format="%d", key="jinwoo_cash")
        if new_cash != cash_bal:
            data["cash_balance"] = new_cash; save_data(data); st.rerun()

    sorted_years = sorted(list(years_data.keys()))
    if not sorted_years:
        st.info("등록된 연도별 데이터가 없습니다. 아래에서 데이터를 추가해 주세요.")
        render_input_panel(data, "jinwoo")
        return

    year_records = []
    tot_in = 0.0; tot_out = 0.0; first_start = 0.0; latest_end = 0.0; yearly_rates = []

    for idx, yr in enumerate(sorted_years):
        row = years_data[yr]
        b_start = to_num(row.get("start", 0))
        c_in = to_num(row.get("in", 0))
        d_out = to_num(row.get("out", 0))
        f_end = to_num(row.get("end", 0))
        if idx == 0: first_start = b_start
        if idx == len(sorted_years) - 1: latest_end = f_end
        tot_in += c_in; tot_out += d_out
        e_net_in = c_in - d_out
        g_profit = f_end - b_start - c_in + d_out
        denom = b_start + (0.5 * c_in) - (0.5 * d_out)
        h_rate = ((f_end - b_start - (c_in - d_out)) / denom * 100.0) if denom != 0 else 0.0
        yearly_rates.append(h_rate)
        year_records.append({
            "연도": yr, "시작": fmt_won(b_start), "입고": fmt_won(c_in), "출고": fmt_won(d_out),
            "순 입금액": fmt_won(e_net_in), "종료": fmt_won(f_end), "총 수익": fmt_won(g_profit),
            "총 수익률*": fmt_pct(h_rate), "_num_rate": h_rate, "_profit": g_profit
        })

    tot_net_in = tot_in - tot_out
    tot_final_end = latest_end
    tot_profit = tot_final_end - first_start - tot_in + tot_out + float(new_cash)
    tot_denom = first_start + float(new_cash) + (0.5 * tot_in) - (0.5 * tot_out)
    tot_rate = ((tot_final_end + float(new_cash) - first_start - (tot_in - tot_out)) / tot_denom * 100.0) if tot_denom != 0 else 0.0

    n_years = len(yearly_rates)
    if n_years > 0:
        product_val = 1.0
        for r in yearly_rates: product_val *= (1.0 + (r / 100.0))
        avg_yearly_rate = (pow(product_val, 1.0 / n_years) - 1.0) * 100.0
    else: avg_yearly_rate = 0.0

    summary_record = [{
        "구분": "전체", "시작": fmt_won(first_start), "입고": fmt_won(tot_in), "출고": fmt_won(tot_out),
        "순 입금액": fmt_won(tot_net_in), "종료": fmt_won(tot_final_end), "총 수익": fmt_won(tot_profit),
        "총 수익률*": fmt_pct(tot_rate), "전체 기간\n평균 수익률": fmt_pct(avg_yearly_rate)
    }]

    st.markdown("#### 📊 전체 기간 성과 요약 (진우)")
    st.dataframe(pd.DataFrame(summary_record), hide_index=True, use_container_width=True)

    st.write("")
    st.markdown("#### 📅 연도별 현황 (진우)")
    def style_performance(row):
        styles = [''] * len(row)
        if pd.notna(row["_num_rate"]) and row["_num_rate"] > 0: styles[row.index.get_loc("총 수익률*")] = 'color: #ff4b4b; font-weight: bold;'
        elif pd.notna(row["_num_rate"]) and row["_num_rate"] < 0: styles[row.index.get_loc("총 수익률*")] = 'color: #60a5fa; font-weight: bold;'
        if pd.notna(row["_profit"]) and row["_profit"] > 0: styles[row.index.get_loc("총 수익")] = 'color: #ff4b4b; font-weight: bold;'
        elif pd.notna(row["_profit"]) and row["_profit"] < 0: styles[row.index.get_loc("총 수익")] = 'color: #60a5fa; font-weight: bold;'
        return styles

    df_years = pd.DataFrame(year_records)
    st.dataframe(df_years.style.apply(style_performance, axis=1), hide_index=True, use_container_width=True)
    st.write("")
    render_input_panel(data, "jinwoo")
