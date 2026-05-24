"""数据模型定义 — 使用 Pydantic 实现类型安全"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ==================== 枚举 ====================

class SceneType(str, Enum):
    NARRATION = "narration"
    SCRIPTED_DIALOGUE = "scripted_dialogue"
    AI_DIALOGUE = "ai_dialogue"
    DECISION_POINT = "decision_point"
    TRANSITION = "transition"
    ENDING = "ending"


class DecisionType(str, Enum):
    OPTIONS = "options"
    MIXED = "mixed"


class NodeStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    COMPLETED = "completed"


class EndingType(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class JudgeResult(str, Enum):
    CONTINUE = "continue"
    SUCCESS = "success"
    FAILURE = "failure"


# ==================== 角色 ====================

class CharacterPerformance(BaseModel):
    """表现层：决定 AI 怎么说话"""
    name: str
    name_cn: str
    title: str = ""
    personality: str = ""
    speech_style: str = ""
    core_motivation: str = ""
    core_fear: str = ""
    core_values: str = ""


class CharacterStructure(BaseModel):
    """结构层：决定角色在冲突中怎么选择"""
    exit_option: str = ""
    bargaining_chips: str = ""
    earth_ties: str = ""
    economic_center: str = ""
    system_control: str = ""
    info_position: str = ""
    generation: str = ""
    time_horizon: str = ""


class CharacterConfig(BaseModel):
    """完整角色设定"""
    id: str
    name_cn: str
    is_player: bool = False
    performance: CharacterPerformance
    structure: CharacterStructure
    chapter_patches: dict[str, str] = {}


# ==================== 场景与分支 ====================

class KeyBeat(BaseModel):
    """脚本对话的一个节拍"""
    speaker: str
    text: str


class DecisionOption(BaseModel):
    """决策选项"""
    id: str
    label: str
    leads_to: str
    consequence: str = ""


class SuccessCondition(BaseModel):
    """成功判定条件"""
    type: str = "semantic_match"
    description: str = ""
    keywords_any: list[str] = []


class FailureCondition(BaseModel):
    """失败判定条件"""
    type: str = "turn_limit"  # semantic_match | turn_limit
    description: str = ""
    keywords_any: list[str] = []
    max_turns: int = 10


class AIDialogueConfig(BaseModel):
    """AI 对话环节配置"""
    max_turns: int = 10
    responding_character: str = ""
    supporting_characters: list[str] = []
    situation_prompt: str = ""
    success_conditions: list[SuccessCondition] = []
    failure_conditions: list[FailureCondition] = []


class DecisionPoint(BaseModel):
    """决策点"""
    id: str
    type: DecisionType = DecisionType.OPTIONS
    prompt_context: str = ""
    options: list[DecisionOption] = []
    free_input_enabled: bool = True
    free_input_prompt: str = "请输入你的方案..."


class Scene(BaseModel):
    """场景"""
    id: str
    type: SceneType
    background: str = "default.png"
    characters_present: list[str] = []
    key_beats: list[KeyBeat] = []
    decision: Optional[DecisionPoint] = None
    ai_dialogue: Optional[AIDialogueConfig] = None
    next: Optional[str] = None


class Branch(BaseModel):
    """分支"""
    id: str
    title: str
    subtitle: str = ""
    phase: str = "A"
    characters: list[str] = []
    background: str = "default.png"
    branch_ending_narration: str = ""
    on_complete_unlocks: list[str] = []
    ai_dialogue: AIDialogueConfig


class Ending(BaseModel):
    """结局"""
    id: str
    type: EndingType
    trigger_branch: str = ""
    title: str = ""
    background: str = "default.png"
    rule_unlocked: Optional[str] = None
    epilogue_narration: str = ""
    fallback_options: list[DecisionOption] = []


class ChapterFlowTransition(BaseModel):
    """流程转换"""
    from_id: str = ""
    from_ids: list[str] = []
    to: str = ""
    to_ids: list[str] = []
    via: str = ""
    condition: str = ""


class ChapterConfig(BaseModel):
    """章节配置"""
    id: str
    title: str
    subtitle: str = ""
    era_background: str = ""
    core_conflict: str = ""
    target_rule: Optional[dict] = None
    scenes: list[Scene] = []
    branches: list[Branch] = []
    endings: list[Ending] = []
    flow: dict = {}


# ==================== 游戏状态 ====================

class DialogueMessage(BaseModel):
    """单条对话消息"""
    speaker_id: str = ""
    speaker_name: str = ""
    text: str = ""
    is_ai_generated: bool = False


class GameState(BaseModel):
    """完整游戏状态"""
    chapter_id: str = ""
    current_scene: str = ""
    current_branch: Optional[str] = None
    current_beat_index: int = 0
    dialogue_history: list[DialogueMessage] = []
    turn_count: int = 0
    completed_branches: list[str] = []
    completed_endings: list[str] = []
    completed_nodes: list[str] = []
    collected_rules: list[str] = []
    replay_flags: dict[str, bool] = {}
    route_map_visited: dict[str, bool] = {}
    current_page: str = "P0"
    config_loaded: bool = False
