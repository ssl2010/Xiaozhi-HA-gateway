import os

from ha_terminal.ha_client import HomeAssistantClient, UnsupportedCommand
from ha_terminal.intent_parser import Command
from plugins_func.register import Action, ActionResponse, ToolType, register_function


DESCRIPTION = {
    "type": "function",
    "function": {
        "name": "ha_control",
        "description": "执行已由本地规则验证的家庭设备控制命令",
        "parameters": {
            "type": "object",
            "properties": {"commands": {"type": "array", "items": {"type": "object"}}},
            "required": ["commands"],
        },
    },
}


def _success_text(command: Command) -> str:
    labels = {
        "turn_on": "已打开",
        "turn_off": "已关闭",
        "set_temperature": f"温度已设为{command.value}度",
        "set_hvac_mode": "模式已调整",
        "set_fan_mode": "风速已调整",
        "set_swing": "摆风已关闭" if command.value == "off" else "摆风已调整",
        "set_brightness": f"亮度已设为{command.value}%",
        "set_effect": f"已切换到{command.value}模式",
        "set_preset_mode": f"已切换到{command.value}模式",
        "set_percentage": f"风量已设为{command.value}%",
    }
    device = {
        "climate": "空调",
        "light": "灯",
        "floor_lamp": "落地灯",
        "air_purifier": "空气净化器",
    }.get(command.device, "设备")
    return f"{command.room}{device}{labels.get(command.action, '已调整')}"


@register_function("ha_control", DESCRIPTION, ToolType.SYSTEM_CTL)
async def ha_control(conn, commands=None):
    base_url = os.environ.get("HA_URL", "http://192.168.3.185:8123")
    token = os.environ.get("HA_TOKEN", "")
    if not token:
        return ActionResponse(Action.ERROR, response="Home Assistant 访问令牌尚未配置")

    client = HomeAssistantClient(base_url, token)
    responses = []
    try:
        for item in commands or []:
            command = Command(
                room=item.get("room", ""),
                device=item.get("device", ""),
                action=item.get("action", ""),
                value=item.get("value"),
            )
            await client.execute(command)
            responses.append(_success_text(command))
    except UnsupportedCommand as exc:
        return ActionResponse(Action.ERROR, response=str(exc))
    except Exception:
        return ActionResponse(Action.ERROR, response="Home Assistant 控制失败，请检查服务状态")
    return ActionResponse(Action.RESPONSE, response="，".join(responses))
