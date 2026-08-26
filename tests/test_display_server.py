import unittest

from ha_terminal.display_server import compact_room_states


class DisplayStateTest(unittest.TestCase):
    def test_missing_roles_stay_absent_and_unavailable_stays_visible(self):
        source = {
            "主卧": {
                "climate": {"state": "cool", "attributes": {"temperature": 25, "fan_mode": "auto"}},
                "temperature": {"state": "26.1", "attributes": {"unit_of_measurement": "°C"}},
            },
            "次卧": {"light": {"state": "unavailable", "attributes": {}}},
        }
        result = compact_room_states(source)
        self.assertNotIn("humidity", result["主卧"])
        self.assertNotIn("climate", result["次卧"])
        self.assertEqual(result["次卧"]["light"]["state"], "unavailable")
        self.assertEqual(result["主卧"]["climate"]["temperature"], 25)
        self.assertEqual(result["主卧"]["devices"][0]["type"], "climate")
        self.assertEqual(result["次卧"]["devices"][0]["name"], "吸顶灯")


if __name__ == "__main__":
    unittest.main()
