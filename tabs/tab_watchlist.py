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
    st.markdown("#### ⭐ 관심종목 실적 관리 (초고속 메모리 연동)")
    st.caption("현재 시세 탭에서 선택한 종목의 데이터를 이미 로드된 메모리에서 즉시 불러와 2단 행으로 관리합니다.")

    watchlist = load_watchlist_data()

    query_params = st.query_params
    del_codes_str = query_params.get("del_codes", "")
    selected_codes = [c.strip().zfill(6) for c in del_codes_str.split(",") if c.strip() and c.strip().isdigit()]

    c_btn1, c_btn2 = st.columns([2, 5])
    with c_btn1:
        if st.button("📥 현재 시세 선택 종목 가져오기", type="primary", use_container_width=True):
            if not selected_codes:
                st.warning("⚠️ '현재 시세' 탭에서 체크박스로 선택된 종목이 없습니다.")
            elif not full_csv_records_map:
                st.warning("⚠️ 동기화된 종목 데이터가 없습니다. 상단의 '실시간 시세 동기화'를 먼저 실행해 주세요.")
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

                    per_val = rec.get("현재PER", "-")
                    pbr_val = rec.get("현재PBR", "-")

                    def fmt_val(v, suffix=""):
                        if v is None or pd.isna(v) or v == "-":
                            return "-"
                        if isinstance(v, (int, float)):
                            return f"{v:,.0f}{suffix}"
                        return f"{v}{suffix}"

                    prev_metrics = {
                        "ROE": f"{rec.get('ROE_직전', 0):.2f}%" if pd.notna(rec.get('ROE_직전')) else "-",
                        "매출액": fmt_val(rec.get('매출액_직전'), "억"),
                        "영업익": fmt_val(rec.get('영업익_직전'), "억"),
                        "당기순이익": fmt_val(rec.get('순이익_직전'), "억")
                    }

                    latest_metrics = {
                        "ROE": f"{rec.get('ROE_최근', 0):.2f}%" if pd.notna(rec.get('ROE_최근')) else "-",
                        "매출액": fmt_val(rec.get('매출액_최근'), "억"),
                        "영업익": fmt_val(rec.get('영업익_최근'), "억"),
                        "당기순이익": fmt_val(rec.get('순이익_최근'), "억")
                    }

                    row_list_data = []

                    if prev_yr != "-":
                        row_list_data.append({
                            "종목명": stock_name,
                            "현재가": curr_price_str,
                            "시총": market_cap,
                            "적용연도": prev_yr,
                            "PER": per_val,
                            "PBR": pbr_val,
                            "ROE": prev_metrics["ROE"],
                            "매출액": prev_metrics["매출액"],
                            "영업익": prev_metrics["영업익"],
                            "당기순이익": prev_metrics["당기순이익"]
                        })

                    if latest_yr != "-":
                        row_list_data.append({
                            "종목명": stock_name,
                            "현재가": curr_price_str,
                            "시총": market_cap,
                            "적용연도": latest_yr,
                            "PER": per_val,
                            "PBR": pbr_val,
                            "ROE": latest_metrics["ROE"],
                            "매출액": latest_metrics["매출액"],
                            "영업익": latest_metrics["영업익"],
                            "당기순이익": latest_metrics["당기순이익"]
                        })

                    watchlist[code] = row_list_data
                    added_count += 1

                save_watchlist_data(watchlist)
                st.success(f"🎉 총 {added_count}개 종목의 데이터가 메모리에서 즉시 로드되어 반영되었습니다!")
                st.rerun()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택한 뒤 위 버튼을 눌러주세요.")
        return

    rows = []
    for code, info_list in watchlist.items():
        if isinstance(info_list, list):
            for i, info in enumerate(info_list):
                if i == 0:
                    rows.append({
                        "종목명": info.get("종목명", code),
                        "현재가": info.get("현재가", "-"),
                        "시총": info.get("시총", "-"),
                        "적용연도": info.get("적용연도", ""),
                        "PER": info.get("PER", "-"),
                        "PBR": info.get("PBR", "-"),
                        "ROE": info.get("ROE", "-"),
                        "매출액": info.get("매출액", "-"),
                        "영업익": info.get("영업익", "-"),
                        "당기순이익": info.get("당기순이익", "-")
                    })
                else:
                    rows.append({
                        "종목명": "",
                        "현재가": "",
                        "시총": "",
                        "적용연도": info.get("적용연도", ""),
                        "PER": info.get("PER", "-"),
                        "PBR": info.get("PBR", "-"),
                        "ROE": info.get("ROE", "-"),
                        "매출액": info.get("매출액", "-"),
                        "영업익": info.get("영업익", "-"),
                        "당기순이익": info.get("당기순이익", "-")
                    })
        elif isinstance(info_list, dict):
            rows.append(info_list)
    
    df_watch = pd.DataFrame(rows)

    st.write("")
    st.markdown("#### 📋 관심종목 리스트")
    st.dataframe(df_watch, hide_index=True, use_container_width=True)

    st.write("")
    with st.expander("🗑️ 관심종목 개별 관리 (삭제)"):
        options_map = {}
        for code, info_list in watchlist.items():
            first_item = info_list[0] if isinstance(info_list, list) and len(info_list) > 0 else info_list
            s_name = first_item.get("종목명", code) if isinstance(first_item, dict) else code
            options_map[f"{s_name} ({code})"] = code

        selected_option = st.selectbox("삭제할 종목 선택", options=list(options_map.keys()), key="watch_del_select")
        
        if st.button("선택 종목 삭제", type="primary", key="watch_del_btn"):
            target_code = options_map[selected_option]
            if target_code in watchlist:
                del watchlist[target_code]
                save_watchlist_data(watchlist)
                st.success(f"종목 '{selected_option}' 삭제 완료")
                st.rerun()
