# Changelog

## 0.2.3 - 2026-09-29

- Stop explicitly requesting a second GitHub Pages build after updating `gh-pages`; the branch update already triggers deployment.
- Remove duplicate same-commit Pages builds observed in the live canary while preserving immutable-path and served-marker verification.

## 0.2.2 - 2026-09-29

- Add a public-repository GitHub Pages publisher for immutable versioned H5 playables under `play/<result_source_sha>/`.
- Preserve older playable versions, reject version-key byte drift, and verify the served deployment marker before handoff.
- Make bundled Vite templates subpath-safe with `base: "./"` so versioned project-site URLs load their assets correctly.
- Let game-exp request this route explicitly while keeping browser/player verification and all human lifecycle gates unchanged.

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
