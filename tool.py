import argparse
import json
import sys

TRANSITIONS = {
    "silence": "silence",
    "user_speech": "listening",
    "process": "thinking",
    "assistant_start": "speaking",
    "assistant_done": "idle",
    "user_correction": "correcting",
    "interrupt": "interrupted",
}
MAX_TURNS = 1000


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def require_object(value, label):
    if not isinstance(value, dict):
        raise ValueError("%s must be a JSON object" % label)


def validate_scenario(scenario):
    require_object(scenario, "scenario")
    name = scenario.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError("scenario name must be a string when provided")
    state = scenario.get("initial_state", "idle")
    if not isinstance(state, str) or not state:
        raise ValueError("initial_state must be a non-empty string")
    steps = scenario.get("turns")
    if not isinstance(steps, list):
        raise ValueError("scenario must contain a 'turns' list")
    if not steps:
        raise ValueError("scenario turns must not be empty")
    if len(steps) > MAX_TURNS:
        raise ValueError("scenario has %s turns; maximum is %s" % (len(steps), MAX_TURNS))
    for i, step in enumerate(steps, 1):
        require_object(step, "turn %s" % i)
        event = step.get("event")
        if event not in TRANSITIONS:
            raise ValueError("unknown event at turn %s: %r" % (i, event))
        expected = step.get("expect")
        if expected is not None and not isinstance(expected, str):
            raise ValueError("expect at turn %s must be a string when provided" % i)


def validate_baseline(baseline):
    require_object(baseline, "baseline")
    if "passed" in baseline and not isinstance(baseline["passed"], bool):
        raise ValueError("baseline passed must be true or false when provided")
    evidence = baseline.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("baseline evidence must be a list when provided")
    for i, step in enumerate(evidence, 1):
        require_object(step, "baseline evidence %s" % i)
        state = step.get("to")
        if not isinstance(state, str) or not state:
            raise ValueError(
                "baseline evidence %s must contain a non-empty string 'to' state" % i
            )


def run_scenario(scenario):
    validate_scenario(scenario)
    name = scenario.get("name") or "unnamed"
    steps = scenario["turns"]
    state = scenario.get("initial_state", "idle")
    evidence = []
    failures = []
    for i, step in enumerate(steps, 1):
        event = step["event"]
        before = state
        state = TRANSITIONS[event]
        expected = step.get("expect")
        ok = expected is None or expected == state
        record = {
            "turn": i,
            "event": event,
            "from": before,
            "to": state,
            "expected": expected,
            "ok": ok,
        }
        evidence.append(record)
        if not ok:
            failures.append(
                "turn %s event %s expected %s but reached %s"
                % (i, event, expected, state)
            )

    return {
        "scenario": name,
        "passed": not failures,
        "final_state": state,
        "transition_count": len(evidence),
        "failures": failures,
        "evidence": evidence,
    }


def compare_baseline(report, baseline):
    validate_baseline(baseline)
    current_path = [e["to"] for e in report["evidence"]]
    old_path = [e.get("to") for e in baseline.get("evidence", [])]
    changes = []
    if baseline.get("passed") is not None and baseline.get("passed") != report["passed"]:
        changes.append(
            "pass status changed from %s to %s"
            % (baseline.get("passed"), report["passed"])
        )
    if old_path != current_path:
        changes.append("state path changed from %s to %s" % (old_path, current_path))
    report["baseline"] = {"matched": not changes, "changes": changes}
    return report


def markdown_report(report):
    status = "PASS" if report["passed"] else "FAIL"
    lines = [
        "# voice-replay report",
        "",
        "- Scenario: `%s`" % report["scenario"],
        "- Status: **%s**" % status,
        "- Final state: `%s`" % report["final_state"],
        "- Transition count: `%s`" % report["transition_count"],
    ]
    if "baseline" in report:
        matched = "yes" if report["baseline"]["matched"] else "no"
        lines.append("- Baseline matched: `%s`" % matched)
    lines.extend([
        "",
        "## Evidence",
        "",
        "| Turn | Event | From | To | Expected | OK |",
        "| ---: | --- | --- | --- | --- | --- |",
    ])
    for item in report["evidence"]:
        expected = "" if item["expected"] is None else item["expected"]
        ok = "yes" if item["ok"] else "no"
        lines.append(
            "| {turn} | `{event}` | `{from_}` | `{to}` | `{expected}` | {ok} |".format(
                turn=item["turn"], event=item["event"], from_=item["from"],
                to=item["to"], expected=expected, ok=ok
            )
        )
    if report["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend("- %s" % failure for failure in report["failures"])
    if "baseline" in report and report["baseline"]["changes"]:
        lines.extend(["", "## Baseline changes", ""])
        lines.extend("- %s" % change for change in report["baseline"]["changes"])
    lines.extend([
        "",
        "## Assumptions and limitations",
        "",
        "This report is generated from synthetic JSON events only. It does not use audio, personal data, model calls, timing, confidence scores, or speech recognition.",
    ])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run deterministic synthetic voice interaction regressions."
    )
    parser.add_argument("scenario", help="scenario JSON file")
    parser.add_argument("--baseline", help="previous report JSON to compare")
    parser.add_argument("--write-report", help="write report JSON to this path")
    parser.add_argument("--write-markdown", help="write Markdown report to this path")
    args = parser.parse_args(argv)

    try:
        report = run_scenario(load_json(args.scenario))
        if args.baseline:
            report = compare_baseline(report, load_json(args.baseline))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.write_report:
        with open(args.write_report, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    if args.write_markdown:
        with open(args.write_markdown, "w", encoding="utf-8") as f:
            f.write(markdown_report(report))

    if not report["passed"]:
        return 1
    if "baseline" in report and not report["baseline"]["matched"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
