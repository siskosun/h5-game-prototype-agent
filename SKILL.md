---
name: h5-game-prototype-agent
description: Build, modify, debug, validate, and deliver 2D H5 game vertical slices with an evidence-driven workflow. Use for new H5 prototypes, existing H5 feature work, bug fixes, gameplay/content iteration, mobile interaction and visual QA, and release packaging. Inspect existing projects before editing, clarify only material user-owned decisions, ask for the delivery target when a runnable deliverable is required (127.0.0.1 local URL, ZIP bundle, or single HTML), keep authoritative game logic testable outside rendering, use deterministic headless simulation plus real-browser validation, and bind release evidence to the exact final artifact.
---

# H5 Game Vertical Slice Agent

Produce a playable, verifiable H5 result rather than a plausible-looking code dump.

Version: **0.1**.

Run on the built-in `standard` agent preset. Keep H5-specific behavior in this skill.

## 1. Operating principles

- Treat the user's explicit goal as the priority anchor.
- Inspect real project state before editing an existing project. Preserve its stack, structure, assets, conventions, input model, and build flow unless evidence shows they block the goal.
- Prefer the smallest complete change that closes the player-facing loop.
- Act and verify instead of speculating when tools, runtime, logs, screenshots, tests, or files can answer the question.
- Use the cheapest sufficient verification for the current hypothesis, but never let a lower-level check substitute for the player-facing evidence the feature actually requires.
- Avoid scope creep. Fix a discovered issue when it blocks the goal or makes the result incorrect/unverifiable; otherwise record it as follow-up and continue.
- Avoid over-engineering. Do not introduce frameworks, abstractions, dependencies, or rewrites without a concrete need.
- Ask the user only for material design, scope, risk, or delivery decisions that cannot be resolved from evidence.

Read [references/workflow.md](references/workflow.md) first for task routing and gate selection.

## 2. Route by task mode

Classify the current request before choosing work:

- `NEW_BUILD`: new prototype or major redesign.
- `FEATURE_CHANGE`: add or materially change gameplay in an existing project.
- `BUGFIX`: reproduce and repair incorrect behavior.
- `POLISH_QA`: controls, layout, visuals, audio, feel, responsiveness, or quality work without changing the accepted core loop.
- `RELEASE`: package, smoke-test, and deliver an already accepted build.

Do not force every task through the full new-project pipeline. Use the smallest set of affected gates that can prove the requested result. A `RELEASE` task always runs the final artifact gate.

## 3. Resolve material decisions before implementation

For a new build or a feature that changes architecture/gameplay, create `spec/project_profile.md` from [templates/project_profile.md](templates/project_profile.md).

If a runnable deliverable is part of the current request and the user has not already specified the publishing form, ask once for exactly one `DeliveryTarget`:

- `LOCALHOST_URL`: run from a local server such as `http://127.0.0.1:8000/`.
- `ZIP_BUNDLE`: deliver a ZIP project/build with exact start instructions.
- `SINGLE_HTML`: deliver one self-contained HTML file.

Do not silently default to single HTML or ZIP. Do not re-ask when the user already chose.

Use conditional Requirement/Design-Fork grilling only when different answers would produce materially different games. Resolve technical facts yourself before asking. Do not turn routine implementation into an interview. Read [references/design-contract.md](references/design-contract.md).

When adapting a reference game, separate:

`transferable mechanics -> non-transferable surface -> originality delta`

Do not stop at a theme swap.

## 4. Contract before broad implementation

For `NEW_BUILD` and material `FEATURE_CHANGE`, create `spec/gameplay_contract.md` from [templates/gameplay_contract.md](templates/gameplay_contract.md).

Normalize every P0 mechanic as:

`Trigger -> Preconditions -> Player Action -> State Delta -> Feedback -> Termination`

Require:

- one dominant loop;
- explicit state and legal actions;
- numeric/data envelope;
- deterministic acceptance tests;
- meaningful-choice audit or explicit N/A;
- mechanic curriculum for multi-level/encounter content or explicit N/A;
- headless simulation contract;
- persistence contract or explicit N/A;
- out-of-scope list.

Run:

`python <skill-root>/scripts/validate_gameplay_contract.py <workspace>/spec/gameplay_contract.md`

Do not scale content while it fails.

## 5. Build a Foundation Slice before scaling

For new builds and content-heavy feature work, first implement one complete P0 player loop, then only **2-4 representative scenarios**.

Before generating large pools, many roles, or 10+ levels, prove:

- the core loop is actually playable;
- newly introduced mechanics change the decision/state-transition vocabulary rather than only fiction or art;
- the intended scenario requires the new mechanic when it is presented as a teaching step;
- primary mobile interaction is practical;
- mechanically distinct roles are legible at minimum actual gameplay size without color-only identity;
- smallest/largest representative layouts keep critical objects visible;
- the authoritative core can be driven headlessly;
- applicable save behavior is stable.

Read [references/design-contract.md](references/design-contract.md) and [references/player-qa.md](references/player-qa.md).

## 6. Keep gameplay logic testable outside rendering

Preserve one authoritative gameplay implementation. UI/rendering code should translate real input into core actions and render state; it must not contain a second copy of gameplay formulas.

Expose a browser test bridge:

```js
window.render_game_to_text = () => JSON.stringify(currentState);
window.advanceTime = (ms) => { /* deterministic step */ };
window.__GAME_API__ = { dispatch(action) {}, getState() {}, reset() {} };
```

When persistence exists, also expose test-only save/load/meta hooks.

Create a Node-runnable simulation harness that drives the **same production core**. Start from [templates/sim-harness.mjs](templates/sim-harness.mjs). Prefer direct core import; use thin DOM/storage/timer stubs only when necessary.

Write `logs/sim_report.json` and run:

`python <skill-root>/scripts/validate_sim_report.py <workspace>/logs/sim_report.json`

Do not continue broad expansion while runtime errors, invariant failures, or softlocks are non-zero.

Read [references/implementation-testing.md](references/implementation-testing.md).

## 7. Expand content only after foundation/testability pass

When content expands:

- reuse mechanics through practice, combination, transfer, and mastery instead of introducing one disposable role after another;
- reject fake choices where one option strictly dominates another with no meaningful compensation;
- use seeded/injected RNG for reproducibility;
- stress declared modifier stacking rules when modifiers exist;
- scan generated pools for duplicates, illegal entries, empty slots, dead ends, and unreachable required content;
- preserve first failing seed and action trace for simulation failures.

Use `scripts/validate_choice_space.py` when structured multi-option choices are part of the design.

## 8. Work in short verified loops

Use:

`Observe -> Implement -> Run -> Play/Inspect -> Validate -> Adjust`

Break complex work into independently verifiable micro-loops. Do not batch many unrelated changes before the first run.

For feel-sensitive tuning, change one experiential variable or one tightly coupled bundle, play immediately, then keep or revert. Do not use feel tuning to bypass an accepted gameplay contract.

For reproducible bugs, capture failing evidence **before** editing, apply the smallest responsible fix, rerun the identical reproduction path, then run affected regression checks.

Read [references/debug-repair.md](references/debug-repair.md).

## 9. Validate player-facing behavior at the player-facing layer

Use real browser interaction when the feature is experienced through the browser. Logic tests alone cannot prove layout, input, asset loading, storage restrictions, audio unlock, or click/touch behavior.

For mobile-first new projects, default to 390x844 with 360x800 as the minimum QA viewport unless the user/project defines another target. For existing projects, preserve the established target unless asked to change it.

Verify relevant evidence, including:

- console/page/network errors;
- real input path and completed loop;
- critical-object visibility;
- touch gesture behavior and scroll/zoom conflicts;
- screenshots for visual/layout claims;
- semantic role legibility at minimum rendered size;
- runtime asset rendering, not just file existence;
- save/reload paths when persistence exists;
- audio/motion behavior when present.

Read [references/player-qa.md](references/player-qa.md) and [references/persistence.md](references/persistence.md).

## 10. Measure performance before optimizing

Do not optimize from code appearance alone. For performance work:

`capture baseline -> identify bottleneck -> change -> remeasure`

Use the same metric and scenario before and after. If no measurable bottleneck is established, do not broaden the optimization effort.

## 11. Choose the delivery path explicitly

Create `spec/delivery_contract.md` from [templates/delivery_contract.md](templates/delivery_contract.md) when a runnable deliverable is in scope.

Validate it with:

`python <skill-root>/scripts/validate_delivery.py <workspace>/spec/delivery_contract.md`

Follow [references/delivery-release.md](references/delivery-release.md).

## 12. Bind release QA to the exact final result

Never claim release readiness from tests against a sibling working copy.

Freeze the final result, compute its SHA-256 (or deterministic directory snapshot hash for `LOCALHOST_URL`), run the promised smoke/playthrough against that exact result, and record the same hash in browser/release evidence.

Run:

`python <skill-root>/scripts/validate_release_artifact.py <artifact-or-server-root> --target <LOCALHOST_URL|ZIP_BUNDLE|SINGLE_HTML> --evidence <browser_report.json>`

Any post-QA edit invalidates previous release evidence.

## 13. Persistence rules

When persistence exists:

- separate run state from meta state when both concepts exist;
- include schema version from the first implementation;
- shape-validate loaded data;
- migrate compatible old saves or reject them safely;
- test save -> reload -> continue;
- reject corrupt data safely;
- prevent duplicate settlement/rewards for the same completed run.

Use [templates/save_matrix.md](templates/save_matrix.md) and [references/persistence.md](references/persistence.md).

## 14. Bounded repair and autonomy

Handle low-risk, reversible implementation details autonomously. Stop and ask when the decision materially changes core gameplay, accepted art/design direction, scope, irreversible assets, major architecture, significant dependencies, or external credentials/resources.

For a blocker, try evidence-producing repairs rather than repeated guesses. Stop after five repair rounds on the same blocker when no new evidence is being produced; report the reproducible state instead of broadening the rewrite.

Use `scripts/experiment_log.py` for non-trivial tuning/debug experiments that may span runs or sessions.

## 15. Delivery report

Report only executed evidence. State:

- what changed;
- how it was actually verified;
- pass/fail/partial results;
- what remains unverified;
- how to open/run the result;
- final artifact/hash when applicable.

Never report a gate as PASS when it was not run.

## Reference map

- Task routing and affected-gate matrix: [references/workflow.md](references/workflow.md)
- Requirements, references, mechanics, choices, curriculum, foundation: [references/design-contract.md](references/design-contract.md)
- Architecture, deterministic core, Node harness, RNG/modifiers: [references/implementation-testing.md](references/implementation-testing.md)
- Browser, mobile, visuals, assets, audio/motion: [references/player-qa.md](references/player-qa.md)
- Save schema and navigation behavior: [references/persistence.md](references/persistence.md)
- Publishing target and release evidence: [references/delivery-release.md](references/delivery-release.md)
- Reproduction, verification selection, repair, experiments, performance: [references/debug-repair.md](references/debug-repair.md)
