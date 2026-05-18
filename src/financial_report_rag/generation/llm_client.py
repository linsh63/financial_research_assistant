"""OpenAI-compatible Chat Completions 客户端。"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class OpenAIChatConfig:
    """保存 OpenAI-compatible API 调用参数。"""

    api_key: str = ""
    base_url: str = "https://api.vveai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 800
    timeout: float = 120.0
    max_retries: int = 5


class OpenAIChatClient:
    """使用 OpenAI Python SDK 调用 Chat Completions。"""

    def __init__(self, config: OpenAIChatConfig):
        """初始化 OpenAI-compatible 客户端。"""
        self.config = config
        if not config.api_key:
            raise RuntimeError("未找到 API Key，请设置 OPENAI_API_KEY 或通过命令行传入。")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("未安装 openai，请先运行 `pip install openai` 或 `pip install -r requirements.txt`。") from exc
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    @classmethod
    def from_env(
        cls,
        api_key_env: str = "OPENAI_API_KEY",
        base_url_env: str = "OPENAI_BASE_URL",
        model_env: str = "OPENAI_MODEL",
        temperature: float = 0.0,
        max_tokens: int = 800,
        timeout: float = 120.0,
    ) -> "OpenAIChatClient":
        """从环境变量创建客户端。"""
        return cls(
            OpenAIChatConfig(
                api_key=os.getenv(api_key_env, ""),
                base_url=os.getenv(base_url_env, "https://api.vveai.com/v1"),
                model=os.getenv(model_env, "gpt-4o-mini"),
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        )

    def generate(self, messages: list[dict[str, str]]) -> str:
        """调用模型生成答案。"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        message = response.choices[0].message
        return str(message.content or "").strip()
