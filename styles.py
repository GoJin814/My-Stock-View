def render_multi_header_table(df, *args, **kwargs):
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        st.info("표시할 데이터가 없습니다.")
        return

    # 종목코드가 있다면 행 식별 속성(data-code)용으로 보관하고 화면 출력에서는 제외
    code_series = None
    if "종목코드" in df.columns:
        code_series = df["종목코드"].astype(str).str.strip().str.zfill(6)
        tab_name = kwargs.get("tab_name", "tab")
        if tab_name != "tab_basic":
            df = df.drop(columns=["종목코드"])

    header_rows = kwargs.get("header_rows", None)
    if not header_rows and args and isinstance(args[0], list):
        header_rows = args[0]

    divider_indices = kwargs.get("divider_indices", None)
    if not divider_indices and len(args) >= 2 and isinstance(args[1], list):
        divider_indices = args[1]
    div_set = set(divider_indices) if divider_indices else set()

    has_naver_link = kwargs.get("has_naver_link", True)
    tab_name = kwargs.get("tab_name", "tab")
    table_id = f"table_{tab_name}"
    has_checkbox = kwargs.get("has_checkbox", False)

    # ⚡ 확실한 흰색 굵은 구분선 인라인 스타일
    thick_style = "border-right: 2.5px solid #ffffff !important;"

    # 1. 헤더 생성
    thead_parts = ["<thead>"]
    if header_rows:
        num_header_rows = len(header_rows)
        for r_idx, row in enumerate(header_rows):
            thead_parts.append("<tr>")
            col_seq = 0 if r_idx == 0 else (1 if not has_checkbox else 2)
            cur_col_pos = 0

            for cell in row:
                r_span_val = cell.get("rowspan", 1)
                c_span_val = cell.get("colspan", 1)
                r_span = f' rowspan="{r_span_val}"' if r_span_val > 1 else ""
                c_span = f' colspan="{c_span_val}"' if c_span_val > 1 else ""
                txt = cell.get("text", "")

                th_classes = []
                th_attrs = ""

                if txt == "종목명":
                    th_classes.append("col-name-th")

                is_leaf = (r_idx + r_span_val == num_header_rows)
                if txt != "선택" and is_leaf:
                    th_classes.append("sortable-th")
                    th_attrs = f' data-col-idx="{col_seq}"'
                    col_seq += 1
                elif txt == "선택":
                    col_seq += 1

                # ⚡ 이 헤더 블록이 끝나는 열 위치 계산
                end_col_idx = cur_col_pos + c_span_val - 1
                border_inline = f' style="{thick_style}"' if (end_col_idx in div_set or cell.get("border_right", False)) else ""

                cur_col_pos += c_span_val

                class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
                thead_parts.append(f'<th{r_span}{c_span}{class_str}{th_attrs}{border_inline}>{txt}</th>')
            thead_parts.append("</tr>")
    else:
        thead_parts.append("<tr>")
        for idx, c in enumerate(df.columns):
            th_classes = []
            th_attrs = ""
            if c == "종목명":
                th_classes.append("col-name-th")
            if c != "선택":
                th_classes.append("sortable-th")
                th_attrs = f' data-col-idx="{idx}"'
            
            border_inline = f' style="{thick_style}"' if idx in div_set else ""

            class_str = f' class="{" ".join(th_classes)}"' if th_classes else ""
            thead_parts.append(f'<th{class_str}{th_attrs}{border_inline}>{c}</th>')
        thead_parts.append("</tr>")
    thead_parts.append("</thead>")

    # 2. 본문 행 생성
    tbody_parts = ["<tbody>"]
    for row_i, (_, row) in enumerate(df.iterrows()):
        code_val = ""
        if code_series is not None and row_i < len(code_series):
            code_val = code_series.iloc[row_i]
        elif "종목코드" in row:
            code_val = str(row["종목코드"]).strip().zfill(6)

        tbody_parts.append(f'<tr data-code="{code_val}">')

        for col_idx, col_name in enumerate(df.columns):
            raw_val = str(row[col_name])
            val = "-" if raw_val in ["nan", "None", ""] else raw_val
            
            # ⚡ 해당 열에 굵은 구분선 스타일 직접 적용
            border_css = thick_style if col_idx in div_set else ""

            if col_name == "선택":
                style_attr = f' style="{border_css}"' if border_css else ""
                tbody_parts.append(f'<td{style_attr}><input type="checkbox" class="stock-checkbox" data-code="{code_val}"></td>')
                continue

            if col_name == "종목명":
                td_classes = ["col-name"]
                if has_naver_link and code_val:
                    pc_url = f"https://finance.naver.com/item/main.naver?code={code_val}"
                    content = f'<a href="{pc_url}" target="_blank" class="naver-pc-link">{val}</a>'
                else:
                    content = val

                class_str = f' class="{" ".join(td_classes)}"'
                style_attr = f' style="{border_css}"' if border_css else ""
                tbody_parts.append(f'<td{class_str}{style_attr}>{content}</td>')
                continue

            color_css = ""
            if "%" in val and val != "-":
                if val.startswith("+"):
                    color_css = "color: #f87171 !important; font-weight: 500;"
                elif val.startswith("-"):
                    color_css = "color: #60a5fa !important; font-weight: 500;"

            combined_style = f"{color_css} {border_css}".strip()
            style_attr = f' style="{combined_style}"' if combined_style else ""

            tbody_parts.append(f'<td{style_attr}>{val}</td>')

        tbody_parts.append("</tr>")
    tbody_parts.append("</tbody>")

    html_code = f"""
    <div class="custom-grid-wrapper">
        <table id="{table_id}" class="custom-grid-table">
            {"".join(thead_parts)}
            {"".join(tbody_parts)}
        </table>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
