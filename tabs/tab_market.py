import streamlit as st
import pandas as pd
import json
import os
import re
import base64
import requests

MARKET_CACHE_FILE = "market_indices_cache.json"

def normalize_date(val):
    if not val or pd.isna(val):
        return ""
    val_str = str(val).strip()
    parsed = pd.to_datetime(val_str, errors='coerce')
    if pd.notnull(parsed):
        return parsed.strftime('%Y-%m-%d')
    digits = re.sub(r'[^0-9]', '', val_str)
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return val_str

def load_market_cache():
    if os.path.exists(MARKET_CACHE_FILE):
        try:
            with open(MARKET_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}

def commit_to_github(filename, content_str, commit_message="Auto-update from Streamlit"):
    """GitHub API를 통해 원본 저장소에 파일을 백그라운드로 자동 커밋"""
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    
    if not token or not repo:
        return False
        
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. 파일의 기존 SHA 조회
    res = requests.get(url, headers=headers, params={"ref": branch})
    sha = None
    if res.status_code == 200:
        sha = res.json().get("sha")
        
    # 2. Base64 인코딩 후 PUT 커밋
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
        
    put_res = requests.put(url, headers=headers, json=payload)
    return put_res.status_code in [200, 201]

def save_market_cache(cache_data):
    # 1. 로컬 컨테이너 저장
    json_text = json.dumps(cache_data, ensure_ascii=False, indent=2)
    with open(MARKET_CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(json_text)
        
    # 2. GitHub 원격 저장소 자동 커밋
    commit_to_github(MARKET_CACHE_FILE, json_text, "Auto-commit market_indices_cache.json")

def render_tab_market():
    m_cache = load_market_cache()

    if not m_cache:
        st.info("기록된 국내지수 데이터가 없습니다. 아래 패널에서 CSV/Excel 파일을 업로드하거나 수기로 등록해 주세요.")
        return None

    sorted_dates = sorted(list(m_cache.keys()), reverse=True)
    records = []
    for d in sorted_dates:
        item = m_cache[d]
        row = {
            "선택": False,
            "일시": d,
            "KOSPI": item.get("KOSPI", "-"),
            "시가총액(억원)": item.get("시가총액(억원)", "-"),
            "per": item.get("per", item.get("PER", item.get("KOSPI_PER_최근", "-"))),
            "pbr": item.get("pbr", item.get("PBR", item.get("KOSPI_PBR_최근", "-"))),
            "고객예탁금(억원)": item.get("고객예탁금(억원)", "-"),
            "신용잔고(억원)": item.get("신용잔고(억원)", "-"),
            "환율": item.get("환율", item.get("환율(원)", "-"))
        }
        records.append(row)

    df_market = pd.DataFrame(records)

    html_parts = [
        '<div style="overflow-x: auto; margin-bottom: 1rem;">',
        '<table style="width: 100%; border-collapse: collapse; font-size: 0.82rem; text-align: center;">',
        '<thead>',
        '<tr style="background-color: var(--secondary-background-color, #f0f2f6); color: var(--text-color, #31333F);">',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 10px;">선택</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">일시</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">KOSPI</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">시가총액(억원)</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">per</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">pbr</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">고객예탁금(억원)</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">신용잔고(억원)</th>',
        '<th style="border: 1px solid rgba(128,128,128,0.3); padding: 8px 12px;">환율</th>',
        '</tr>',
        '</thead>',
        '</table>',
        '</div>'
    ]
    st.markdown("".join(html_parts), unsafe_allow_html=True)

    disabled_cols = [c for c in df_market.columns if c != "선택"]
    edited_df = st.data_editor(
        df_market,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width="small"),
            "일시": st.column_config.TextColumn("일시", width="medium"),
            "per": st.column_config.TextColumn("per"),
            "pbr": st.column_config.TextColumn("pbr"),
        },
        disabled=disabled_cols,
        hide_index=True,
        use_container_width=True,
        key="market_monitor_editor"
    )

    json_bytes = json.dumps(m_cache, ensure_ascii=False, indent=2).encode('utf-8')
    st.download_button(
        "💾 국내지수 전체 백업(JSON 다운로드)",
        data=json_bytes,
        file_name="market_indices_backup.json",
        mime="application/json",
        help="서버가 재부팅되더라도 언제든 복원할 수 있도록 지수 데이터를 파일로 저장합니다."
    )

    return edited_df

def render_market_inputs():
    with st.expander("🌐 국내지수 데이터 파일 업로드(CSV / Excel) 및 수기 등록", expanded=False):
        t_upload, t_manual, t_restore = st.tabs(["📊 CSV / Excel 파일 일괄 업로드", "✍️ 개별 수기 입력", "📂 백업 파일(JSON) 복원"])

        # 1. CSV / Excel 파일 일괄 업로드
        with t_upload:
            st.write("보유하고 계신 **CSV 또는 Excel(.xlsx)** 파일을 업로드하면 날짜별 데이터가 자동으로 병합/추가됩니다.")
            market_file = st.file_uploader(
                "지수 데이터 파일 선택 (일시, KOSPI, 시가총액, PER, PBR 등)",
                type=["csv", "xlsx", "xls"],
                key="market_csv_excel_uploader"
            )
            if market_file is not None:
                if st.button("📥 파일 데이터 읽어서 추가하기", type="primary", key="btn_apply_market_file"):
                    try:
                        if market_file.name.endswith(".csv"):
                            try:
                                df_up = pd.read_csv(market_file, encoding="utf-8")
                            except UnicodeDecodeError:
                                market_file.seek(0)
                                df_up = pd.read_csv(market_file, encoding="cp949")
                        else:
                            df_up = pd.read_excel(market_file)

                        df_up.columns = [str(c).replace(" ", "").strip() for c in df_up.columns]

                        date_col = None
                        for c in df_up.columns:
                            if any(k in c for k in ["일시", "날짜", "Date", "DATE"]):
                                date_col = c
                                break

                        if not date_col:
                            st.error("파일에서 '일시' 또는 '날짜' 컬럼을 찾을 수 없습니다.")
                        else:
                            cache = load_market_cache()
                            added_count = 0

                            for _, r in df_up.iterrows():
                                raw_d = str(r[date_col]).strip()
                                d_str = normalize_date(raw_d)
                                if not d_str:
                                    continue

                                if d_str not in cache:
                                    cache[d_str] = {}

                                for col in df_up.columns:
                                    if col == date_col:
                                        continue
                                    val_str = str(r[col]).strip()
                                    if val_str in ["nan", "None", ""]:
                                        val_str = "-"

                                    if "시가총액" in col:
                                        cache[d_str]["시가총액(억원)"] = val_str
                                    elif "고객예탁금" in col or "예탁금" in col:
                                        cache[d_str]["고객예탁금(억원)"] = val_str
                                    elif "신용잔고" in col or "신용융자" in col:
                                        cache[d_str]["신용잔고(억원)"] = val_str
                                    elif "환율" in col:
                                        cache[d_str]["환율"] = val_str
                                    elif col.upper() == "PER":
                                        cache[d_str]["per"] = val_str
                                    elif col.upper() == "PBR":
                                        cache[d_str]["pbr"] = val_str
                                    elif col in ["KOSPI", "코스피"]:
                                        cache[d_str]["KOSPI"] = val_str
                                    else:
                                        cache[d_str][col] = val_str

                                added_count += 1

                            save_market_cache(cache)
                            st.success(f"총 {added_count}개 일자의 지수 데이터가 성공적으로 반영 및 GitHub에 자동 커밋되었습니다!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")

        # 2. KOSPI 전용 개별 수기 입력
        with t_manual:
            c_date, _ = st.columns([2, 4])
            with c_date:
                input_date = st.date_input("기준 일자", key="market_input_date")
            date_str = str(input_date)

            st.write("**KOSPI 및 시장 매크로 데이터 입력**")
            r1_c1, r1_c2, r1_c3 = st.columns(3)
            with r1_c1:
                in_kospi = st.text_input("KOSPI 지수", placeholder="예: 2528.92", key="man_kospi")
            with r1_c2:
                in_mcap = st.text_input("시가총액(억원)", placeholder="예: 20,712,779", key="man_mcap")
            with r1_c3:
                in_fx = st.text_input("환율", placeholder="예: 1455.5", key="man_fx")

            r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
            with r2_c1:
                in_per = st.text_input("per", placeholder="예: 13.32", key="man_per")
            with r2_c2:
                in_pbr = st.text_input("pbr", placeholder="예: 0.89", key="man_pbr")
            with r2_c3:
                in_deposit = st.text_input("고객예탁금(억원)", placeholder="예: 572,328", key="man_deposit")
            with r2_c4:
                in_credit = st.text_input("신용잔고(억원)", placeholder="예: 181,786", key="man_credit")

            if st.button("📌 수기 데이터 저장", type="primary", key="btn_save_market"):
                cache = load_market_cache()
                if date_str not in cache:
                    cache[date_str] = {}
                cache[date_str].update({
                    "KOSPI": in_kospi.strip() or "-",
                    "시가총액(억원)": in_mcap.strip() or "-",
                    "per": in_per.strip() or "-",
                    "pbr": in_pbr.strip() or "-",
                    "고객예탁금(억원)": in_deposit.strip() or "-",
                    "신용잔고(억원)": in_credit.strip() or "-",
                    "환율": in_fx.strip() or "-",
                })
                save_market_cache(cache)
                st.success(f"{date_str} KOSPI 데이터가 저장 및 GitHub에 자동 커밋되었습니다.")
                st.rerun()

        # 3. JSON 백업 복원 탭
        with t_restore:
            up_json = st.file_uploader("백업받은 market_indices_backup.json 업로드", type=["json"], key="json_backup_restore")
            if up_json is not None:
                if st.button("📥 백업 데이터 즉시 복원", type="primary", key="btn_restore_json"):
                    try:
                        content = json.load(up_json)
                        if isinstance(content, dict):
                            cache = load_market_cache()
                            cache.update(content)
                            save_market_cache(cache)
                            st.success(f"총 {len(content)}일자의 지수 데이터가 복원 및 GitHub에 자동 커밋되었습니다.")
                            st.rerun()
                        else:
                            st.error("올바른 JSON 형식의 백업 파일이 아닙니다.")
                    except Exception as e:
                        st.error(f"복원 중 오류 발생: {e}")
