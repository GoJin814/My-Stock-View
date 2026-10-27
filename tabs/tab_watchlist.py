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
    st.caption("'현재 시세' 탭에서 추가한 관심종목의 직전/최근연도 실적 데이터를 2단 행으로 관리합니다.")

    watchlist = load_watchlist_data()

    if not watchlist:
        st.info("등록된 관심종목이 없습니다. '현재 시세' 탭에서 종목을 선택하고 [관심종목 추가] 버튼을 눌러주세요.")
        return

    # 데이터프레임 구성 (전체 행에 반영할 일괄 선택 상태 반영)
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
    
    # 상단 전체 선택 체크박스 제공
    col_sel, _ = st.columns([1, 4])
    with col_sel:
        select_all = st.checkbox("전체 선택 / 해제", key="watchlist_select_all")

    if select_all:
        df_watch["선택"] = True

    edited_df = st.data_editor(
        df_watch,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", default=False, width=50),
            "종목코드": None
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
