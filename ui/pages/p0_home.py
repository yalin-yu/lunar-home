"""P0 首页"""

import base64
import streamlit as st
from pathlib import Path
from ui.assets import get_ui_asset, get_background


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

    st.title("月球宪章")
    st.caption("Moon Charter — 互动叙事游戏")

    # 世界观简述
    from engine.config_loader import get_loader
    loader = get_loader()
    world = loader.get_world_premise()

    with st.container(border=True):
        for line in world.strip().split("\n"):
            line = line.strip()
            if not line:
                st.write("")
            else:
                st.write(line)

    st.divider()

    def _to_story_map():
        from engine.game_state import GameStateManager
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P1"
        )

    def _to_charter():
        from engine.game_state import GameStateManager
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P4"
        )

    st.button("▶  进入故事地图", key="btn_story_map",
              type="primary", on_click=_to_story_map, use_container_width=True)
    st.button("📜  查看月球宪章", key="btn_charter",
              on_click=_to_charter, use_container_width=True)
