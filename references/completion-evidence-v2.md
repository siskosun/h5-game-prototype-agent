# Completion Evidence v2

v2 is opt-in. Existing schema v1 reports and checkpoints[] remain supported without migration.

Use v1 for small PROBE tasks. Use v2 when a SLICE or NEAR_RELEASE brief promises materially different outcomes, branches or recovery paths. Do not invent paths to inflate coverage; declare paths from the accepted brief or explicit test plan.

v2 adds source_sha (40-character Git commit), paths[] (stable id, required flag and ordered checkpoint ids), transitions[] (directed checkpoint edges) and path_results[] (status, exact artifact/source identities, input origin, trace path/digest and ordered observed transitions).

A PASS path requires a digest-matching trace, exact source/artifact identity, actual engine/browser/player input, all path checkpoints PASS and current, and an observed transition sequence identical to the declared path. State injection and model calls can prepare a scenario but cannot certify a player path.

Path coverage = passed required declared paths / required declared paths.
Transition coverage = required declared transitions observed in PASS player-input path results / required declared transitions.
Missing required paths and edges remain visible. Optional paths do not block --require-path-coverage. Coverage applies only to the declared test model; it does not prove all possible states, fun, balance or market demand.

Commands:
    python scripts/completion_checkpoints.py report.json --root PROJECT
    python scripts/completion_checkpoints.py report.json --root PROJECT --require-path-coverage
    python scripts/completion_checkpoints.py report.json --root PROJECT --changed src/rules.gd --require-path-coverage

The coverage gate is explicit. The validator checks evidence integrity and declared coverage, not game execution or operator truthfulness. Trusted game-exp evaluation must independently replay traces against the frozen Candidate before classifying runtime facts as TRUSTED_OBSERVED.
