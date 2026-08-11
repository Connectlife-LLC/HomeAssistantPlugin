import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "hisense_ac_plugin" / "temperature.py"
SPEC = importlib.util.spec_from_file_location("hisense_temperature", MODULE_PATH)
temperature_module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(temperature_module)
resolve_current_temperature = temperature_module.resolve_current_temperature


class DummyDevice:
    def __init__(self, status):
        self.status = status

    def get_status_value(self, key, default=None):
        return self.status.get(key, default)


class TemperatureResolutionTests(unittest.TestCase):
    def test_prefers_panel_temperature_when_available(self):
        device = DummyDevice({"t_temp_in": "24.5", "f_temp_in": "26.0"})
        self.assertEqual(resolve_current_temperature(device), (24.5, "t_temp_in"))

    def test_falls_back_to_indoor_temperature_when_panel_missing(self):
        device = DummyDevice({"f_temp_in": "25.0"})
        self.assertEqual(resolve_current_temperature(device), (25.0, "f_temp_in"))

    def test_supports_numeric_string_values(self):
        device = DummyDevice({"t_temp": "22"})
        self.assertEqual(resolve_current_temperature(device), (22.0, "t_temp"))


if __name__ == "__main__":
    unittest.main()
