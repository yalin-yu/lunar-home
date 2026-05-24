"""分支管理器 — 追踪分支完成状态和推进条件"""

from .models import GameState, ChapterConfig, Branch, DecisionOption, DecisionPoint


class BranchManager:
    """管理分支解锁、完成状态和重玩降级"""

    def __init__(self):
        pass

    @staticmethod
    def get_branches_by_phase(
        chapter: ChapterConfig, phase: str
    ) -> list[Branch]:
        """获取某个阶段的所有分支"""
        return [b for b in chapter.branches if b.phase == phase]

    @staticmethod
    def get_branch_status(
        state: GameState, branch_id: str, chapter: ChapterConfig
    ) -> str:
        """返回分支状态 — A 分支需指挥厅完成，B 分支需联合会议完成 + ≥1 A"""
        if branch_id in state.completed_branches:
            return "completed"

        branch = None
        for b in chapter.branches:
            if b.id == branch_id:
                branch = b
                break
        if branch is None:
            return "locked"

        # A 阶段分支：需 scene_command_hall 完成（即做出了 A 阶段决策）
        if branch.phase == "A":
            if "scene_command_hall" in state.completed_nodes:
                return "available"
            return "locked"

        # B 阶段分支：需 scene_joint_meeting 完成 且 ≥1 A 完成
        if branch.phase == "B":
            a_branches = BranchManager.get_branches_by_phase(chapter, "A")
            a_done = any(b.id in state.completed_branches for b in a_branches)
            if "scene_joint_meeting" in state.completed_nodes and a_done:
                return "available"
            return "locked"

        return "locked"

    @staticmethod
    def get_scene_status(
        state: GameState, scene_id: str, chapter: ChapterConfig
    ) -> str:
        """返回场景状态 — 严格渐进解锁"""
        if scene_id in state.completed_nodes:
            return "completed"

        # 只有序幕始终可用
        if scene_id == "scene_opening":
            return "available"

        # 各场景的解锁前提
        prerequisites = {
            "scene_medical_bay": ["scene_opening"],
            "scene_command_hall": ["scene_medical_bay"],
            "transition_solar_storm": [],  # 特殊：需要 ≥1 A 分支完成
            "scene_joint_meeting": ["transition_solar_storm"],
            "scene_epilogue": ["ending_success"],
        }

        prereqs = prerequisites.get(scene_id, [])
        if prereqs:
            if all(p in state.completed_nodes for p in prereqs):
                return "available"
            return "locked"

        # 过渡场景：至少完成一条 A 分支
        if scene_id == "transition_solar_storm":
            a_branches = BranchManager.get_branches_by_phase(chapter, "A")
            if any(b.id in state.completed_branches for b in a_branches):
                return "available"
            return "locked"

        return "locked"

    @staticmethod
    def get_node_status(
        state: GameState, node_id: str, chapter: ChapterConfig
    ) -> str:
        """返回任意节点的解锁状态，用于 P3 路线图渲染"""
        # 已完成
        if node_id in state.completed_nodes:
            return "completed"

        # 分支节点：使用 get_branch_status
        if node_id.startswith("branch_"):
            return BranchManager.get_branch_status(state, node_id, chapter)

        # 结局节点
        if node_id.startswith("ending_"):
            if node_id in state.completed_endings:
                return "completed"
            # ending_success 需要 branch_b3 完成
            ending_prereqs = {
                "ending_success": ["branch_b3"],
                "ending_failure": ["branch_b3"],
            }
            prereqs = ending_prereqs.get(node_id, [])
            if prereqs and all(p in state.completed_nodes for p in prereqs):
                return "available"
            return "locked"

        # 场景节点
        return BranchManager.get_scene_status(state, node_id, chapter)

    @staticmethod
    def get_flow_nodes(chapter: ChapterConfig) -> list[dict]:
        """
        获取章节路线图的所有节点，用于 P3 渲染。
        返回格式: [{id, label, description, type: scene|branch|ending}]
        """
        flow = chapter.flow
        nodes = flow.get("chapter_map_nodes", [])
        return nodes

    @staticmethod
    def get_downgraded_options(
        decision_point: DecisionPoint
    ) -> list[DecisionOption]:
        """返回降级后的预设选项（关闭自由输入）"""
        return decision_point.options

    @staticmethod
    def get_fallback_options(ending) -> list[DecisionOption]:
        """返回失败结局的降级选项"""
        return ending.fallback_options

    @staticmethod
    def can_advance_past_transition(
        state: GameState, chapter: ChapterConfig
    ) -> bool:
        """检查是否满足进入过渡场景的条件"""
        a_branches = BranchManager.get_branches_by_phase(chapter, "A")
        return any(b.id in state.completed_branches for b in a_branches)
