"""P5 结局展示 — 成功/非正常结局（纯 Streamlit 原生）"""

import streamlit as st
from engine.config_loader import get_loader
from engine.game_state import GameStateManager
from engine.models import EndingType


def render():
    state = st.session_state.game_state

    # 判断结局类型：优先检查是否有成功结局
    if "ending_success" in state.completed_endings:
        _render_success(state)
    elif state.collected_rules and "rule_001" in state.collected_rules:
        _render_success(state)
    else:
        _render_failure(state)


def _render_success(state):
    loader = get_loader()
    # 居中布局
    _, col, _ = st.columns([1, 3, 1])
    with col:
        st.markdown("## ✦")
        st.header("结局达成")

    st.divider()

    # 规则卡片
    chapter = loader.get_chapter(state.chapter_id) if state.chapter_id else None
    target_rule = chapter.target_rule if chapter else None

    if target_rule:
        with st.container(border=True):
            st.caption("《月球宪章》第一条")
            st.subheader(target_rule["name"])
            st.write(target_rule["text"])
            st.caption("✦ 已收录 ✦")

    # 尾声旁白
    ending = None
    if chapter:
        for e in chapter.endings:
            if e.type == EndingType.SUCCESS:
                ending = e
                break
    if ending:
        st.markdown(f"*{ending.epilogue_narration}*")

    st.divider()

    def _to_map():
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P1"
        )
    st.button("▶ 返回故事地图", key="success_back",
              on_click=_to_map, use_container_width=True)


def _render_failure(state):
    # 居中布局
    _, col, _ = st.columns([1, 3, 1])
    with col:
        st.markdown("## ✦ 脐带断了 ✦")

    st.divider()

    st.markdown(
        "你的方案未能获得两站关键人员的支持。在密闭的月球基地中，"
        "信任一旦流失就难以重建。但这不是终点——你可以重新尝试。"
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        def _retry():
            st.session_state.game_state = st.session_state.game_state.model_copy(
                update={
                    "current_page": "P2",
                    "turn_count": 0,
                    "dialogue_history": [],
                }
            )
        st.button("⟳ 重新挑战", key="failure_retry",
                  on_click=_retry, use_container_width=True)
    with col2:
        def _to_map():
            st.session_state.game_state = GameStateManager.navigate_to_page(
                st.session_state.game_state, "P1"
            )
        st.button("↩ 返回地图", key="failure_back",
                  on_click=_to_map, use_container_width=True)
