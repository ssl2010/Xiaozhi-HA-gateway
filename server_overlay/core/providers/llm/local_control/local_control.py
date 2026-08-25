from core.providers.llm.base import LLMProviderBase


class LLMProvider(LLMProviderBase):
    """Avoids loading or calling an LLM for out-of-domain commands."""

    def __init__(self, config):
        self.model_name = "local-ha-control"

    def response(self, session_id, dialogue, **kwargs):
        yield "暂时只支持控制主卧、客厅和书房的空调，以及四个房间的灯。"

    def response_with_functions(self, session_id, dialogue, functions=None):
        yield from self.response(session_id, dialogue)
