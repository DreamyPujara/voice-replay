import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
TOOL = os.path.join(ROOT, "tool.py")


class AdversarialInputTests(unittest.TestCase):
    def run_with_json(self, payload, *extra):
        with tempfile.TemporaryDirectory() as td:
            scenario = os.path.join(td, "scenario.json")
            with open(scenario, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            cmd = [sys.executable, TOOL, scenario, *extra]
            return subprocess.run(cmd, text=True, capture_output=True)

    def test_empty_turns_are_rejected_with_error_json(self):
        result = self.run_with_json({"name": "empty", "turns": []})
        self.assertEqual(result.returncode, 2)
        err = json.loads(result.stderr)
        self.assertIn("turns must not be empty", err["error"])
        self.assertEqual(result.stdout, "")

    def test_non_object_scenario_is_rejected(self):
        result = self.run_with_json([])
        self.assertEqual(result.returncode, 2)
        self.assertIn("scenario must be a JSON object", json.loads(result.stderr)["error"])

    def test_boundary_turn_count_is_rejected_before_running(self):
        payload = {"turns": [{"event": "silence"}] * 1001}
        result = self.run_with_json(payload)
        self.assertEqual(result.returncode, 2)
        self.assertIn("maximum is 1000", json.loads(result.stderr)["error"])

    def test_malformed_baseline_gets_useful_error(self):
        with tempfile.TemporaryDirectory() as td:
            scenario = os.path.join(td, "scenario.json")
            baseline = os.path.join(td, "baseline.json")
            with open(scenario, "w", encoding="utf-8") as f:
                json.dump({"turns": [{"event": "silence"}]}, f)
            with open(baseline, "w", encoding="utf-8") as f:
                json.dump({"evidence": {}}, f)
            result = subprocess.run(
                [sys.executable, TOOL, scenario, "--baseline", baseline],
                text=True,
                capture_output=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("baseline evidence must be a list", json.loads(result.stderr)["error"])


if __name__ == "__main__":
    unittest.main()
