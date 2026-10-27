import streamlit as st
import pandas as pd
import json
import os
import base64
import requests

WATCHLIST_CACHE_FILE = "watchlist_data.json"

def load_watchlist_data():
    if os.path.exists(WATCHLIST_CACHE_FILE):
        try:
            with open(WATCHLIST_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def commit_to_github(filename, content_str, commit_message="Auto-update watchlist data"):
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
        payload = {"message": commit_message, "content": content_b64, "branch": branch}
        if sha: payload["sha"] = sha
        put_res = requests.put(url, headers=headers, json=payload, timeout=7)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

def save_watchlist_data(data):
    json_text = json.dumps(data, ensure_ascii=False, indent=2)
    with open(WATCHLIST_CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(json_text)
    commit_to_github(WATCHLIST_CACHE_FILE, json_text, "Auto-commit watchlist_data.json")

def render_tab_watchlist(full_csv_records_map=None):
    st.markdown("#### ⭐ 관심종목 실적 관리")
    st.caption("현재 시세 탭에서 선택한 종목의 데이터를 직전연도/최근연도별로 완벽하게 매칭하여 2단 행으로 관리합니다.")

    watchlist = load_watchlist_data()

    query_params = st.query_params
    del_codes_str = query_params.get("del_codes", "")
    selected_codes = [c.strip().zfill(6) for c in del_codes_str.split(",") if c.strip() and c.strip().isdigit()]

    c_btn1, c_btn2 = st.columns([2, 5])
    with c_btn1:
        if st.button("📥 현재 시세 선택 종목 가져오기", type="primary", use_container_width=True):
            if not selected_codes:
                st.warning("⚠️ '현재 시세' 탭에서 체크박스로 선택된 종목이 없습니다. 현재시세 탭에서 종목을 먼저 체크해 주세요.")
            elif not full_csv_records_map:
                st.warning("⚠️ 동기화된 데이터가 없습니다. 상단의 '실시간 시세 동기화'를 먼저 실행해 주세요.")
            else:
                added_count = 0
                for code in selected_codes:
                    rec = full_csv_records_map.get(code)
                    if not rec:
                        continue
                    
                    stock_name = rec.get("종목명", f"종목_{code}")
                    curr_price_str = rec.get("현재가", "-")
                    market_cap = rec.get("시총", "-")
                    
                    prev_yr = rec.get("직전연도", "-")
                    latest_yr = rec.get("최근연도", "-")

                    def fmt_val(v, suffix=""):
                        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
                            return "-"
                        if isinstance(v, (int, float)):
                            return f"{v:,.0f}{suffix}"
                        val_str = str(v).strip()
                        if not val_str or val_str.lower() == "none":
                            return "-"
                        return f"{val_str}{suffix}"

                    def fmt_rate(v):
                        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
                            return "-"
                        if isinstance(v, (int, float)):
                            return f"{v:.2f}%"
                        val_str = str(v).strip()
                        if not val_str or val_str.lower() == "none":
                            return "-"
                        return f"{val_str}%" if not val_str.endswith("%") else val_str

                    def fmt_multi(v):
                        if v is None or pd.isna(v) or v == "-" or str(v).lower() == "none":
                            return "-"
                        val_str = str(v).strip()
                        if not val_str or val_str.lower() == "none":
                            return "-"
                        return f"{val_str}배" if not val_str.endswith("배") else val_str

                    prev_metrics = {
                        "PER": fmt_multi(rec.get("PER_직전")),
                        "PBR": fmt_multi(rec.get("PBR_직전")),
                        "ROE": fmt_rate(rec.get("ROE_직전")),
                        "매출액": fmt_val(rec.get("매출액_직전"), "억"),
                        "영업익": fmt_val(rec.get("영업익_직전"), "억"),
                        "당기순이익": fmt_val(rec.get("순이익_직전"), "억")
                    }

                    latest_metrics = {
                        "PER": fmt_multi(rec.get("PER_최근")),
                        "PBR": fmt_multi(rec.get("PBR_최근")),
                        "ROE": fmt_rate(rec.get("ROE_최근")),
                        "매출액": fmt_val(rec.get("매출액_최근"), "억"),
                        "영업익": fmt_val(rec.get("영업익_최근"), "억"),
                        "당기순이익": fmt_val(rec.get("순이익_최근"), "억")
                    }

                    row_list_data = []

                    if prev_yr != "-":
                        row_list_data.append({
                            "종목코드": code,
                            "종목명": stock_name,
                            "현재가": curr_price_str,
                            "시총": market_cap,
                            "적용연도": prev_yr,
                            "PER": prev_metrics["PER"],
                            "PBR": prev_metrics["PBR"],
                            "ROE": prev_metrics["ROE"],
                            "매출액": prev_metrics["매출액"],
                            "영업익": prev_metrics["영업익"],
                            "당기순이익": prev_metrics["당기순이익"]
                        })

                    if latest_yr != "-":
                        row_list_data.append({
                            "종목코드": code,
                            "종목명": stock_name,
                            "현재가": curr_price_str,
                            "시총": market_cap,
                            "적용연도": latest_yr,
                            "PER": latest_metrics["PER"],
                            "PBR": latest_metrics["PBR"],
                            "ROE": latest_metrics["ROE"],
                            "매출액": latest_metrics["매출액"],
                            "영업익": latest_metrics["영업익"],
                            "당기순이익": latest_metrics["당기순이익"]
                        })

                    watchlist[code] = row_list_data
                    added_count += 1

                save_watchlist_data(watchlist)
                st.success(f"🎉 총 {added_count}개 종목의 데이터가 반영되었습니다!")
                st.rerun()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택한 뒤 위 버튼을 눌러주세요.")
        return

    # 데이터프레임 구성 (선택 체크박스 컬럼 추가)
    rows = []
    for code, info_list in watchlist.items():
        if isinstance(info_list, list):
            for i, info in enumerate(info_list):
                def clean_cell(val):
                    if val is None or pd.isna(val) or str(val).strip().lower() in ["none", ""]:
                        return "-"
                    return str(val).strip()

                if i == 0:
                    rows.append({
                        "선택": False,
                        "종목코드": code,
                        "종목명": clean_cell(info.get("종목명", code)),
                        "현재가": clean_cell(info.get("현재가", "-")),
                        "시총": clean_cell(info.get("시총", "-")),
                        "적용연도": clean_cell(info.get("적용연도", "")),
                        "PER": clean_cell(info.get("PER", "-")),
                        "PBR": clean_cell(info.get("PBR", "-")),
                        "ROE": clean_cell(info.get("ROE", "-")),
                        "매출액": clean_cell(info.get("매출액", "-")),
                        "영업익": clean_cell(info.get("영업익", "-")),
                        "당기순이익": clean_cell(info.get("당기순이익", "-"))
                    })
                else:
                    rows.append({
                        "선택": False,
                        "종목코드": code,
                        "종목명": "",
                        "현재가": "",
                        "시총": "",
                        "적용연도": clean_cell(info.get("적용연도", "")),
                        "PER": clean_cell(info.get("PER", "-")),
                        "PBR": clean_cell(info.get("PBR", "-")),
                        "ROE": clean_cell(info.get("ROE", "-")),
                        "매출액": clean_cell(info.get("매출액", "-")),
                        "영업익": clean_cell(info.get("영업익", "-")),
                        "당기순이익": clean_cell(info.get("당기순이익", "-"))
                    })

    df_watch = pd.DataFrame(rows)

    st.write("")
    st.markdown("#### 📋 관심종목 리스트")
    
    # 인터랙티브 에디터블 데이터프레임으로 출력하여 체크박스 선택 가능하도록 구성
    edited_df = st.data_editor(
        df_watch,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width=50),
            "종목코드": None  # 내부 식별용이므로 화면에서는 숨김
        },
        disabled=["종목명", "현재가", "시총", "적용연도", "PER", "PBR", "ROE", "매출액", "영업익", "당기순이익"],
        hide_index=True,
        use_container_width=True,
        key="watchlist_editor"
    )

    st.write("")
    c_del1, _ = st.columns([2, 5])
    with c_del1:
        if st.button("🗑️ 선택한 관심종목 일괄 삭제", type="primary", use_container_width=True):
            # 체크된 행들의 종목코드 수집
            checked_rows = edited_df[edited_df["선택"] == True]
            codes_to_delete = checked_rows["종목코드"].dropna().unique().tolist()

            if not codes_to_delete:
                st.warning("⚠️ 삭제할 종목의 체크박스를 선택해 주세요.")
            else:
                deleted_names = []
                for code in codes_to_delete:
                    if code in watchlist:
                        first_item = watchlist[code][0] if isinstance(watchlist[code], list) else {}
                        deleted_names.append(first_item.get("종목명", code))
                        del watchlist[code]
                
                save_watchlist_data(watchlist)
                st.success(f"🗑️ 선택한 종목({', '.join(deleted_names)}) 삭제 완료")
                st.rerun()
