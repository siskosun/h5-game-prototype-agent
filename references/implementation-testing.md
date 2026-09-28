# Implementation and deterministic testing

## Preserve the existing stack when possible

For existing projects, reuse current framework, architecture, state ownership, input model, and build tools unless they block the requested result.

For new 2D H5 projects, prefer:

- DOM + TypeScript/Vite for cards, management, grid/board, inventory, and UI-heavy interactions.
- Phaser + TypeScript/Vite for continuous movement, collision, projectiles, action, or realtime combat.

Use simpler plain HTML/CSS/JS when it is sufficient for the scope.

## One authoritative gameplay core

Keep gameplay rules outside rendering. Rendering/UI may read state and dispatch legal actions, but must not reimplement gameplay formulas.

Inject or control RNG, time, storage, and external dependencies needed for deterministic tests.

Expose browser test hooks for deterministic state inspection and stepping. Test normal player behavior through real UI separately.

## Node headless harness

Drive the same production core from Node. Prefer direct import. If the game is physically bundled into one HTML, use a thin adapter or minimal DOM/localStorage/timer stubs rather than rewriting rules.

Start from `templates/sim-harness.mjs`.

The harness should report at least:

- runs;
- runtimeErrors;
- invariantFailures;
- softlocks;
- failingSeeds;
- firstFailure with seed, action trace, and state when possible.

Treat a harness that tests a duplicate implementation as invalid evidence.

## Acceptance and stress

Use deterministic Given/When/Then tests for P0 rules. Stress rules that can compound or deadlock.

For runtime modifiers, define only when applicable:

- stack mode: additive, multiplicative, replace, strongest-only, etc.;
- maximum stacks/duration;
- stable base used for percentage changes;
- numeric envelope at maximum declared stack depth.

Avoid repeatedly multiplying the current value when the intended rule is a stable-base penalty, unless the compounding behavior is explicitly designed.

## RNG

Use seeded/injected RNG for gameplay behavior that affects tests or reproducibility. Preserve failing seeds.
