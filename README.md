# h5-game-prototype-agent 0.2.0

A model-agnostic Skill for building and verifying 2D H5/web game prototypes.

## Two completion levels

- **PROBE**: fast graybox mechanic screening. One hypothesis, one repeatable loop, deterministic machine checks, browser player path, screenshots/video, then human batch playtest.
- **SLICE**: a small complete H5 vertical slice with the existing gameplay-contract, browser QA, delivery, and release-evidence workflow.

Task mode remains independent: NEW_BUILD, FEATURE_CHANGE, BUGFIX, POLISH_QA, RELEASE.

## PROBE evidence

A probe freezes `probe_card.md`, uses manual/realtime clock modes, seeded RNG, and QA interface v1. `npm run probe:check` runs:

- browser health;
- manual-clock determinism;
- a real-input complete player path;
- success / failure / retry / edge;
- spam / idle / repeated-action degeneracy probes;
- screenshots and a short WebM recording.

Agent verdicts are only `READY_FOR_PLAYTEST`, `MACHINE_REJECT`, or `UNCERTAIN`. Human PASS/REJECT is never fabricated.

## Templates

- `templates/dom`: Vite + TypeScript DOM starter.
- `templates/phaser`: Vite + TypeScript + Phaser starter.
- `templates/probe`: graybox mechanic-probe starter with Playwright QA.

All three support `npm ci`, `npm test`, and `npm run build`. The normal production build excludes `__GAME_API__`. QA builds use `npm run build:qa`.

## Relationship to GPS and game-exp

Godot Prototype Studio (GPS) remains the Godot implementation skill. When a stack decision resolves to H5, GPS should hand off to this Skill rather than growing its own H5 workflow.

After a human-passed probe:

- continue here as SLICE; or
- bind it to game-exp for controlled Candidate/Review/selection lifecycle.

game-exp remains authoritative for experiment identity, protected Ledger/Manifest, Candidate, Review, PROMISING/SELECTED/REJECTED, Integration, and Archive. This Skill only implements and supplies evidence.

## Development vs runtime package

The repository contains tests, CI, and development records. `dev/build_skill_zip.py` builds the runtime-only `dist/skill.zip` from a whitelist:

`SKILL.md, VERSION, agents/, assets/, references/, scripts/, templates/`

It excludes development files, node_modules, build outputs, probe evidence, logs, and caches.

## Install

Import `dist/skill.zip` through the host's Skill installation flow, or install the extracted runtime directory into the host's supported skill directory.

Updating this GitHub repository is not the same as updating an already installed Skill.

## Development checks

```bash
python -m unittest discover -s tests -v
python dev/build_skill_zip.py
```

Template integration is also exercised in CI on Windows and Linux.

The `probe-browser` job runs all three scenarios, then stages evidence with:

```bash
python dev/check_probe_e2e.py
python dev/stage_probe_evidence.py
```

Download `probe-evidence-<sha>` from the Actions run. It contains `normal/`,
`spam-wins/`, and `spam-intended/`, each with the unchanged `report.json`, every
referenced PNG in `screenshots/`, and the referenced WebM in `video/`.
`manifest.json` maps original paths to artifact paths and records file sizes and
SHA-256 digests. To resolve a report's `.probe/...` reference after extraction,
replace `.probe/` with that scenario's directory name.

Only these explicit files are copied; other hidden files and unreferenced media
are excluded. Missing, empty, or disallowed evidence in any scenario fails the
staging step. Staging and upload still run after a failed probe, retaining any
available evidence plus manifest errors for diagnosis. Uploading no files is an
error. Machine verdicts retain their existing meaning; successful CI is not a
human playtest PASS.
