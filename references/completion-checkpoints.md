# Player-path completion checks

Use for consequential gameplay changes and near-release slices. Do not require full-game progression for a mechanic probe.

1. Derive the smallest complete normal-player path from the accepted brief: launch -> action -> observable transition -> contracted terminal/recovery. Mark each checkpoint with a stable ID, dependencies, source files, required/optional, expected state and feedback.
2. Run actual engine/browser input; record input provenance, action timing, authoritative state, runtime screen/log, exact artifact identity, expected outcome and first failure. State injection and direct calls are setup/logic checks, never proof of normal-player reachability.
3. Write a JSON report with schema_version 1, artifact_sha256, checkpoints[] (id, requires[], source_files[], status, input_origin, normal_player_path, terminal, required, evidence[] with type/path/sha256). Use scripts/completion_checkpoints.py REPORT --root PROJECT --expected-artifact SHA --require-completion for integrity/dependency checks. This script does not play the game and cannot certify truthfulness or fun.
4. After a change, run --changed RELATIVE_PATH for each affected file. Retest invalidated checkpoints and dependent paths. Preserve the previously passing clean player path and the same failing seed/input trace. Use a disposable candidate copy, retain only when repair plus protected regression passes; revert candidate on regression, without modifying the user's accepted baseline.
5. A complete session is required only to the extent the brief promises one. Optional human feel remains UNVERIFIED without human evidence. Never change acceptance or fabricated evidence to make a gate pass.
