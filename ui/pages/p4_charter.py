"""P4 宪章面板 — 已收集规则展示（纯 Streamlit 原生）"""

import streamlit as st
from engine.config_loader import get_loader
from engine.game_state import GameStateManager


def render():
    # 返回按钮
    def _on_back():
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P1"
        )
    st.button("← 返回", key="p4_back", on_click=_on_back)

    st.title("《月球宪章》")
    state = st.session_state.game_state

    # 已收集规则
    if state.collected_rules:
        loader = get_loader()
        chapter = loader.get_chapter(state.chapter_id) if state.chapter_id else None
        target_rule = chapter.target_rule if chapter else None

        for rule_id in state.collected_rules:
            if target_rule and target_rule.get("id") == rule_id:
                rule_num = rule_id.replace("rule_", "")
                with st.container(border=True):
                    st.caption(f"规则 #{rule_num}")
                    st.subheader(target_rule["name"])
                    st.write(target_rule["text"])
                    if chapter:
                        st.caption(f"来源：{chapter.title}")
    else:
        st.info("尚未收集任何规则。完成第一章的成功结局以解锁第一条规则。")

    st.divider()

    # 未解锁占位
    if "rule_001" not in state.collected_rules:
        with st.container(border=True):
            st.caption("规则 #001")
            st.subheader("???")
            st.caption("完成「断裂的脐带」成功结局后解锁")

    with st.container(border=True):
        st.caption("规则 #002")
        st.subheader("???")
        st.caption("完成「最后的窗口」成功结局后解锁")

    progress = f"{len(state.collected_rules)}/2"
    st.caption(f"进度：{progress} 条规则已收集")
