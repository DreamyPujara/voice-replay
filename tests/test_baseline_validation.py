import unittest

import tool


class BaselineValidationTest(unittest.TestCase):
    def test_rejects_baseline_evidence_without_to_state(self):
        report = tool.run_scenario({"turns": [{"event": "silence"}]})
        bad_baseline = {"passed": True, "evidence": [{"turn": 1, "event": "silence"}]}

        with self.assertRaisesRegex(ValueError, "non-empty string 'to' state"):
            tool.compare_baseline(report, bad_baseline)

    def test_accepts_previous_report_as_baseline(self):
        scenario = {"turns": [{"event": "silence"}]}
        report = tool.run_scenario(scenario)

        compared = tool.compare_baseline(tool.run_scenario(scenario), report)

        self.assertTrue(compared["baseline"]["matched"])
        self.assertEqual([], compared["baseline"]["changes"])


if __name__ == "__main__":
    unittest.main()
