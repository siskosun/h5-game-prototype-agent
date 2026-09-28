# Workflow and task routing

Use one task mode per current request. Change mode only when the user's goal materially changes.

## Task modes

### NEW_BUILD
1. Resolve Project Profile and DeliveryTarget when delivery is in scope.
2. Resolve material requirement/design forks.
3. Write Gameplay Contract.
4. Select smallest stable implementation profile.
5. Build one complete P0 loop.
6. Build 2-4 Foundation scenarios.
7. Prove headless testability and player-facing controls/visual language.
8. Expand content only after foundation/testability pass.
9. Run real-browser, responsive, persistence, and release checks as applicable.

### FEATURE_CHANGE
1. Inspect the existing project and baseline behavior.
2. Update only the affected contract when behavior/design changes materially.
3. Implement in a short verified loop.
4. Run affected logic and browser regressions.
5. Run release validation only when a deliverable is requested.

### BUGFIX
1. Reproduce and capture failing evidence when reproducible.
2. Narrow the responsible surface.
3. Apply the smallest fix.
4. Rerun the identical reproduction path.
5. Run adjacent regression checks.
6. Do not expand scope to unrelated defects.

### POLISH_QA
1. Capture a baseline screenshot/interaction/metric.
2. Change one visual, interaction, audio, or feel surface at a time.
3. Validate in the real browser at the relevant viewport/input mode.
4. Keep/revert based on evidence.
5. Do not alter accepted gameplay rules without contract backflow.

### RELEASE
1. Freeze the accepted build.
2. Validate the selected DeliveryTarget.
3. Produce the final artifact/server directory snapshot.
4. Compute SHA-256.
5. Run smoke/playthrough against the exact final result.
6. Bind evidence to the same hash.
7. Deliver without post-QA edits.

## Affected-gate rule

Run only gates that can prove the requested change, except final release which always requires the artifact gate.

- Pure logic change: acceptance/headless first; browser regression if player-visible behavior can change.
- Input/layout/visual change: real browser + screenshot/interaction evidence.
- Persistence change: save matrix + reload path.
- Asset change: runtime render evidence + load/network checks.
- Performance change: baseline metric + same metric after change.
- Release: final artifact smoke + evidence hash match.

## Existing-project inspection

Before editing, identify the actual stack/version, directory structure, entrypoint, input system, state ownership, rendering/UI approach, assets, build/start commands, tests, and current errors/warnings relevant to the task.

Prefer existing architecture and engine/framework capabilities. Do not rewrite a working subsystem merely because another design is more familiar.

## Task boundary

Fix a newly discovered issue now only when it:

- blocks the current goal;
- can make the current result incorrect;
- prevents meaningful verification; or
- would cause obvious immediate rework in the current task.

Otherwise record it as risk/technical debt/follow-up and continue.
