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


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_scenario(scenario):
    name = scenario.get("name") or "unnamed"
    steps = scenario.get("turns")
    if not isinstance(steps, list):
        raise ValueError("scenario must contain a 'turns' list")

    state = scenario.get("initial_state", "idle")
    evidence = []
    failures = []
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            raise ValueError("each turn must be an object")
        event = step.get("event")
        if event not in TRANSITIONS:
            raise ValueError("unknown event at turn %s: %r" % (i, event))
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run deterministic synthetic voice interaction regressions."
    )
    parser.add_argument("scenario", help="scenario JSON file")
    parser.add_argument("--baseline", help="previous report JSON to compare")
    parser.add_argument("--write-report", help="write report JSON to this path")
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

    if not report["passed"]:
        return 1
    if "baseline" in report and not report["baseline"]["matched"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
