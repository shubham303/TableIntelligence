# Contributing

This project is built one algorithm at a time. Before adding anything, read
`docs/vision.md` and `docs/architecture.md` — they define the contracts every
contribution must honor.

## To add a capability
Follow `docs/adding-an-algorithm.md` exactly. In short: pick an unchecked roadmap
item, research it, write its precondition with the shared `validation/` helpers,
implement it against an existing library, return a structured `Result`, add a
known-answer test to the harness, document it, and check the box in the README.

## Non-negotiable invariants
- Structured, inspectable returns (never print-and-return-None).
- Centralized dtype/assumption checks — no local duplication.
- `store` is the single owner and writer of the table.
- Deterministic computation; transparent, rule-based method selection.
- Computation comes from trusted libraries, never improvised.

## Setup
```bash
pip install -e ".[dev]"
pytest
```
