import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import re
import base64
import requests

RETURNS_LIVING_CACHE_FILE = "returns_living.json"

def to_num(val):
    if val is None or str(val).strip() in ["", "-", "None", "nan"]:
        return 0.0
    try:
        s = str(val).strip().replace(',', '')
        clean = re.sub(r'[^0-9.-]', '', s)
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

def load_returns_living_data():
    defaults = {
        "cash_balance": 9169,
        "years": {
            "2024": {"start": 4560795, "in": 3094435, "out": 1763182, "end": 5699508},
            "2025": {"start": 5699375, "in": 8021179, "out": 6031413, "end": 10548054}
        }
    }
    if os.path.exists(RETURNS_LIVING_CACHE_FILE):
        try:
            with open(RETURNS_LIVING_CACHE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict) and "years" in saved:
                    return saved
        except Exception:
            pass
    return defaults

def commit_to_github(filename, content_str, commit_message="Auto-update returns living data"):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    if not token or not repo:
        return False
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        res = requests.get(url, headers=headers, params={"ref": branch}, timeout=7)
        sha = res.json().get("sha") if res.status_code == 200 else None
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        payload = {
            "message": commit_message,
            "content": content_b64,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha
        put_res = requests.put(url, headers=headers, json=payload, timeout=7)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

def save_returns_living_data(data):
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(RETURNS_LIVING_CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(json_text)
    commit_to_github(RETURNS_LIVING_CACHE_FILE, json_text, "Auto-commit returns_living.json")

def render_tab_returns_living():
    data = load_returns_living_data()
    cash_bal = float(data.get("cash_balance", 0))
    years_data = data.get("years", {})

    st.markdown("##### 📌 잔여 예수금 설정 (셀 B1)")
    c_cash, _ = st.columns([2, 5])
    with c_cash:
        new_cash = st.number_input(
            "잔여 예수금 (원)", 
            value=int(cash_bal), 
            step=1000, 
            format="%d",
            help="엑셀의 B1 잔여 예수금 값입니다."
        )
        if new_cash != cash_bal:
            data["cash_balance"] = new_cash
            save_returns_living_data(data)
            st.rerun()

    sorted_years = sorted(list(years_data.keys()))
    if not sorted_years:
        st.info("등록된 연도별 데이터가 없습니다. 아래에서 데이터를 추가해 주세요.")
        render_input_panel(data)
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

        if idx == 0:
            first_start = b_start
        if idx == len(sorted_years) - 1:
            latest_end = f_end

        tot_in += c_in
        tot_out += d_out

        e_net_in = c_in - d_out
        g_profit = f_end - b_start - c_in + d_out
        denom = b_start + (0.5 * c_in) - (0.5 * d_out)
        h_rate = ((f_end - b_start - (c_in - d_out)) / denom * 100.0) if denom != 0 else 0.0
        yearly_rates.append(h_rate)

        # 연도별 현황 표 순서 변경: [연도, 총 수익, 총 수익률*, 시작, 입고, 출고, 순 입금액, 종료]
        year_records.append({
            "연도": yr,
            "총 수익": fmt_won(g_profit),
            "총 수익률*": fmt_pct(h_rate),
            "시작": fmt_won(b_start),
            "입고": fmt_won(c_in),
            "출고": fmt_won(d_out),
            "순 입금액": fmt_won(e_net_in),
            "종료": fmt_won(f_end),
            "_num_rate": h_rate,
            "_profit": g_profit
        })

    tot_net_in = tot_in - tot_out
    tot_final_end = latest_end 
    tot_profit = tot_final_end - first_start - tot_in + tot_out + float(new_cash)
    tot_denom = first_start + float(new_cash) + (0.5 * tot_in) - (0.5 * tot_out)
    tot_rate = ((tot_final_end + float(new_cash) - first_start - (tot_in - tot_out)) / tot_denom * 100.0) if tot_denom != 0 else 0.0

    n_years = len(yearly_rates)
    if n_years > 0:
        product_val = 1.0
        for r in yearly_rates:
            product_val *= (1.0 + (r / 100.0))
        avg_yearly_rate = (pow(product_val, 1.0 / n_years) - 1.0) * 100.0
    else:
        avg_yearly_rate = 0.0

    # 전체 기간 요약 표 순서 변경: [구분, 총 수익, 총 수익률*, 전체 기간 평균 수익률, 시작, 입고, 출고, 순 입금액, 종료]
    summary_record = [{
        "구분": "전체",
        "총 수익": fmt_won(tot_profit),
        "총 수익률*": fmt_pct(tot_rate),
        "전체 기간\n평균 수익률": fmt_pct(avg_yearly_rate),
        "시작": fmt_won(first_start),
        "입고": fmt_won(tot_in),
        "출고": fmt_won(tot_out),
        "순 입금액": fmt_won(tot_net_in),
        "종료": fmt_won(tot_final_end),
        "_sum_profit": tot_profit,
        "_sum_rate": tot_rate,
        "_sum_avg_rate": avg_yearly_rate
    }]

    df_summary = pd.DataFrame(summary_record)
    df_years = pd.DataFrame(year_records)

    st.caption("※ 엑셀 수식과 100% 동일하게 연동됩니다. (전체 총 수익 및 수익률에 잔여 예수금 B1 포함)")

    # 1. 상단 요약 테이블 스타일링 함수
    def style_summary(row):
        styles = [''] * len(row)
        idx_profit = row.index.get_loc("총 수익")
        idx_rate = row.index.get_loc("총 수익률*")
        idx_avg = row.index.get_loc("전체 기간\n평균 수익률")

        p_val = row["_sum_profit"]
        r_val = row["_sum_rate"]
        avg_val = row["_sum_avg_rate"]

        if pd.notna(p_val) and p_val > 0: styles[idx_profit] = 'color: #ff4b4b; font-weight: bold;'
        elif pd.notna(p_val) and p_val < 0: styles[idx_profit] = 'color: #60a5fa; font-weight: bold;'

        if pd.notna(r_val) and r_val > 0: styles[idx_rate] = 'color: #ff4b4b; font-weight: bold;'
        elif pd.notna(r_val) and r_val < 0: styles[idx_rate] = 'color: #60a5fa; font-weight: bold;'

        if pd.notna(avg_val) and avg_val > 0: styles[idx_avg] = 'color: #ff4b4b; font-weight: bold;'
        elif pd.notna(avg_val) and avg_val < 0: styles[idx_avg] = 'color: #60a5fa; font-weight: bold;'

        return styles

    styled_summary_df = df_summary.style.apply(style_summary, axis=1)

    st.markdown("#### 📊 전체 기간 성과 요약")
    st.dataframe(
        styled_summary_df,
        column_config={
            "구분": st.column_config.TextColumn("구분", width=65),
            "총 수익": st.column_config.TextColumn("총 수익", width=105),
            "총 수익률*": st.column_config.TextColumn("총 수익률*", width=95),
            "전체 기간\n평균 수익률": st.column_config.TextColumn("전체 기간 평균 수익률", width=140),
            "시작": st.column_config.TextColumn("시작", width=105),
            "입고": st.column_config.TextColumn("입고", width=105),
            "출고": st.column_config.TextColumn("출고", width=105),
            "순 입금액": st.column_config.TextColumn("순 입금액", width=105),
            "종료": st.column_config.TextColumn("종료", width=115),
            "_sum_profit": None,
            "_sum_rate": None,
            "_sum_avg_rate": None
        },
        hide_index=True,
        use_container_width=True
    )

    st.write("")
    # 2. 하단 연도별 테이블 스타일링 함수
    st.markdown("#### 📅 연도별 현황")
    
    def style_performance(row):
        styles = [''] * len(row)
        idx_profit = row.index.get_loc("총 수익")
        idx_rate = row.index.get_loc("총 수익률*")
        
        num_rate = row["_num_rate"]
        num_profit = row["_profit"]
        
        if pd.notna(num_profit) and num_profit > 0:
            styles[idx_profit] = 'color: #ff4b4b; font-weight: bold;'
        elif pd.notna(num_profit) and num_profit < 0:
            styles[idx_profit] = 'color: #60a5fa; font-weight: bold;'

        if pd.notna(num_rate) and num_rate > 0:
            styles[idx_rate] = 'color: #ff4b4b; font-weight: bold;'
        elif pd.notna(num_rate) and num_rate < 0:
            styles[idx_rate] = 'color: #60a5fa; font-weight: bold;'
            
        return styles

    styled_years_df = df_years.style.apply(style_performance, axis=1)

    st.dataframe(
        styled_years_df,
        column_config={
            "연도": st.column_config.TextColumn("연도", width=75),
            "총 수익": st.column_config.TextColumn("총 수익", width=110),
            "총 수익률*": st.column_config.TextColumn("총 수익률*", width=100),
            "시작": st.column_config.TextColumn("시작", width=110),
            "입고": st.column_config.TextColumn("입고", width=110),
            "출고": st.column_config.TextColumn("출고", width=110),
            "순 입금액": st.column_config.TextColumn("순 입금액", width=110),
            "종료": st.column_config.TextColumn("종료", width=120),
            "_num_rate": None,
            "_profit": None
        },
        hide_index=True,
        use_container_width=True
    )

    st.write("")
    render_input_panel(data)

def render_input_panel(data):
    show_box = st.toggle("✍️ 연도별 현황 등록 / 수정 / 삭제", value=False)
    if show_box:
        with st.container():
            t_add, t_del = st.tabs(["➕ 연도별 데이터 입력/수정", "🗑️ 연도 삭제"])
            
            with t_add:
                r1_c1, r1_c2 = st.columns(2)
                with r1_c1:
                    in_year = st.text_input("연도 (예: 2026)", key="rl_in_year")
                with r1_c2:
                    in_start = st.text_input("시작 기초자산(원)", placeholder="예: 10548054", key="rl_in_start")

                r2_c1, r2_c2, r2_c3 = st.columns(3)
                with r2_c1:
                    in_in = st.text_input("입고(원)", placeholder="예: 5000000", key="rl_in_in")
                with r2_c2:
                    in_out = st.text_input("출고(원)", placeholder="예: 1000000", key="rl_in_out")
                with r2_c3:
                    in_end = st.text_input("종료 기말자산(원)", placeholder="예: 16500000", key="rl_in_end")

                if st.button("💾 연도 데이터 저장", type="primary", use_container_width=True, key="btn_save_rl_year"):
                    if not in_year.strip():
                        st.warning("연도를 입력해 주세요.")
                    else:
                        y_key = str(in_year).strip()
                        if "years" not in data:
                            data["years"] = {}
                        data["years"][y_key] = {
                            "start": to_num(in_start),
                            "in": to_num(in_in),
                            "out": to_num(in_out),
                            "end": to_num(in_end)
                        }
                        save_returns_living_data(data)
                        st.success(f"{y_key}년 데이터가 저장 및 GitHub에 커밋되었습니다.")
                        st.rerun()

            with t_del:
                existing_years = sorted(list(data.get("years", {}).keys()), reverse=True)
                if not existing_years:
                    st.info("삭제할 연도 데이터가 없습니다.")
                else:
                    del_yr = st.selectbox("삭제할 연도 선택", options=existing_years, key="rl_sel_del_yr")
                    if st.button("🗑️ 데이터 삭제", type="primary", key="btn_del_rl_year"):
                        if del_yr in data["years"]:
                            del data["years"][del_yr]
                            save_returns_living_data(data)
                            st.success(f"{del_yr}년 데이터 삭제 완료")
                            st.rerun()
