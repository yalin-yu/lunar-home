"""游戏状态管理器 — 不可变状态转换"""

from .models import GameState, DialogueMessage, EndingType


class GameStateManager:
    """所有状态操作都是纯函数：接受 GameState，返回新的 GameState"""

    @staticmethod
    def init_state(chapter_id: str) -> GameState:
        """创建初始状态"""
        chapter = _get_chapter(chapter_id)
        return GameState(
            chapter_id=chapter_id,
            current_scene=chapter.flow.get("start", ""),
            current_page="P2",
        )

    @staticmethod
    def advance_beat(state: GameState) -> GameState:
        """推进脚本对话/旁白到下一个节拍，或到下一场景"""
        chapter = _get_chapter(state.chapter_id)
        scene = _get_scene(chapter, state.current_scene)
        new_index = state.current_beat_index + 1

        # 还有下一个 beat → 推进
        if new_index < len(scene.key_beats):
            return state.model_copy(update={"current_beat_index": new_index})

        # beat 已播完 → 标记当前场景完成
        nodes = list(state.completed_nodes)
        if state.current_scene and state.current_scene not in nodes:
            nodes.append(state.current_scene)
        return state.model_copy(update={
            "current_beat_index": new_index,
            "completed_nodes": nodes,
        })

    @staticmethod
    def select_option(state: GameState, option_id: str, leads_to: str) -> GameState:
        """玩家选择了决策选项 → 跳转到对应分支或场景"""
        chapter = _get_chapter(state.chapter_id)
        is_branch = any(b.id == leads_to for b in chapter.branches)

        # 标记当前场景完成
        nodes = list(state.completed_nodes)
        if state.current_scene and state.current_scene not in nodes:
            nodes.append(state.current_scene)

        if is_branch:
            return state.model_copy(update={
                "current_branch": leads_to,
                "current_scene": "",
                "current_beat_index": 0,
                "turn_count": 0,
                "dialogue_history": [],
                "current_page": "P2",
                "completed_nodes": nodes,
            })
        else:
            return state.model_copy(update={
                "current_scene": leads_to,
                "current_branch": None,
                "current_beat_index": 0,
                "turn_count": 0,
                "dialogue_history": [],
                "current_page": "P2",
                "completed_nodes": nodes,
            })

    @staticmethod
    def add_dialogue(state: GameState, speaker_id: str,
                     speaker_name: str, text: str,
                     is_ai: bool = False) -> GameState:
        """添加一条对话到历史"""
        msg = DialogueMessage(
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            text=text,
            is_ai_generated=is_ai,
        )
        new_history = list(state.dialogue_history) + [msg]
        new_turn = state.turn_count + (1 if is_ai else 0)
        return state.model_copy(update={
            "dialogue_history": new_history,
            "turn_count": new_turn,
        })

    @staticmethod
    def mark_branch_complete(state: GameState, branch_id: str) -> GameState:
        """标记分支已完成"""
        completed = list(state.completed_branches)
        if branch_id not in completed:
            completed.append(branch_id)
        nodes = list(state.completed_nodes)
        if branch_id not in nodes:
            nodes.append(branch_id)
        return state.model_copy(update={
            "completed_branches": completed,
            "completed_nodes": nodes,
            "current_branch": None,
            "turn_count": 0,
        })

    @staticmethod
    def trigger_ending(state: GameState, ending_id: str) -> GameState:
        """触发结局"""
        chapter = _get_chapter(state.chapter_id)
        ending = _get_ending(chapter, ending_id)

        completed = list(state.completed_endings)
        if ending_id not in completed:
            completed.append(ending_id)

        collected = list(state.collected_rules)
        if ending.rule_unlocked and ending.rule_unlocked not in collected:
            collected.append(ending.rule_unlocked)

        nodes = list(state.completed_nodes)
        if ending_id not in nodes:
            nodes.append(ending_id)

        return state.model_copy(update={
            "completed_endings": completed,
            "collected_rules": collected,
            "completed_nodes": nodes,
            "current_page": "P5",
            "current_branch": None,
        })

    @staticmethod
    def mark_node_complete(state: GameState, node_id: str) -> GameState:
        """标记任意节点（场景/分支/结局）为已完成"""
        nodes = list(state.completed_nodes)
        if node_id not in nodes:
            nodes.append(node_id)
        return state.model_copy(update={"completed_nodes": nodes})

    @staticmethod
    def mark_replay_downgrade(state: GameState, dp_id: str) -> GameState:
        """标记某决策点已降级为选项模式"""
        flags = dict(state.replay_flags)
        flags[dp_id] = True
        return state.model_copy(update={"replay_flags": flags})

    @staticmethod
    def is_downgraded(state: GameState, dp_id: str) -> bool:
        return state.replay_flags.get(dp_id, False)

    @staticmethod
    def navigate_to_page(state: GameState, page: str) -> GameState:
        return state.model_copy(update={"current_page": page})

    @staticmethod
    def enter_chapter(state: GameState, chapter_id: str) -> GameState:
        """从 P1 进入某章节 → 到 P3"""
        return GameStateManager.init_state(chapter_id).model_copy(
            update={"current_page": "P3"}
        )


# ==================== 内部辅助 ====================

def _get_chapter(chapter_id: str):
    from .config_loader import get_loader
    return get_loader().get_chapter(chapter_id)


def _get_scene(chapter, scene_id: str):
    for s in chapter.scenes:
        if s.id == scene_id:
            return s
    raise KeyError(f"场景 '{scene_id}' 未找到")


def _get_ending(chapter, ending_id: str):
    for e in chapter.endings:
        if e.id == ending_id:
            return e
    raise KeyError(f"结局 '{ending_id}' 未找到")
