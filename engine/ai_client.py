"""AI 客户端 — 调用外部 LLM API（OpenAI 兼容接口）"""

import json
import streamlit as st
from urllib.request import Request, urlopen
from urllib.error import URLError


class AIClient:
    """同步 HTTP 客户端，调用 OpenAI 兼容的 Chat Completions API"""

    def __init__(self):
        # 优先从 Streamlit secrets 读取，其次环境变量
        self.api_base = _get_config("AI_API_BASE", "https://api.openai.com/v1")
        self.api_key = _get_config("AI_API_KEY", "")
        self.model = _get_config("AI_MODEL", "gpt-4o")
        self.max_tokens = int(_get_config("AI_MAX_TOKENS", "512"))
        self.temperature = float(_get_config("AI_TEMPERATURE", "0.8"))

    def chat(self, system_prompt: str, messages: list[dict]) -> str:
        """
        发送对话请求，返回 AI 回复文本。

        messages 格式: [{"role": "user", "content": "..."}, ...]
        会自动在前面插入 system message。
        """
        if not self.api_key:
            return self._fallback_response(system_prompt, messages)

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        body = json.dumps({
            "model": self.model,
            "messages": full_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }).encode("utf-8")

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        req = Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")

        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except URLError as e:
            return f"[API 调用失败: {e}]"
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return f"[响应解析失败: {e}]"

    def judge(self, question: str) -> str:
        """轻量判定调用（用于 AI 二次判定）"""
        if not self.api_key:
            return "YES"  # 无 API 时默认通过

        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个判定器。只回复 YES 或 NO。"},
                {"role": "user", "content": question},
            ],
            "max_tokens": 5,
            "temperature": 0.0,
        }).encode("utf-8")

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        req = Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")

        try:
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return "YES"

    def _fallback_response(self, system_prompt: str, messages: list[dict]) -> str:
        """无 API key 时的离线回复"""
        last_msg = messages[-1]["content"] if messages else ""
        return (
            f"[离线模式] 我听到了你说的话。\n\n"
            f"你说了「{last_msg[:50]}{'...' if len(last_msg) > 50 else ''}」\n\n"
            f"配置 AI_API_KEY 后可以启用完整的 AI 对话。"
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


def _get_config(key: str, default: str) -> str:
    """从 st.secrets 或环境变量读取配置"""
    try:
        return st.secrets.get(key, default)
    except Exception:
        import os
        return os.environ.get(key, default)
