"""저장소 유틸: 로컬 파일 + GitHub 백업(비동기), 쿼리파라미터 헬퍼."""
import os
import json
import base64
import logging
from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st

SAVE_FILE = "saved_codes.txt"
WATCHLIST_FILE = "watchlist_codes.txt"
SORT_FILE = "sort_state.json"
MARKET_CACHE_FILE = "market_indices_cache.json"
THRESHOLDS_FILE = "market_thresholds.json"

log = logging.getLogger("store")
# 커밋은 한 번에 하나씩 순서대로 실행 (sha 충돌 방지). UI는 기다리지 않는다.
_COMMIT_POOL = ThreadPoolExecutor(max_workers=1)


def _gh_cfg():
    """st.secrets는 메인 스레드에서만 읽는다."""
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo = st.secrets.get("GITHUB_REPO")
        branch = st.secrets.get("GITHUB_BRANCH", "main")
    except Exception:
        return None
    if not token or not repo:
        return None
    return str(token).strip(), str(repo).strip(), str(branch).strip()


def _gh_put(cfg, filename, content, msg):
    token, repo, branch = cfg
    url = f"https://api.github.com/repos/{repo}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        res = requests.get(url, headers=headers, params={"ref": branch}, timeout=10)
        sha = res.json().get("sha") if res.status_code == 200 else None
        payload = {
            "message": msg,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        put = requests.put(url, headers=headers, json=payload, timeout=10)
        if put.status_code not in (200, 201):
            log.warning("GitHub 커밋 실패 (%s): %s", put.status_code, filename)
    except Exception as e:
        log.warning("GitHub 통신 에러 (%s): %s", filename, e)


def save_text(filename, content, msg=None):
    """로컬에 즉시 저장하고 GitHub 백업은 백그라운드로 보낸다."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    cfg = _gh_cfg()
    if cfg:
        _COMMIT_POOL.submit(_gh_put, cfg, filename, content, msg or f"Auto-update {filename}")


def load_text(filename, default=""):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return default


def load_json(filename, default):
    try:
        data = json.loads(load_text(filename, ""))
        if isinstance(data, type(default)):
            return data
    except Exception:
        pass
    return default


def save_json(filename, obj, msg=None):
    save_text(filename, json.dumps(obj, ensure_ascii=False, indent=2), msg)


def read_codes(filename):
    out, seen = [], set()
    for line in load_text(filename, "").splitlines():
        s = line.strip()
        if s.isdigit():
            c = s.zfill(6)
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


def write_codes(filename, codes, msg=None):
    cleaned = list(dict.fromkeys(
        str(c).strip().zfill(6) for c in codes if str(c).strip().isdigit()
    ))
    content = "\n".join(cleaned) + ("\n" if cleaned else "")
    save_text(filename, content, msg or f"Auto-commit {filename} ({len(cleaned)} stocks)")


# ---- 쿼리파라미터 헬퍼 ----
def qp_list(key):
    raw = st.query_params.get(key, "")
    if isinstance(raw, list):
        raw = ",".join(raw)
    return list(dict.fromkeys(s.strip() for s in str(raw).split(",") if s.strip()))


def qp_codes(key):
    return list(dict.fromkeys(c.zfill(6) for c in qp_list(key) if c.isdigit()))


def qp_clear(key):
    if key in st.query_params:
        del st.query_params[key]
