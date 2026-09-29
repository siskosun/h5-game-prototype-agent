# Changelog

## 0.2.1 - 2026-09-29

- Add the game-exp `iteration_delivery` return contract after completed managed implementation passes.
- Distinguish verified shareable URLs, environment-bound local URLs, downloadable artifacts, and an explicit missing-playable state.
- Bind the handoff to player-visible changes, 1-3 human focus points, producer/build identity, and an optional real prior Candidate.
- Keep delivery evidence participant-reported; PROBE machine verdicts still cannot create human Review or lifecycle transitions.

## 0.2.0 - 2026-09-28

- Add completion level `PROBE` beside the existing `SLICE` workflow while keeping task modes independent.
- Add deterministic realtime/manual clocks and seeded pure-state RNG to DOM and Phaser templates.
- Add QA interface v1 with seed/scenario/clock/input-log controls and production-build isolation.
- Replace the non-runnable simulation skeleton with real TypeScript tests that import the production core.
- Add the graybox PROBE scaffold, Playwright player path, success/failure/retry/edge checks, degeneracy detection, screenshots, and WebM evidence.
- Add `probe_card.py`, `probe_log.py`, and `validate_probe_report.py`.
- Add probe-to-SLICE and game-exp handoff contracts without moving human lifecycle gates into this Skill.
- Add runtime-only skill packaging and Windows/Linux CI.
- Remove model/tool-specific operating language.

## 0.1

Initial H5 vertical-slice Skill with DOM and Phaser templates, deterministic bridge shape, release validation, and design/testing references.
