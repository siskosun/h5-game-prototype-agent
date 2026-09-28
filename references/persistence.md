# Persistence and save evolution

Use persistence only when it supports the player promise.

## Save structure

When both concepts exist, separate:

- run state: current session/progress needed to resume the active run;
- meta state: long-lived unlocks, records, settings, achievements, or progression.

Version persistent payloads from the first implementation. Shape-validate every load.

For incompatible versions, either migrate with an explicit function or reject safely and fall back to a valid state. Never partially trust malformed data.

## Required behavior when applicable

Test:

- stable mid-loop checkpoint -> reload -> continue;
- settings/navigation does not silently destroy the run;
- completion clears/archives current run according to contract while preserving intended meta state;
- repeated settlement for the same run does not duplicate rewards;
- corrupt saves fall back safely;
- incompatible schema migrates or is safely rejected.

Use `templates/save_matrix.md` and `scripts/validate_save_matrix.py` for projects with run+meta flows. Adapt rows to the project's actual navigation rather than inventing screens that do not exist.
