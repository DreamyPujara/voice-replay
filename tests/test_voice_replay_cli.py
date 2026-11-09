import json
import os
import tempfile
import unittest

import tool


class VoiceReplayTests(unittest.TestCase):
    def test_scenario_specific_expectations_create_evidence(self):
        scenario = {
            "name": "silence then correction",
            "turns": [
                {"event": "silence", "expect": "silence"},
                {"event": "user_speech", "expect": "listening"},
                {"event": "user_correction", "expect": "correcting"},
            ],
        }
        report = tool.run_scenario(scenario)
        self.assertTrue(report["passed"])
        self.assertEqual(report["final_state"], "correcting")
        self.assertEqual(report["transition_count"], 3)
        self.assertEqual([e["to"] for e in report["evidence"]], ["silence", "listening", "correcting"])

    def test_failed_expectation_is_deterministic(self):
        report = tool.run_scenario({"turns": [{"event": "interrupt", "expect": "speaking"}]})
        self.assertFalse(report["passed"])
        self.assertEqual(report["failures"], ["turn 1 event interrupt expected speaking but reached interrupted"])

    def test_baseline_detects_state_path_change(self):
        current = tool.run_scenario({"turns": [{"event": "user_speech"}]})
        baseline = {"passed": True, "evidence": [{"to": "silence"}]}
        compared = tool.compare_baseline(current, baseline)
        self.assertFalse(compared["baseline"]["matched"])
        self.assertIn("state path changed", compared["baseline"]["changes"][0])

    def test_main_writes_report(self):
        with tempfile.TemporaryDirectory() as d:
            scenario_path = os.path.join(d, "scenario.json")
            report_path = os.path.join(d, "report.json")
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump({"turns": [{"event": "assistant_done", "expect": "idle"}]}, f)
            self.assertEqual(tool.main([scenario_path, "--write-report", report_path]), 0)
            with open(report_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertTrue(saved["passed"])
            self.assertEqual(saved["final_state"], "idle")


if __name__ == "__main__":
    unittest.main()
