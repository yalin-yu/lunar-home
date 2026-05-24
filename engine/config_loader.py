"""配置加载器 — YAML → Pydantic 模型"""

import yaml
from pathlib import Path
from .models import (
    CharacterConfig, CharacterPerformance, CharacterStructure,
    ChapterConfig, Scene, Branch, Ending, KeyBeat,
    DecisionPoint, DecisionOption,
    AIDialogueConfig, SuccessCondition, FailureCondition,
)


class ConfigLoader:
    """单例配置加载器，启动时一次性加载所有 YAML"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self._world_premise: str = ""
        self._characters: dict[str, CharacterConfig] = {}
        self._chapters: dict[str, ChapterConfig] = {}
        self._loaded = False

    # ---------- 加载入口 ----------

    def load_all(self):
        """加载全部配置"""
        self._load_world()
        self._load_characters()
        self._load_chapters()
        self._loaded = True
        print(f"[ConfigLoader] 已加载 {len(self._characters)} 个角色, "
              f"{len(self._chapters)} 个章节")

    # ---------- 世界观 ----------

    def _load_world(self):
        path = self.config_dir / "world.yaml"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            self._world_premise = data.get("premise", "")

    def get_world_premise(self) -> str:
        return self._world_premise

    # ---------- 角色 ----------

    def _load_characters(self):
        char_dir = self.config_dir / "characters"
        if not char_dir.exists():
            return
        for path in char_dir.glob("*.yaml"):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            perf = CharacterPerformance(**data.get("performance", {}))
            struct = CharacterStructure(**data.get("structure", {}))
            char = CharacterConfig(
                id=data["id"],
                name_cn=data.get("name_cn", ""),
                is_player=data.get("is_player", False),
                performance=perf,
                structure=struct,
                chapter_patches=data.get("chapter_patches", {}),
            )
            self._characters[char.id] = char

    def get_character(self, char_id: str) -> CharacterConfig:
        if char_id not in self._characters:
            raise KeyError(f"角色 '{char_id}' 未找到")
        return self._characters[char_id]

    def get_all_characters(self) -> dict[str, CharacterConfig]:
        return self._characters

    def get_player_character(self) -> CharacterConfig:
        for c in self._characters.values():
            if c.is_player:
                return c
        raise RuntimeError("未定义玩家角色")

    # ---------- 章节 ----------

    def _load_chapters(self):
        chap_dir = self.config_dir / "chapters"
        if not chap_dir.exists():
            return
        for path in chap_dir.glob("*.yaml"):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            chapter = self._parse_chapter(data)
            self._chapters[chapter.id] = chapter

    def _parse_chapter(self, data: dict) -> ChapterConfig:
        scenes = [self._parse_scene(s) for s in data.get("scenes", [])]
        branches = [self._parse_branch(b) for b in data.get("branches", [])]
        endings = [self._parse_ending(e) for e in data.get("endings", [])]
        return ChapterConfig(
            id=data["id"],
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            era_background=data.get("era_background", ""),
            core_conflict=data.get("core_conflict", ""),
            target_rule=data.get("target_rule"),
            scenes=scenes,
            branches=branches,
            endings=endings,
            flow=data.get("flow", {}),
        )

    def _parse_scene(self, data: dict) -> Scene:
        decision = None
        if "decision" in data and data["decision"]:
            d = data["decision"]
            opts = [DecisionOption(**o) for o in d.get("options", [])]
            decision = DecisionPoint(
                id=d.get("id", ""),
                type=d.get("type", "options"),
                prompt_context=d.get("prompt_context", ""),
                options=opts,
            )
        ai_dialogue = None
        if "ai_dialogue" in data and data["ai_dialogue"]:
            ai_dialogue = self._parse_ai_dialogue(data["ai_dialogue"])
        beats = [KeyBeat(**b) for b in data.get("key_beats", [])]
        return Scene(
            id=data["id"],
            type=data.get("type", "narration"),
            background=data.get("background", "default.png"),
            characters_present=data.get("characters_present", []),
            key_beats=beats,
            decision=decision,
            ai_dialogue=ai_dialogue,
            next=data.get("next"),
        )

    def _parse_branch(self, data: dict) -> Branch:
        ai = self._parse_ai_dialogue(data.get("ai_dialogue", {}))
        return Branch(
            id=data["id"],
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            phase=data.get("phase", "A"),
            characters=data.get("characters", []),
            background=data.get("background", "default.png"),
            branch_ending_narration=data.get("branch_ending_narration", ""),
            on_complete_unlocks=data.get("on_complete_unlocks", []),
            ai_dialogue=ai,
        )

    def _parse_ai_dialogue(self, data: dict) -> AIDialogueConfig:
        success_conds = [SuccessCondition(**c) for c in data.get("success_conditions", [])]
        failure_conds = [FailureCondition(**c) for c in data.get("failure_conditions", [])]
        return AIDialogueConfig(
            max_turns=data.get("max_turns", 10),
            responding_character=data.get("responding_character", ""),
            supporting_characters=data.get("supporting_characters", []),
            situation_prompt=data.get("situation_prompt", ""),
            success_conditions=success_conds,
            failure_conditions=failure_conds,
        )

    def _parse_ending(self, data: dict) -> Ending:
        opts = [DecisionOption(**o) for o in data.get("fallback_options", [])]
        return Ending(
            id=data["id"],
            type=data.get("type", "failure"),
            trigger_branch=data.get("trigger_branch", ""),
            title=data.get("title", ""),
            background=data.get("background", "default.png"),
            rule_unlocked=data.get("rule_unlocked"),
            epilogue_narration=data.get("epilogue_narration", ""),
            fallback_options=opts,
        )

    def get_chapter(self, chapter_id: str) -> ChapterConfig:
        if chapter_id not in self._chapters:
            raise KeyError(f"章节 '{chapter_id}' 未找到")
        return self._chapters[chapter_id]

    def get_all_chapters(self) -> dict[str, ChapterConfig]:
        return self._chapters

    # ---------- 便捷查询 ----------

    def get_scene(self, chapter_id: str, scene_id: str) -> Scene:
        chapter = self.get_chapter(chapter_id)
        for s in chapter.scenes:
            if s.id == scene_id:
                return s
        raise KeyError(f"场景 '{scene_id}' 未在章节 '{chapter_id}' 中找到")

    def get_branch(self, chapter_id: str, branch_id: str) -> Branch:
        chapter = self.get_chapter(chapter_id)
        for b in chapter.branches:
            if b.id == branch_id:
                return b
        raise KeyError(f"分支 '{branch_id}' 未在章节 '{chapter_id}' 中找到")

    def get_ending(self, chapter_id: str, ending_id: str) -> Ending:
        chapter = self.get_chapter(chapter_id)
        for e in chapter.endings:
            if e.id == ending_id:
                return e
        raise KeyError(f"结局 '{ending_id}' 未在章节 '{chapter_id}' 中找到")


# 全局单例
_loader: ConfigLoader | None = None


def init_loader(config_dir: str) -> ConfigLoader:
    global _loader
    _loader = ConfigLoader(config_dir)
    _loader.load_all()
    return _loader


def get_loader() -> ConfigLoader:
    if _loader is None:
        raise RuntimeError("ConfigLoader 未初始化，请先调用 init_loader()")
    return _loader
