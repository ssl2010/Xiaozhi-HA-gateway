"""Parse the deliberately small Chinese HA command grammar.

The terminal controls real devices, so supported commands are explicit and
deterministic. Unknown or ambiguous speech is rejected instead of being sent
to an LLM to guess an entity or service call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re


ROOM_ALIASES = {
    "主卧": "主卧",
    "主卧室": "主卧",
    "次卧": "次卧",
    "次卧室": "次卧",
    "客厅": "客厅",
    "书房": "书房",
}

FAN_MODES = {
    "自动": "auto",
    "低速": "low",
    "低风": "low",
    "一档": "low",
    "中速": "medium",
    "中风": "medium",
    "二档": "medium",
    "高速": "high",
    "强风": "high",
    "三档": "high",
}

CN_DIGITS = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def _temperature_value(value: str) -> int | None:
    if value.isdigit():
        number = int(value)
    elif value == "十":
        number = 10
    elif "十" in value:
        tens, ones = value.split("十", 1)
        number = (CN_DIGITS.get(tens, 1) * 10) + (CN_DIGITS.get(ones, 0) if ones else 0)
    else:
        number = CN_DIGITS.get(value, -1)
    return number if 16 <= number <= 30 else None


@dataclass(frozen=True)
class Command:
    room: str
    device: str
    action: str
    value: object | None = None
    source_text: str = field(default="", compare=False)


def _normalize(text: str) -> str:
    replacements = {
        "打开一下": "打开",
        "关闭一下": "关闭",
        "开一下": "打开",
        "关一下": "关闭",
        "摄氏度": "度",
        "灯光": "灯",
        "电灯": "灯",
        "调成": "调到",
        "设置为": "调到",
        "设为": "调到",
    }
    text = re.sub(r"[，。！？、,.!?；;]+", "|", text.strip())
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"(?:然后|并且|接着|同时)", "|", text)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _room_at(text: str, start: int) -> tuple[str | None, int]:
    matches = [(alias, room) for alias, room in ROOM_ALIASES.items() if text.startswith(alias, start)]
    if not matches:
        return None, start
    alias, room = max(matches, key=lambda item: len(item[0]))
    return room, start + len(alias)


def _parse_clause(room: str, clause: str, original: str) -> list[Command]:
    if "空调" in clause:
        commands: list[Command] = []
        swing_action = None
        if any(word in clause for word in ("打开摆风", "开启摆风", "摆风打开", "扫风打开")):
            swing_action = Command(room, "climate", "set_swing", True, original)
        elif any(word in clause for word in ("关闭摆风", "摆风关闭", "停止摆风", "扫风关闭")):
            swing_action = Command(room, "climate", "set_swing", False, original)

        switch_text = clause
        for phrase in ("打开摆风", "开启摆风", "摆风打开", "关闭摆风", "摆风关闭", "停止摆风",
                       "扫风打开", "扫风关闭"):
            switch_text = switch_text.replace(phrase, "")
        turn_on = any(word in switch_text for word in ("打开", "开启", "开空调"))
        turn_off = any(word in switch_text for word in ("关闭", "关空调"))
        if turn_on and turn_off:
            return []
        if turn_on:
            commands.append(Command(room, "climate", "turn_on", source_text=original))
        elif turn_off:
            commands.append(Command(room, "climate", "turn_off", source_text=original))

        temp = re.search(r"(?:温度)?(?:调到|调至)?(1[6-9]|2[0-9]|30|[一二两三四五六七八九]?十[一二三四五六七八九]?)度?", clause)
        if temp:
            value = _temperature_value(temp.group(1))
            if value is not None:
                commands.append(Command(room, "climate", "set_temperature", value, original))

        for spoken, mode in FAN_MODES.items():
            if spoken in clause:
                commands.append(Command(room, "climate", "set_fan_mode", mode, original))
                break
        if swing_action is not None:
            commands.append(swing_action)
        # Turning a device off while also changing its settings is ambiguous.
        if turn_off and len(commands) > 1:
            return []
        return commands

    if "灯" in clause:
        commands = []
        turn_on = any(word in clause for word in ("打开", "开启", "开灯"))
        turn_off = any(word in clause for word in ("关闭", "关灯"))
        if turn_on and turn_off:
            return []
        if turn_on:
            commands.append(Command(room, "light", "turn_on", source_text=original))
        elif turn_off:
            commands.append(Command(room, "light", "turn_off", source_text=original))
        brightness = re.search(r"(?:亮度)?(?:调到|调至)?(100|[1-9]?\d)%?", clause)
        if brightness and any(word in clause for word in ("亮度", "调亮", "调暗", "%")):
            commands.append(Command(room, "light", "set_brightness", int(brightness.group(1)), original))
        effect = re.search(r"(?:切换到|切换成|切换|调到|换成)(.+?)(?:模式)?$", clause)
        if effect and any(word in clause for word in ("模式", "切换", "换成")):
            value = effect.group(1).removesuffix("灯").strip()
            if value:
                commands.append(Command(room, "light", "set_effect", value, original))
        if turn_off and len(commands) > 1:
            return []
        return commands

    return []


def parse_commands(text: str) -> list[Command]:
    """Return supported commands, or an empty list for unsafe/unknown input."""
    commands: list[Command] = []
    previous_room: str | None = None
    previous_device: str | None = None
    for clause in filter(None, _normalize(text).split("|")):
        matches = [
            (clause.find(alias), len(alias), room)
            for alias, room in ROOM_ALIASES.items()
            if alias in clause
        ]
        if matches:
            _, _, room = min(matches, key=lambda item: (item[0], -item[1]))
        elif previous_room is not None:
            room = previous_room
            clause = room + clause
        else:
            continue

        if "空调" in clause:
            device = "空调"
        elif "灯" in clause:
            device = "灯"
        elif previous_device is not None:
            device = previous_device
            clause = room + device + clause.removeprefix(room)
        else:
            continue

        parsed = _parse_clause(room, clause, text)
        if not parsed:
            previous_room = None
            previous_device = None
            continue
        commands.extend(parsed)
        previous_room = room
        previous_device = device
    return commands
