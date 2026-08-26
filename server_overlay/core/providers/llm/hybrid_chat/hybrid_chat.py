"""Cloud chat fallback for utterances not claimed by local HA rules."""

import os

from core.providers.llm.openai.openai import LLMProvider as OpenAIProvider


class LLMProvider(OpenAIProvider):
    def __init__(self, config):
        api_key = os.environ.get("XIAOZHI_LLM_API_KEY", "").strip()
        self.enabled = bool(api_key)
        if not self.enabled:
            self.model_name = "chat-not-configured"
            return
        merged = dict(config)
        merged["api_key"] = api_key
        merged["base_url"] = os.environ.get(
            "XIAOZHI_LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/"
        )
        merged["model_name"] = os.environ.get("XIAOZHI_LLM_MODEL", "glm-4-flash")
        super().__init__(merged)

    def response(self, session_id, dialogue, **kwargs):
        if not self.enabled:
            yield "AI 对话密钥尚未配置，家庭设备控制仍可正常使用。"
            return
        yield from super().response(session_id, dialogue, **kwargs)

    def response_with_functions(self, session_id, dialogue, functions=None, **kwargs):
        if not self.enabled:
            yield "AI 对话密钥尚未配置，家庭设备控制仍可正常使用。", None
            return
        yield from super().response_with_functions(session_id, dialogue, functions, **kwargs)
