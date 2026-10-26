import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import base64
import requests

CACHE_FILE = "returns_jinwoo.json"

def to_num(val):
    if val is None or str(val).strip() in ["", "-", "None", "nan"]:
        return 0.0
    try:
        clean = re.sub(r'[^0-9.-]', '', str(val))
        return float(clean) if clean else 0.0
    except Exception:
        return 0.0

def fmt_won(val):
    if pd.isna(val) or val is None:
        return "-"
    return f"{int(round(val)):,}"

def fmt_pct(val):
    if pd.isna(val) or val is None:
        return "-"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.2f}%"

def load_data():
    defaults = {"cash_balance": 0, "years": {}}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict) and "years" in saved:
                    return saved
        except Exception:
            pass
    return defaults

def commit_to_github(filename, content_str):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    if not token or not repo:
        return False
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {"Authorization": f"Bearer {token.strip()}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    try:
        res = requests.get(url, headers=headers, params={"ref": branch}, timeout=7)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        payload = {"message": "Auto-update returns jinwoo", "content": content_b64, "branch": branch}
        if sha: payload["sha"] = sha
        put_res = requests.put(url, headers=headers, json=payload, timeout=7)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

def save_data(data):
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(json_text)
    commit_to_github(CACHE_FILE, json_text)

def render_tab_returns_jinwoo():
    data = load_data()
    cash_bal = float(data.get("cash_balance", 0))
    years_data = data.get("years", {})

    st.markdown("##### 📌 잔여 예수금 설정 (셀 B1)")
    c_cash, _ = st.columns([2, 5])
    with c_cash:
        new_cash = st.number_input("잔여 예수금 (원)", value=int(cash_bal), step=1000, format="%d", key="jinwoo_cash")
        if new_cash != cash_bal:
            data["cash_balance"] = new_cash
            save_data(data)
            st.rerun()

    sorted_years = sorted(list(years_data.keys()))
    if not sorted_years:
        st.info("등록된 연도별 데이터가 없습니다. 아래에서 데이터를 추가해 주세요.")
        render_input_panel(data, "jinwoo")
        return

    year_records = []
    tot_in = 0.0
    tot_out = 0.0
    first_start = 0.0
    latest_end = 0.0
    yearly_rates = []

    for idx, yr in enumerate(sorted_years):
        row = years_data[yr]
        b_start = to_num(row.get("start", 0))
        c_in = to_num(row.get("in", 0))
        d_out = to_num(row.get("out", 0))
        f_end = to_num(row.get("end", 0))

        if idx == 0: first_start = b_start
        if idx == len(sorted_years) - 1: latest_end = f_end

        tot_in += c_in
        tot_out += d_out
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
    else:
        avg_yearly_rate = 0.0

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
    st.dataframe(
        df_years.style.apply(style_performance, axis=1),
        column_config={"_num_rate": None, "_profit": None},
        hide_index=True,
        use_container_width=True
    )
    st.write("")
    render_input_panel(data, "jinwoo")

def render_input_panel(data, prefix="jinwoo"):
    show_box = st.toggle("✍️ 연도별 현황 등록 / 수정 / 삭제", value=False, key=f"{prefix}_toggle")
    if show_box:
        with st.container():
            t_add, t_del = st.tabs(["➕ 연도별 데이터 입력/수정", "🗑️ 연도 삭제"])
            with t_add:
                r1_c1, r1_c2 = st.columns(2)
                with r1_c1: in_year = st.text_input("연도 (예: 2026)", key=f"{prefix}_yr")
                with r1_c2: in_start = st.text_input("시작 기초자산(원)", key=f"{prefix}_st")
                r2_c1, r2_c2, r2_c3 = st.columns(3)
                with r2_c1: in_in = st.text_input("입고(원)", key=f"{prefix}_in")
                with r2_c2: in_out = st.text_input("출고(원)", key=f"{prefix}_out")
                with r2_c3: in_end = st.text_input("종료 기말자산(원)", key=f"{prefix}_end")
                if st.button("💾 연도 데이터 저장", type="primary", use_container_width=True, key=f"{prefix}_sv"):
                    if in_year.strip():
                        y_key = str(in_year).strip()
                        if "years" not in data: data["years"] = {}
                        data["years"][y_key] = {"start": to_num(in_start), "in": to_num(in_in), "out": to_num(in_out), "end": to_num(in_end)}
                        save_data(data)
                        st.success(f"{y_key}년 데이터 저장 완료")
                        st.rerun()
            with t_del:
                existing_years = sorted(list(data.get("years", {}).keys()), reverse=True)
                if existing_years:
                    del_yr = st.selectbox("삭제할 연도 선택", options=existing_years, key=f"{prefix}_del_sel")
                    if st.button(f"🗑️ {del_yr}년 데이터 삭제", type="primary", key=f"{prefix}_del_btn"):
                        del data["years"][del_yr]
                        save_data(data)
                        st.success(f"{del_yr}년 데이터 삭제 완료")
                        st.rerun()
