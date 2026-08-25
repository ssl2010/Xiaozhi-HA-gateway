import json
from typing import Dict, List

from core.providers.intent.base import IntentProviderBase
from ha_terminal.intent_parser import parse_commands


class IntentProvider(IntentProviderBase):
    async def detect_intent(self, conn, dialogue_history: List[Dict], text: str) -> str:
        commands = parse_commands(text)
        if not commands:
            return '{"function_call":{"name":"continue_chat"}}'
        payload = [
            {
                "room": item.room,
                "device": item.device,
                "action": item.action,
                "value": item.value,
            }
            for item in commands
        ]
        return json.dumps(
            {"function_call": {"name": "ha_control", "arguments": {"commands": payload}}},
            ensure_ascii=False,
        )
