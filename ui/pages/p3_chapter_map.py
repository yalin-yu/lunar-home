"""P3 章节路线图 — 网状节点+分支并列布局"""

import streamlit as st
from engine.config_loader import get_loader
from engine.branch_manager import BranchManager
from engine.game_state import GameStateManager


def render():
    state = st.session_state.game_state
    loader = get_loader()
    chapter = loader.get_chapter(state.chapter_id)

    # 返回 P1
    def _to_story_map():
        st.session_state.game_state = GameStateManager.navigate_to_page(
            st.session_state.game_state, "P1"
        )
    st.button("← 返回故事地图", key="p3_back", on_click=_to_story_map)

    st.title(chapter.title)
    st.caption(chapter.core_conflict)
    st.divider()

    flow_nodes = chapter.flow.get("chapter_map_nodes", [])

    # ---- 将节点按阶段分组 ----
    phases = _group_into_phases(flow_nodes)

    for i, group in enumerate(phases):
        # 阶段之间的箭头
        if i > 0:
            _, col, _ = st.columns([5, 1, 5])
            with col:
                st.markdown(
                    "<p style='text-align:center;color:#4A90D9;margin:0;font-size:1.2rem;'>↓</p>",
                    unsafe_allow_html=True,
                )

        nodes = group["nodes"]
        if len(nodes) == 1:
            _render_node(nodes[0], state, chapter)
        else:
            # 多节点（分支并列）：横向排列
            cols = st.columns(len(nodes))
            for j, node in enumerate(nodes):
                with cols[j]:
                    _render_node(node, state, chapter, compact=True)

    # 进度摘要
    st.divider()
    total_branches = len([n for n in flow_nodes if n["id"].startswith("branch_")])
    completed = len(state.completed_branches)
    st.caption(
        f"分支进度: {completed}/{total_branches}  |  "
        f"已收集规则: {len(state.collected_rules)} 条"
    )


def _group_into_phases(flow_nodes: list[dict]) -> list[dict]:
    """将节点按故事阶段分组，分支节点合并为并列组"""
    phases = []
    i = 0
    while i < len(flow_nodes):
        node = flow_nodes[i]
        nid = node["id"]

        # 分支组：连续的 A 系列或 B 系列
        if nid.startswith("branch_a") or nid.startswith("branch_b"):
            group = [node]
            prefix = "branch_a" if nid.startswith("branch_a") else "branch_b"
            j = i + 1
            while j < len(flow_nodes):
                if flow_nodes[j]["id"].startswith(prefix):
                    group.append(flow_nodes[j])
                    j += 1
                else:
                    break
            phases.append({"nodes": group})
            i = j
        else:
            phases.append({"nodes": [node]})
            i += 1

    return phases


def _render_node(node, state, chapter, compact=False):
    """渲染单个节点按钮 — 使用渐进解锁"""
    node_id = node["id"]
    label = node["label"]
    desc = node.get("description", "")

    is_branch = node_id.startswith("branch_")
    is_ending = node_id.startswith("ending_")

    # 统一用 get_node_status 获取解锁状态
    status = BranchManager.get_node_status(state, node_id, chapter)

    # 显示文本
    if is_branch:
        branch_obj = _find_branch(chapter, node_id)
        display_label = branch_obj.title if branch_obj else label
        display_sub = branch_obj.subtitle if branch_obj else desc
        node_type = "branch"
    elif is_ending:
        ending_obj = _find_ending(chapter, node_id)
        display_label = ending_obj.title if ending_obj else label
        display_sub = desc
        node_type = "ending"
    else:
        display_label = label
        display_sub = desc
        node_type = "scene"

    icons = {"available": "▶", "completed": "✓", "locked": "🔒"}
    icon = icons.get(status, "🔒")

    # 按钮文本
    if compact:
        btn_text = f"{icon} {display_label}\n{display_sub}"
    elif node_type == "branch":
        btn_text = f"{icon} {display_label} — {display_sub}"
    else:
        btn_text = f"{icon} {display_label}"

    if status == "locked":
        st.button(
            btn_text, key=f"p3_{node_id}", disabled=True, use_container_width=True
        )
    else:
        if st.button(btn_text, key=f"p3_{node_id}", use_container_width=True):
            _enter_node(state, node_id, node_type, is_branch)
            st.rerun()


def _enter_node(state, node_id, node_type, is_branch):
    """点击节点后进入对应场景/分支"""
    if is_branch:
        new_state = state.model_copy(
            update={
                "current_branch": node_id,
                "current_scene": "",
                "current_beat_index": 0,
                "turn_count": 0,
                "dialogue_history": [],
                "current_page": "P2",
            }
        )
    elif node_type == "ending":
        new_state = GameStateManager.trigger_ending(state, node_id)
    else:
        new_state = state.model_copy(
            update={
                "current_scene": node_id,
                "current_branch": None,
                "current_beat_index": 0,
                "turn_count": 0,
                "dialogue_history": [],
                "current_page": "P2",
            }
        )
    st.session_state.game_state = new_state


def _find_branch(chapter, branch_id):
    for b in chapter.branches:
        if b.id == branch_id:
            return b
    return None


def _find_ending(chapter, ending_id):
    for e in chapter.endings:
        if e.id == ending_id:
            return e
    return None
