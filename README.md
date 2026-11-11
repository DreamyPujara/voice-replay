# voice-replay

`voice-replay` is a tiny offline regression runner for one user: a voice UX builder who needs repeatable evidence that synthetic interaction scenarios still follow expected states.

It does **not** call models, record audio, play audio, or use personal data. Scenarios are plain JSON fixtures.

## Run the demo

```bash
python tool.py examples/correction_interrupt.json
```

Write a baseline report:

```bash
python tool.py examples/correction_interrupt.json --write-report baseline.json
python tool.py examples/correction_interrupt.json --baseline baseline.json
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

## Tradeoffs and non-goals

This first version is intentionally small: transitions are fixed and symbolic. It is not a speech recognizer, media tool, load tester, model evaluator, or enterprise workflow service. Future versions could add richer state-machine rules after the core report format proves useful.

## AI assistance

This code and documentation were generated with AI assistance. Limitations: review transition semantics before relying on them for product decisions, and keep scenarios synthetic.
