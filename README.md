# voice-replay

`voice-replay` is a tiny offline regression runner for one user: a voice UX builder who needs repeatable evidence that synthetic interaction scenarios still follow expected states.

It does **not** call models, record audio, play audio, or use personal data. Scenarios are plain JSON fixtures.

## Run the demo

```bash
python tool.py examples/correction_interrupt.json
```

Write deterministic JSON and Markdown reports:

```bash
python tool.py examples/correction_interrupt.json --write-report report.json --write-markdown report.md
python tool.py examples/correction_interrupt.json --baseline report.json --write-markdown compared.md
```

Exit codes: `0` pass, `1` expectation or baseline mismatch, `2` invalid input.

## Scenario format

A scenario is a JSON object with a non-empty `turns` list. Each turn has an `event` and optional scenario-specific `expect` state. Supported events are `silence`, `user_speech`, `process`, `assistant_start`, `assistant_done`, `user_correction`, and `interrupt`. To keep mistakes obvious, `initial_state` must be a non-empty string when provided, `expect` must be a string when provided, and scenarios are capped at 1000 turns.

## Metrics reported

- pass/fail status
- final state
- transition count
- per-turn deterministic evidence
- baseline state-path changes when `--baseline` is used

## Assumptions, tradeoffs and non-goals

Reports are deterministic because transitions are fixed symbolic mappings from synthetic events to states. Markdown is intended for quick human review; JSON remains the stable format for automation. This is not a speech recognizer, media tool, load tester, model evaluator, timing simulator, or enterprise workflow service.

## AI assistance

This code and documentation were generated with AI assistance. Limitations: review transition semantics before relying on them for product decisions, and keep scenarios synthetic.
