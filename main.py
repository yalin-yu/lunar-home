"""月球宪章 — 主入口"""

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="月球宪章",
    page_icon="🌙",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---- 全局 CSS（最小化，只做必要的视觉微调）----

def inject_minimal_css():
    st.markdown("""
    <style>
    .stApp { background: #0d0d1a; color: #e0e0e0; }
    header { display: none; }
    .stMain { padding: 0; max-width: 480px; margin: 0 auto; }
    .stButton > button {
        border-radius: 8px; border: 1px solid #4A90D9;
        background: rgba(74,144,217,0.08); color: #e0e0e0;
        padding: 10px 16px; font-size: 0.9rem; width: 100%;
        text-align: left; white-space: normal; min-height: 44px;
    }
    .stButton > button:hover { background: rgba(74,144,217,0.2); border-color: #7ab8ff; }
    .stButton > button:disabled { opacity: 0.4; border-color: #3A3A5C; color: #666; }
    hr { border-color: rgba(255,255,255,0.08); margin: 12px 0; }
    .stChatMessage { background: rgba(0,0,0,0.3) !important; }
    </style>
    """, unsafe_allow_html=True)


# ---- 配置 & 状态初始化 ----

@st.cache_resource
def init_config():
    from engine.config_loader import init_loader
    config_dir = Path(__file__).parent / "config"
    return init_loader(str(config_dir))


def init_game_state():
    from engine.models import GameState
    if "game_state" not in st.session_state:
        st.session_state.game_state = GameState()


def switch_page(page: str):
    from engine.game_state import GameStateManager
    st.session_state.game_state = GameStateManager.navigate_to_page(
        st.session_state.game_state, page
    )


# ---- 路由 ----

def main():
    inject_minimal_css()
    init_config()
    init_game_state()

    state = st.session_state.game_state
    page = state.current_page

    if page == "P0":
        from ui.pages import p0_home
        p0_home.render()
    elif page == "P1":
        from ui.pages import p1_story_map
        p1_story_map.render()
    elif page == "P2":
        from ui.pages import p2_scene
        p2_scene.render()
    elif page == "P3":
        from ui.pages import p3_chapter_map
        p3_chapter_map.render()
    elif page == "P4":
        from ui.pages import p4_charter
        p4_charter.render()
    elif page == "P5":
        from ui.pages import p5_ending
        p5_ending.render()
    else:
        st.error(f"未知页面: {page}")


if __name__ == "__main__":
    main()
