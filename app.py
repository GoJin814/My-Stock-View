import os

import pandas as pd
import streamlit as st

from styles import apply_custom_styles, inject_client_sort_sync_engine
from data import build_master, apply_sort, SORT_OPTIONS, get_raw
from store import SAVE_FILE, SORT_FILE, read_codes, write_codes, load_json, save_json
from tabs.tab_watchlist import render_tab_watchlist
from tabs.tab_basic import render_tab_basic
from tabs.tab_share import render_tab_share
from tabs.tab_perf import render_tab_perf
from tabs.tab_market import render_tab_market, render_market_inputs
from tabs.tab_returns_living import render_tab_returns_living
from tabs.tab_returns_pension import render_tab_returns_pension
from tabs.tab_returns_roun import render_tab_returns_roun
from tabs.tab_returns_jinwoo import render_tab_returns_jinwoo


st.set_page_config(page_title="Scanning", layout="wide")
apply_custom_styles()

MENUS = [
    "⭐ 관심종목", "📊 현재시세", "💰 주당가치", "📈 실적", "🌐 국내지수",
    "📈 수익률-생활비", "📈 수익률-연금", "📈 수익률-roun", "📈 수익률-진우",
]


def _mode(values):
    vals = [v for v in values if v not in ("-", "", None)]
    return max(set(vals), key=vals.count) if vals else None


# ---------- 헤더 ----------
title_col, sync_col = st.columns([5, 1.2])
with title_col:
    st.title("Scanning")
with sync_col:
    st.write("")
    if st.button("🔄 실시간 시세 동기화", use_container_width=True):
        get_raw.clear()
        st.rerun()

# ---------- 종목 목록 ----------
if not os.path.exists(SAVE_FILE):
    write_codes(SAVE_FILE, ["005930"], "Auto-commit saved_codes.txt (init)")
current_codes = read_codes(SAVE_FILE)

if not current_codes:
    st.info("등록된 종목이 없습니다. 아래에서 종목코드를 추가해 주세요.")
    with st.container(border=True):
        st.markdown("##### ➕ 종목코드 추가")
        c_code, c_btn = st.columns([3, 1])
        with c_code:
            init_code = st.text_input("종목코드 (6자리)", placeholder="예: 005930",
                                      max_chars=6, key="init_single_code")
        with c_btn:
            st.write("")
            if st.button("종목 추가", use_container_width=True, key="btn_init_add"):
                code = init_code.strip().zfill(6)
                if code.isdigit():
                    write_codes(SAVE_FILE, [code])
                    st.rerun()
    st.caption("네이버 증권 모바일 API 실시간 연동")
    st.stop()

with st.spinner(f"종목 {len(current_codes)}개 데이터를 동기화하는 중입니다..."):
    master = build_master(current_codes)

most_prev_yr = _mode(master["직전연도"].tolist()) or "2025년"
most_latest_yr = _mode(master["최근연도"].tolist()) or "2026년"

# ---------- 밸류에이션 필터 ----------
show_filter = st.toggle("🎯 밸류에이션 (PER / PBR) 범위 조건 필터링", value=False, key="tg_filter")

filter_year = f"최근 연도 ({most_latest_yr})"
use_per_filter = False
use_pbr_filter = False
per_min, per_max = 0.0, 30.0
pbr_min, pbr_max = 0.0, 3.0

if show_filter:
    with st.container():
        st.markdown('<div class="filter-container-box">', unsafe_allow_html=True)
        f_c1, f_c2, f_c3 = st.columns(3)
        with f_c1:
            filter_year = st.selectbox(
                "필터 기준 연도",
                [f"최근 연도 ({most_latest_yr})", f"직전 연도 ({most_prev_yr})"],
                key="flt_year",
            )
        with f_c2:
            use_per_filter = st.checkbox("PER 범위 필터 적용", key="flt_use_per")
            per_min = st.number_input("PER 최소값", value=0.0, step=1.0,
                                      disabled=not use_per_filter, key="flt_per_min")
            per_max = st.number_input("PER 최대값", value=30.0, step=1.0,
                                      disabled=not use_per_filter, key="flt_per_max")
        with f_c3:
            use_pbr_filter = st.checkbox("PBR 범위 필터 적용", key="flt_use_pbr")
            pbr_min = st.number_input("PBR 최소값", value=0.0, step=0.1,
                                      disabled=not use_pbr_filter, key="flt_pbr_min")
            pbr_max = st.number_input("PBR 최대값", value=3.0, step=0.1,
                                      disabled=not use_pbr_filter, key="flt_pbr_max")
        st.markdown('</div>', unsafe_allow_html=True)

prefix = "_최근" if filter_year.startswith("최근") else "_직전"
mask = pd.Series(True, index=master.index)
if use_per_filter:
    mask &= master[f"_num_PER{prefix}"].between(per_min, per_max)
if use_pbr_filter:
    mask &= master[f"_num_PBR{prefix}"].between(pbr_min, pbr_max)

# ---------- 정렬 (서버 저장 → 모든 기기 공통) ----------
labels = list(SORT_OPTIONS)
saved_sort = load_json(SORT_FILE, {"key": "등록순", "asc": True})
if saved_sort.get("key") not in SORT_OPTIONS:
    saved_sort = {"key": "등록순", "asc": True}

sc1, sc2 = st.columns([3, 2])
with sc1:
    sort_key = st.selectbox(
        "정렬 기준 (현재시세 · 주당가치 · 실적 탭 공통)",
        labels,
        index=labels.index(saved_sort["key"]),
        key="sort_key",
    )
with sc2:
    sort_dir = st.radio(
        "정렬 방향", ["오름차순", "내림차순"],
        index=0 if saved_sort.get("asc", True) else 1,
        horizontal=True, key="sort_dir",
    )

new_sort = {"key": sort_key, "asc": sort_dir == "오름차순"}
if new_sort != saved_sort:
    save_json(SORT_FILE, new_sort, "Auto-commit sort_state.json")

view = apply_sort(master[mask].reset_index(drop=True), SORT_OPTIONS[sort_key], new_sort["asc"])

# ---------- 메뉴 (URL ?menu= 에 저장 → 새로고침해도 같은 메뉴 유지) ----------
qp_menu = st.query_params.get("menu", MENUS[0])
if qp_menu not in MENUS:
    qp_menu = MENUS[0]

menu = st.segmented_control(
    "메뉴", MENUS, default=qp_menu, key="menu_sel", label_visibility="collapsed",
) or qp_menu

if st.query_params.get("menu") != menu:
    st.query_params["menu"] = menu

# ---------- 선택된 메뉴만 렌더링 (보이지 않는 탭은 실행하지 않음) ----------
if menu == "⭐ 관심종목":
    render_tab_watchlist()
elif menu == "📊 현재시세":
    render_tab_basic(view, master, current_codes)
elif menu == "💰 주당가치":
    render_tab_share(view, most_prev_yr, most_latest_yr)
elif menu == "📈 실적":
    render_tab_perf(view, most_prev_yr, most_latest_yr)
elif menu == "🌐 국내지수":
    render_tab_market()
    st.write("")
    render_market_inputs()
elif menu == "📈 수익률-생활비":
    render_tab_returns_living()
elif menu == "📈 수익률-연금":
    render_tab_returns_pension()
elif menu == "📈 수익률-roun":
    render_tab_returns_roun()
elif menu == "📈 수익률-진우":
    render_tab_returns_jinwoo()

inject_client_sort_sync_engine()

st.caption("네이버 증권 공식 모바일 API (/basic, /integration, /finance/annual) 실시간 연동")
