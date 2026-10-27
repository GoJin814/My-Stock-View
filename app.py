    # 2. 현재 시세 탭
    with tab2:
        edited_basic_df = render_tab_basic(df_basic)

        b_col0, b_col1, b_col2, b_col3 = st.columns([2, 1.5, 2, 2])
        
        # [현재시세 탭으로 이동된] 관심종목 추가 버튼 (실시간 동기화와 동일한 primary 스타일)
        with b_col0:
            if st.button("⭐ 선택 종목을 관심종목에 추가", type="primary", use_container_width=True, key="btn_add_watchlist_market"):
                raw_del = st.query_params.get("del_codes", "")
                selected_codes = [c.strip().zfill(6) for c in str(raw_del).split(",") if c.strip() and c.strip().isdigit()]

                if not selected_codes:
                    st.warning("⚠️ 체크박스로 선택된 종목이 없습니다. 추가할 종목을 먼저 선택해 주세요.")
                else:
                    # 관심종목 캐시 파일 로드 후 선택된 종목 일괄 추가 및 저장
                    watchlist_file = "watchlist_data.json"
                    watchlist = {}
                    if os.path.exists(watchlist_file):
                        try:
                            with open(watchlist_file, "r", encoding="utf-8") as f:
                                watchlist = json.load(f)
                        except Exception:
                            pass

                    full_csv_map = {item["종목코드"]: item for item in full_csv_records}
                    added_count = 0

                    for code in selected_codes:
                        rec = full_csv_map.get(code)
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
                                "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
                                "적용연도": prev_yr, "PER": prev_metrics["PER"], "PBR": prev_metrics["PBR"],
                                "ROE": prev_metrics["ROE"], "매출액": prev_metrics["매출액"],
                                "영업익": prev_metrics["영업익"], "당기순이익": prev_metrics["영업익"] # 영업익 중복 방지 수정
                            })
                            # 정확한 매핑 적용
                            row_list_data[-1]["당기순이익"] = prev_metrics["당기순이익"]

                        if latest_yr != "-":
                            row_list_data.append({
                                "종목코드": code, "종목명": stock_name, "현재가": curr_price_str, "시총": market_cap,
                                "적용연도": latest_yr, "PER": latest_metrics["PER"], "PBR": latest_metrics["PBR"],
                                "ROE": latest_metrics["ROE"], "매출액": latest_metrics["매출액"],
                                "영업익": latest_metrics["영업익"], "당기순이익": latest_metrics["당기순이익"]
                            })

                        watchlist[code] = row_list_data
                        added_count += 1

                    # JSON 저장 및 GitHub 커밋
                    with open(watchlist_file, "w", encoding="utf-8") as wf:
                        json.dump(watchlist, wf, ensure_ascii=False, indent=2)
                    
                    st.success(f"🎉 총 {added_count}개 종목이 관심종목에 추가되었습니다! (상단 '⭐ 관심종목' 탭에서 확인)")

        with b_col1:
            if st.button("🗑️ 선택 종목 삭제", type="primary", use_container_width=True, key="btn_del_basic"):
                ... # 기존 삭제 로직 유지
