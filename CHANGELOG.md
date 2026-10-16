# Changelog

## 0.2.6 - 2026-10-16

- Add read-only per-Skill published-version and vetted-compatibility preflight, including optional dependent handoff gate.
- Check exact version, pinned SKILL.md Git blob and optional installed peers; unverified newer releases and unavailable network never auto-promote.
- Preserve standalone development without version gates and all game-exp trusted lifecycle and human Review authority.


## 0.2.5 - 2026-10-16

- Bind new H5 PROBE evidence to a working-source SHA-256, including dirty/untracked code, while retaining legacy Git SHA and build identity fields.
- Detect source modifications during browser QA and classify the resulting evidence as UNCERTAIN; support optional source-tree verification in the PROBE report validator without invalidating legacy reports.
- Prevent nested game-source folders named `artifacts`, `dist`, `.probe`, etc. from being incorrectly skipped by the source fingerprint.
- Add a production-core time-window boundary regression and document disposable known-bad plus semantically-equivalent oracle calibration for consequential mechanics.
- Keep the game-exp trusted evaluator, Review, PROMISING, selection and other human-owned gates unchanged.


## 0.2.4 - 2026-10-14

- Publish optional game-opportunity provenance: keep stable research identifiers and distinguish market interest from the frozen H5 PROBE question.
- Record only real, eligible player aggregates as research; machine QA/Playwright results do not become player preferences or human Review.
- Preserve existing PROBE fields, game-exp handoff schemas and lifecycle authority. Add version-gated stable Skill Release publishing after CI checks.


## 0.2.3 - 2026-09-29

- Move GitHub Pages deployment from the legacy Pages build queue to the managed game-exp GitHub Actions Pages workflow.
- Keep `gh-pages` as an immutable static version store, but require the default branch to contain `.github/workflows/game-exp-pages.yml`.
- Dispatch and bind to the exact workflow run for the requested version key, wait for successful deployment, then verify the served immutable marker/page.
- Safely migrate only the legacy `gh-pages` configuration previously created by this publisher; unrelated Pages configurations remain untouched.

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
