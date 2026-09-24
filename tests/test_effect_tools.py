import tempfile
from pathlib import Path
import unittest
from companion.effect_tools import read_source, parameters, effects


class EffectToolTests(unittest.TestCase):
    def test_sources_are_bounded_and_ambiguous_names_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Bloom.fx").write_text("x" * 25000)
            state = {"base_path": directory, "search_paths": ["."]}
            result = read_source(state, "Bloom.fx")
            self.assertEqual(len(result["source"]), 24000)
            self.assertEqual(result["next_offset"], 24000)
            self.assertEqual(len(read_source(state, "Bloom.fx", 24000)["source"]), 1000)
            with self.assertRaises(ValueError):
                read_source(state, "../Bloom.fx")
            with self.assertRaises(ValueError):
                read_source(state, "credentials.json")
            (root / "other").mkdir()
            (root / "other/Bloom.fx").write_text("second")
            state["search_paths"].append("other")
            with self.assertRaises(ValueError):
                read_source(state, "Bloom.fx")

    def test_parameter_paging_preserves_ids_and_values(self):
        state = {"parameters": [{"id": i, "effect": "Bloom.fx", "name": "Value" + str(i), "value": [i]} for i in range(130)]}
        first = parameters(state)
        second = parameters(state, offset=first["next_offset"])
        self.assertEqual(first["items"][0]["id"], 0)
        self.assertEqual(second["items"][-1]["value"], [129])
        self.assertIsNone(second["next_offset"])
        self.assertEqual(effects(state)["items"][0]["file"], "Bloom.fx")
