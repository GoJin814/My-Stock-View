import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import json
import requests
from concurrent.futures import ThreadPoolExecutor

# Firebase Admin SDK 연동
import firebase_admin
from firebase_admin import credentials, db

from styles import apply_custom_styles, inject_client_sort_sync_engine
from api import fetch_basic, fetch_integration, fetch_finance, extract_row_list, to_num
from tabs.tab_watchlist import render_tab_watchlist
from tabs.tab_basic import render_tab_basic
from tabs.tab_share import render_tab_share
from tabs.tab_perf import render_tab_perf
from tabs.tab_market import render_tab_market, render_market_inputs, load_market_cache, save_market_cache
from tabs.tab_returns_living import render_tab_returns_living
from tabs.tab_returns_pension import render_tab_returns_pension
from tabs.tab_returns_roun import render_tab_returns_roun
from tabs.tab_returns_jinwoo import render_tab_returns_jinwoo

st.set_page_config(page_title="Scanning", layout="wide")
apply_custom_styles()

SAVE_FILE = "saved_codes.txt"


# -------------------------------------------------------------
# 0. 공통 유틸
# -------------------------------------------------------------
def dedupe_codes(codes):
    """종목코드 목록을 6자리 문자열로 정규화하고 중복을 제거한다 (순서 유지)."""
    out = []
    for c in codes:
        s = str(c).strip()
        if s.isdigit():
            z = s.zfill(6)
            if z not in out:
                out.append(z)
    return out


def _yr(k):
    """'2025', '2025/12', 'IFRS(연결)2025' 등에서 연도만 추출"""
    m = re.search(r"(20\d{2})", str(k))
    return f"{m.group(1)}년" if m else "-"


# -------------------------------------------------------------
# 1. Firebase 초기화 및 동기화 함수
# -------------------------------------------------------------
if not firebase_admin._apps:
    try:
        cred_dict = dict(st.secrets["firebase"])
        db_url = cred_dict.pop("databaseURL", "https://my-stock-view-default-rtdb.firebaseio.com")
        if "private_key" in cred_dict and isinstance(cred_dict["private_key"], str):
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {"databaseURL": db_url})
    except Exception as e:
        st.error(f"⚠️ Firebase 초기화 실패: {e}")


def load_codes():
    """Firebase에서 정렬 순서(sort_order)를 우선 불러오고, 없으면 saved_codes를 사용한다."""
    try:
        synced_order = db.reference("my_stock_view/sort_order").get()
        if synced_order and isinstance(synced_order, list):
            cleaned_order = dedupe_codes(synced_order)
            if cleaned_order:
                return cleaned_order

        codes = db.reference("my_stock_view/saved_codes").get()
        if codes and isinstance(codes, list):
            cleaned = dedupe_codes(codes)
            if cleaned:
                return cleaned
    except Exception:
        pass

    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            codes = dedupe_codes(f.readlines())
            if codes:
                return codes

    default_codes = ["005930"]
    save_codes(default_codes)
    return default_codes


def save_codes(codes):
    """종목코드 목록 저장 (Firebase + 로컬 파일)"""
    cleaned = dedupe_codes(codes)
    try:
        db.reference("my_stock_view/saved_codes").set(cleaned)
    except Exception as e:
        st.error(f"⚠️ Firebase 저장 실패: {e}")

    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned) + "\n")


def get_synced_sort_order():
    """모든 기기 간 공유되는 종목 정렬 순서 가져오기"""
    try:
        order = db.reference("my_stock_view/sort_order").get()
        if order and isinstance(order, list):
            return dedupe_codes(order)
    except Exception:
        pass
    return None


def load_filter_settings():
    """Firebase에서 동기화된 필터 설정 가져오기"""
    default = {"show_filter": False, "filter_year_idx": 0,
               "use_per": False, "per_range": [0.0, 30.0],
               "use_pbr": False, "pbr_range": [0.0, 3.0]}
    try:
        data = db.reference("my_stock_view/filter_settings").get()
        if data and isinstance(data, dict):
            return {**default, **data}
    except Exception:
        pass
    return default


def save_filter_settings(settings):
    """필터 변경 시 Firebase에 즉시 저장"""
    try:
        db.reference("my_stock_view/filter_settings").set(settings)
    except Exception:
        pass


def save_synced_sort_order(order_list):
    """정렬 순서를 중복 없이 Firebase에 저장"""
    try:
        cleaned = dedupe_codes(order_list)
        if cleaned:
            db.reference("my_stock_view/sort_order").set(cleaned)
    except Exception:
        pass


def apply_order(df, order):
    """데이터프레임 행을 정렬 순서(order)대로 재배열한다."""
    if df is None or df.empty or "종목코드" not in df.columns or not order:
        return df
    order_map = {c: i for i, c in enumerate(order)}
    codes = df["종목코드"].astype(str).str.zfill(6)
    return (df.assign(_rank=codes.map(lambda c: order_map.get(c, 9999)))
              .sort_values("_rank", kind="stable")
              .drop(columns="_rank")
              .reset_index(drop=True))


# -------------------------------------------------------------
# 2. 증권 데이터 수집 엔진
# -------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_single_stock(code: str):
    basic = fetch_basic(code)
    integration = fetch_integration(code)
    fin_json = fetch_finance(code)

    stock_name = basic.get("stockName", "-")
    raw_close = basic.get("closePrice", "-")
    curr_price_str = f"{raw_close}원" if (raw_close != "-" and "원" not in str(raw_close)) else str(raw_close)
    numeric_close = to_num(raw_close)

    total_infos = integration.get("totalInfos", [])
    market_cap = "-"
    integration_dict = {}
    for item in total_infos:
        item_code = str(item.get("code", "")).strip()
        item_key = str(item.get("key", "")).strip()
        item_val = str(item.get("value", "")).strip()
        if item_code == "marketValue" or item_key in ["시총", "시가총액"]:
            market_cap = item_val
        integration_dict[item_key] = item_val

    raw_per = basic.get("per", integration_dict.get("PER", "-"))
    raw_pbr = basic.get("pbr", integration_dict.get("PBR", "-"))

    per_val = f"{str(raw_per).replace('배', '')}배" if raw_per not in ["-", "N/A", None] else "-"
    pbr_val = f"{str(raw_pbr).replace('배', '')}배" if raw_pbr not in ["-", "N/A", None] else "-"

    fin_info = {
        "latest_yr": "-", "prev_yr": "-",
