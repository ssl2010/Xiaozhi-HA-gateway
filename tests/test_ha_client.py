import unittest

from ha_terminal.ha_client import UnsupportedCommand, build_service_call, load_entities
from ha_terminal.intent_parser import Command


class ServiceCallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities()

    def test_climate_temperature(self):
        self.assertEqual(
            build_service_call(Command("主卧", "climate", "set_temperature", 25), self.entities),
            ("climate", "set_temperature", {"entity_id": "climate.68e478810885_climate", "temperature": 25}),
        )

    def test_light_brightness(self):
        domain, service, data = build_service_call(Command("书房", "light", "set_brightness", 30), self.entities)
        self.assertEqual((domain, service), ("light", "turn_on"))
        self.assertEqual(data["brightness_pct"], 30)

    def test_climate_swing_modes(self):
        for spoken, expected in (("vertical", "vertical"), ("horizontal", "horizontal"), ("both", "both"), ("off", "off")):
            domain, service, data = build_service_call(
                Command("客厅", "climate", "set_swing", spoken), self.entities
            )
            self.assertEqual((domain, service), ("climate", "set_swing_mode"))
            self.assertEqual(data["swing_mode"], expected)

    def test_invalid_climate_swing_mode_is_blocked(self):
        with self.assertRaises(UnsupportedCommand):
            build_service_call(Command("客厅", "climate", "set_swing", "diagonal"), self.entities)

    def test_reserved_secondary_bedroom_climate_is_blocked(self):
        with self.assertRaises(UnsupportedCommand):
            build_service_call(Command("次卧", "climate", "turn_on"), self.entities)


if __name__ == "__main__":
    unittest.main()
