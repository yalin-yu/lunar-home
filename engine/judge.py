"""判定器 — 关键词匹配 + AI 二次判定"""

from .models import (
    DialogueMessage, SuccessCondition, FailureCondition,
    JudgeResult, AIDialogueConfig,
)


class Judge:
    """评估 AI 对话是否触发成功/失败条件"""

    def __init__(self, ai_api_caller=None):
        """
        ai_api_caller: 可选的 AI API 调用函数，用于二次语义判定。
        签名为 async def(question: str) -> str
        """
        self._ai_caller = ai_api_caller

    def evaluate(
        self,
        player_messages: list[str],
        config: AIDialogueConfig,
        turn_count: int,
    ) -> JudgeResult:
        """
        评估当前对话状态。
        返回 CONTINUE / SUCCESS / FAILURE
        """
        # 1. 合并玩家所有消息为一个文本
        combined = " ".join(player_messages)

        # 2. 检查成功条件
        if config.success_conditions:
            for cond in config.success_conditions:
                if self._match_keywords(combined, cond.keywords_any):
                    return JudgeResult.SUCCESS

        # 3. 检查失败条件 —— 轮数耗尽
        for cond in config.failure_conditions:
            if cond.type == "turn_limit":
                if turn_count >= cond.max_turns:
                    return JudgeResult.FAILURE
            elif cond.type == "semantic_match":
                if self._match_keywords(combined, cond.keywords_any):
                    return JudgeResult.FAILURE

        # 4. 继续对话
        return JudgeResult.CONTINUE

    async def evaluate_with_ai(
        self,
        player_messages: list[str],
        config: AIDialogueConfig,
        turn_count: int,
    ) -> JudgeResult:
        """
        先做关键词匹配，命中后调用 AI 做语义二次判定。
        """
        combined = " ".join(player_messages)

        # 第一步：关键词匹配
        keyword_hit = False
        for cond in config.success_conditions:
            if self._match_keywords(combined, cond.keywords_any):
                keyword_hit = True
                break

        if not keyword_hit:
            # 没命中关键词 → 检查失败条件
            return self.evaluate(player_messages, config, turn_count)

        # 第二步：AI 语义判定
        if self._ai_caller is None:
            # 无 AI caller → 关键词命中即视为成功
            return JudgeResult.SUCCESS

        prompt = (
            "请判断以下玩家发言是否体现了一个制度性方案的意图。"
            "玩家需要提出一个具体的制度框架，包含至少以下两个要素中的两个：\n"
            "1. 供应链中立：维持生命的资源供应不应受政治冲突影响\n"
            "2. 生存权优先：月球基地居民的生存权优先于任何地球政治冲突\n"
            "3. 制度化保障：需要可验证的、跨基地的制度机制\n\n"
            f"玩家发言：\n{combined}\n\n"
            "请仅回复 YES 或 NO。"
        )
        try:
            result = await self._ai_caller(prompt)
            if "YES" in result.upper():
                return JudgeResult.SUCCESS
        except Exception:
            # AI 判定失败 → 关键词命中即可
            return JudgeResult.SUCCESS

        # AI 判定为 NO → 检查失败条件
        return self.evaluate(player_messages, config, turn_count)

    @staticmethod
    def _match_keywords(text: str, keywords: list[str]) -> bool:
        """检查文本是否包含任意关键词"""
        if not keywords:
            return False
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
