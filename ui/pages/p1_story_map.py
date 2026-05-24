"""P1 故事地图 — 章节目录"""

import base64
import streamlit as st
from pathlib import Path
from engine.config_loader import get_loader
from engine.game_state import GameStateManager
from ui.assets import get_background


def _img_b64(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    ext = p.suffix.lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def render():
    # 背景图
    bg_b64 = _img_b64(get_background("main.jpg"))
    if bg_b64:
        st.markdown(f"""
        <style>
        .stApp {{
            background: url({bg_b64}) center/cover no-repeat fixed;
        }}
        .stApp::before {{
            content: '';
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(13, 13, 26, 0.75);
            z-index: 0;
        }}
        .stMain > div {{ position: relative; z-index: 1; }}
        </style>
        """, unsafe_allow_html=True)

    # 返回首页
    def _to_home():
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P0"
        )
    st.button("← 返回首页", key="p1_back", on_click=_to_home)

    st.title("故事地图")

    loader = get_loader()
    all_chapters = loader.get_all_chapters()
    state = st.session_state.game_state

    for chap_id, chapter in all_chapters.items():
        is_completed = bool(state.collected_rules)

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                icon = "✓ " if is_completed else ""
                st.subheader(f"{icon}{chapter.title}")
                st.caption(chapter.subtitle)
                if is_completed:
                    st.caption(f"已收集: {len(state.collected_rules)} 条规则")
            with col2:
                def _enter_chapter(cid=chap_id):
                    st.session_state.game_state = state.model_copy(update={
                        "chapter_id": cid,
                        "current_scene": "",
                        "current_branch": None,
                        "current_beat_index": 0,
                        "turn_count": 0,
                        "dialogue_history": [],
                        "current_page": "P3",
                    })
                st.button("进入", key=f"p1_enter_{chap_id}",
                          on_click=_enter_chapter)

    # 锁定章节
    with st.container(border=True):
        st.subheader("🔒 第二章")
        st.caption("最后的窗口 — 开发中")

    # 快捷入口
    st.divider()
    def _to_charter():
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P4"
        )
    st.button("📜  查看月球宪章", key="p1_to_charter", on_click=_to_charter)
