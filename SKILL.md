---
name: h5-game-prototype-agent
description: Build, modify, debug, validate, and deliver 2D H5/web mini-games, including fast gameplay experiments and mechanic probes. Use for H5, web games, 网页小游戏, 快速试玩法, 玩法初筛, mechanic probe, browser gameplay, mobile interaction, bug fixes, polish, vertical slices, Playwright QA, and tested delivery.
---

# H5 Game Prototype Agent

Produce a playable, verifiable H5 result rather than a plausible code dump. Keep one authoritative gameplay core and verify only claims that were actually exercised.

## 1. Choose completion level separately from task mode

Choose one completion level:

- **PROBE** — fast graybox test of one gameplay hypothesis.
- **SLICE** — small but complete vertical slice or delivery-quality H5 build.

Choose task mode independently:

- `NEW_BUILD`
- `FEATURE_CHANGE`
- `BUGFIX`
- `POLISH_QA`
- `RELEASE`

Examples: a bug in a mechanic probe is `BUGFIX + PROBE`; a polished new browser game is `NEW_BUILD + SLICE`.

Select **PROBE** when the request says or implies batch exploration, fast trials, initial screening, validating one mechanic, 快速试玩法, 玩法初筛, or mechanic probe. Select **SLICE** for complete/playable-for-others/near-release/vertical-slice requests. For an ambiguous new project, default to PROBE and state that default in the first reply; the user may override it. Never re-ask after the level is resolved.

For PROBE, read [mechanic probe](references/mechanic-probe.md). For SLICE or non-probe work, read [workflow](references/workflow.md).

## 2. PROBE is intentionally narrower

In PROBE:

- use `LOCALHOST_URL`; do not ask for DeliveryTarget;
- use `probe_card.md`, not `gameplay_contract.md`;
- build one repeatable core loop, not 2-4 foundation scenarios;
- run fixed checks plus at most 50 seeded smoke runs, not the SLICE-scale simulation target;
- stay graybox; do not request visual references or begin art direction;
- compute build identity/digests only when handing the probe to game-exp or another explicit evidence consumer;
- ask only questions that materially change the hypothesis.

Still require:

- one authoritative gameplay implementation;
- the QA/test interface;
- a real browser player path using real input;
- evidence only for checks actually executed;
- human judgment for fun/preference.

Do not let automated checks produce a human PASS.

## 3. For SLICE, preserve the existing contract workflow

For a new or materially changed SLICE, create `spec/project_profile.md` and `spec/gameplay_contract.md`. Normalize P0 mechanics as:

`Trigger -> Preconditions -> Player Action -> State Delta -> Feedback -> Termination`

Build one complete P0 loop before scaling content. Use 2-4 representative scenarios, keep logic testable outside rendering, run the intended browser target early, and bind release evidence to the exact final artifact. See [design contract](references/design-contract.md), [implementation testing](references/implementation-testing.md), [player QA](references/player-qa.md), and [delivery/release](references/delivery-release.md).

## 4. Keep time and randomness reproducible

For new templates and mechanics that depend on time or randomness:

- keep `realtime | manual` clock modes;
- in manual mode, browser animation/update loops must not advance gameplay time;
- advance time only through the deterministic test hook;
- keep seeded RNG state in the authoritative game state;
- do not call `Math.random()` for gameplay outcomes that need reproducibility.

The bundled DOM, Phaser, and PROBE templates implement this contract.

## 5. Keep the QA bridge out of production

Preserve:

- `render_game_to_text`;
- `advanceTime(ms)`;
- `window.__GAME_API__.dispatch/getState/reset`.

QA interface v1 also exposes `setSeed`, `setScenario`, `setClockMode`, `getInputLog`, and `version: "1"`.

Record browser/player actions as `PLAYER`; programmatic `dispatch` as `INJECTED`; Playwright touch emulation as `EMULATED_TOUCH` in browser evidence.

Install the bridge only in Vite dev mode or when `VITE_QA=1` (for `build:qa`). A normal `npm run build` must not contain `__GAME_API__`.

## 6. Work in short verified loops

Use:

`Observe -> Implement -> Run -> Play/Inspect -> Validate -> Adjust`

For a reproducible bug, capture failing evidence first, apply the smallest responsible fix, rerun the same path, then affected regressions. Do not broaden a repair merely because another improvement is possible.

Use the cheapest sufficient check for each claim, but never substitute a logic test for browser input/layout behavior or an automated policy for human experience.

## 7. Browser evidence

For player-facing browser behavior, verify at the browser layer:

- console/page/network errors;
- real input and a complete player path;
- target viewport and critical visibility;
- click/touch/keyboard behavior as applicable;
- screenshots for visual/layout claims;
- save/reload when persistence exists;
- audio/motion when promised.

Mobile-first defaults to 390x844 unless the project specifies another target. Playwright touch is emulated evidence, not proof of physical-device feel.

## 8. PASS after a probe has two exits

After a real human `PASS`:

- upgrade to SLICE using [probe to slice](references/probe-to-slice.md); or
- hand the probe to game-exp using [game-exp integration](references/game-exp-integration.md).

Do not rewrite the frozen hypothesis/kill criteria during the handoff merely to make the next stage easier.

## 9. Evidence and verdicts

For PROBE:

- `agent_verdict`: `READY_FOR_PLAYTEST | MACHINE_REJECT | UNCERTAIN`;
- `human_verdict`: `PENDING | PASS | REJECT | UNCERTAIN`.

An agent never sets PASS. A harness/environment failure is `UNCERTAIN`, not evidence that the mechanic should be rejected.

For SLICE, report only executed evidence and the exact artifact/hash when applicable. Never label an unrun gate PASS.

For a game-exp-managed implementation pass, return one structured `iteration_delivery` object after completed source work. Include 1-8 player-visible changes, a verified playable descriptor or explicit `MISSING`, 1-3 playtest focus points, `producer=h5-game-prototype-agent`, optional build identity, and an optional real prior Candidate id. When the game-exp handoff requests a shareable URL for a public repository, prefer the bundled immutable GitHub Pages publisher after local build/player QA, then run the real browser smoke against the deployed URL before setting `verified=true`. It is participant-reported implementation context only and never authorizes Review, PROMISING, SELECTED, REJECTED, Integration, or Archive.

## 10. Utilities

From the skill root:

```bash
python scripts/probe_card.py validate PROBE/probe_card.md
python scripts/probe_card.py freeze PROBE/probe_card.md
python scripts/probe_card.py check PROBE/probe_card.md
python scripts/probe_log.py search KEYWORD
python scripts/validate_probe_report.py PROBE/.probe/report.json --card PROBE/probe_card.md
python scripts/validate_gameplay_contract.py WORKSPACE/spec/gameplay_contract.md
python scripts/validate_release_artifact.py ARTIFACT --target LOCALHOST_URL --evidence browser_report.json
python scripts/publish_github_pages.py --repo owner/repo --source dist --version-key <source_sha> --producer h5-game-prototype-agent --require-relative-entrypoint --json
```

The PROBE scaffold supports:

```bash
npm ci
npm test
npm run build
npm run probe:check
```

## Reference map

- PROBE eight-step workflow, time box, degeneracy, human testing: [mechanic probe](references/mechanic-probe.md)
- Probe -> SLICE: [probe to slice](references/probe-to-slice.md)
- Probe -> game-exp: [game-exp integration](references/game-exp-integration.md)
- SLICE routing: [workflow](references/workflow.md)
- Gameplay contract/design: [design contract](references/design-contract.md)
- Core/tests/RNG: [implementation testing](references/implementation-testing.md)
- Browser/mobile/player QA: [player QA](references/player-qa.md)
- Persistence: [persistence](references/persistence.md)
- Release evidence: [delivery/release](references/delivery-release.md)
- Debug/repair: [debug repair](references/debug-repair.md)
