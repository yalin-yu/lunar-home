"""System Prompt 构造器 — 为 AI 对话构建角色扮演上下文"""

from .models import CharacterConfig, AIDialogueConfig, DialogueMessage
from .config_loader import get_loader


class PromptBuilder:
    """根据场景和角色配置构建 AI system prompt"""

    def __init__(self):
        self.loader = get_loader()

    def build(
        self,
        situation_prompt: str,
        responding_character_id: str,
        supporting_character_ids: list[str] | None = None,
        chapter_id: str = "chapter_1",
    ) -> str:
        """构建完整 system prompt"""
        parts = []

        # 1. 世界观前提
        world = self.loader.get_world_premise()
        parts.append(f"【世界观前提】\n{world}")

        # 2. 玩家角色
        player = self.loader.get_player_character()
        parts.append(self._format_player(player, chapter_id))

        # 3. 对话对象
        responder = self.loader.get_character(responding_character_id)
        parts.append(self._format_npc(responder, chapter_id))

        # 4. 辅助角色
        if supporting_character_ids:
            for sid in supporting_character_ids:
                if sid != responding_character_id:
                    try:
                        sc = self.loader.get_character(sid)
                        parts.append(self._format_supporting(sc, chapter_id))
                    except KeyError:
                        pass

        # 5. 当前情境
        parts.append(f"【当前情境】\n{situation_prompt}")

        # 6. 对话规则
        parts.append(self._dialogue_rules(responder.name_cn))

        return "\n\n".join(parts)

    def _format_player(self, char: CharacterConfig, chapter_id: str) -> str:
        perf = char.performance
        struct = char.structure
        patch = char.chapter_patches.get(chapter_id, "")

        text = f"【玩家角色 - {char.name_cn}】\n"
        text += f"身份：{perf.title}。{perf.personality}\n"
        text += f"说话风格：{perf.speech_style}\n"
        text += f"核心动机：{perf.core_motivation}\n"
        text += f"核心恐惧：{perf.core_fear}\n"
        text += f"核心价值观：{perf.core_values}\n"
        text += f"退出选项：{struct.exit_option}\n"
        text += f"地球牵挂：{struct.earth_ties}\n"
        text += f"经济重心：{struct.economic_center}\n"
        text += f"控制/依赖度：{struct.system_control}\n"
        if patch:
            text += f"\n本章状态：{patch}"
        return text

    def _format_npc(self, char: CharacterConfig, chapter_id: str) -> str:
        perf = char.performance
        struct = char.structure
        patch = char.chapter_patches.get(chapter_id, "")

        text = f"【对话对象 - {char.name_cn}（{perf.title}）】\n"
        text += f"性格：{perf.personality}\n"
        text += f"说话风格：{perf.speech_style}\n"
        text += f"核心动机：{perf.core_motivation}\n"
        text += f"核心恐惧：{perf.core_fear}\n"
        text += f"核心价值观：{perf.core_values}\n"
        text += f"退出选项：{struct.exit_option}\n"
        text += f"议价筹码：{struct.bargaining_chips}\n"
        text += f"地球牵挂：{struct.earth_ties}\n"
        text += f"经济重心：{struct.economic_center}\n"
        text += f"系统控制：{struct.system_control}\n"
        text += f"信息位置：{struct.info_position}\n"
        text += f"代际位置：{struct.generation}\n"
        text += f"时间视野：{struct.time_horizon}\n"
        if patch:
            text += f"\n本章状态：{patch}"
        return text

    def _format_supporting(self, char: CharacterConfig, chapter_id: str) -> str:
        perf = char.performance
        patch = char.chapter_patches.get(chapter_id, "")
        text = f"【在场角色 - {char.name_cn}（{perf.title}）】\n"
        text += f"性格：{perf.personality}\n"
        text += f"说话风格：{perf.speech_style}\n"
        if patch:
            text += f"本章状态：{patch}"
        return text

    def _dialogue_rules(self, npc_name: str) -> str:
        return f"""【对话规则】
1. 你是{npc_name}，以第一人称回应玩家。
2. 回应内容应严格遵循你的性格、动机和本章处境。
3. 每次只回复一段对话，不要替玩家说话。
4. 不要重复已经说过的话，对话应自然推进。
5. 在密闭月球基地环境中，人与人之间既有冲突也有不得不合作的现实——请保持这种张力。"""
