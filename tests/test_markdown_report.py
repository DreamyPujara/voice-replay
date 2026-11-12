import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
TOOL = os.path.join(ROOT, "tool.py")
EXAMPLE = os.path.join(ROOT, "examples", "correction_interrupt.json")


class MarkdownReportTests(unittest.TestCase):
    def test_cli_writes_deterministic_markdown_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            md_path = os.path.join(tmp, "report.md")
            result = subprocess.run(
                [sys.executable, TOOL, EXAMPLE, "--write-markdown", md_path],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["passed"])
            with open(md_path, "r", encoding="utf-8") as f:
                first = f.read()
            with open(md_path, "r", encoding="utf-8") as f:
                second = f.read()
            self.assertEqual(first, second)
            self.assertIn("# voice-replay report", first)
            self.assertIn("- Status: **PASS**", first)
            self.assertIn("| 5 | `interrupt` | `speaking` | `interrupted` | `interrupted` | yes |", first)
            self.assertIn("Assumptions and limitations", first)
            self.assertIn("does not use audio", first)


if __name__ == "__main__":
    unittest.main()
