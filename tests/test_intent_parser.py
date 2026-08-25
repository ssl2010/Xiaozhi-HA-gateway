import unittest

from ha_terminal.intent_parser import Command, parse_commands


class IntentParserTest(unittest.TestCase):
    def test_climate_switches(self):
        self.assertEqual(parse_commands("打开主卧空调"), [Command("主卧", "climate", "turn_on")])
        self.assertEqual(parse_commands("把客厅空调关闭一下"), [Command("客厅", "climate", "turn_off")])

    def test_climate_settings(self):
        self.assertEqual(parse_commands("书房空调温度调到二十六度"), [Command("书房", "climate", "set_temperature", 26)])
        self.assertEqual(parse_commands("书房空调温度调到26度"), [Command("书房", "climate", "set_temperature", 26)])
        self.assertEqual(parse_commands("主卧空调调成高速"), [Command("主卧", "climate", "set_fan_mode", "high")])
        self.assertEqual(parse_commands("客厅空调打开摆风"), [Command("客厅", "climate", "set_swing", True)])

    def test_lights(self):
        self.assertEqual(parse_commands("打开书房灯"), [Command("书房", "light", "turn_on")])
        self.assertEqual(parse_commands("次卧灯亮度调到35%"), [Command("次卧", "light", "set_brightness", 35)])

    def test_multiple_rooms(self):
        self.assertEqual(
            parse_commands("关闭主卧空调，打开书房灯"),
            [Command("主卧", "climate", "turn_off"), Command("书房", "light", "turn_on")],
        )

    def test_ambiguous_is_rejected(self):
        self.assertEqual(parse_commands("把空调打开"), [])
        self.assertEqual(parse_commands("有点热"), [])
        self.assertEqual(parse_commands("打开次卧空调"), [Command("次卧", "climate", "turn_on")])


if __name__ == "__main__":
    unittest.main()
