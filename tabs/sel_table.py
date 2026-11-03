import os
import streamlit.components.v1 as components

_COMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "components", "sel_table")
_sel_table = components.declare_component("sel_table", path=os.path.abspath(_COMP_DIR))


def selectable_table(html, key, frame_h=400):
    """HTML 표를 iframe 안에 그리고, 체크된 종목코드 목록(list)을 반환한다."""
    return _sel_table(html=html, frame_h=frame_h, key=key, default=[])
