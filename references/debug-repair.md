# Debugging, repair, verification choice, and performance

## Reproduce before repair

For a reproducible bug:

`reproduce -> capture failure -> narrow scope -> fix -> same reproduction -> regression`

Prefer the user's actual failing path. Do not modify suspicious code first when the failure can be observed cheaply.

Do not manufacture success by swallowing exceptions, disabling assertions/tests, hard-coding success, or weakening acceptance criteria.

## Minimum sufficient verification

Choose the lowest-cost evidence that can prove the current hypothesis:

- pure state/formula bug: targeted unit/headless test;
- simulation/softlock/balance bug: deterministic harness with seed/trace;
- input/layout/visual bug: real browser interaction and screenshot;
- save bug: exact save/reload/navigation reproduction;
- asset bug: runtime load/render evidence;
- release issue: exact final artifact/server-root smoke;
- performance issue: measured baseline and same metric after change.

Lower-level PASS does not prove a higher-level player-facing claim.

## Bounded repair

For each failed attempt:

1. state the hypothesis;
2. change the smallest responsible surface;
3. rerun the failing path;
4. capture new evidence;
5. rerun affected regression only after the direct failure is fixed.

If repeated attempts stop producing new evidence, change method. After five repair rounds on the same blocker without meaningful progress, stop broadening the rewrite and report the reproducible blocker.

Use `scripts/experiment_log.py` for named experiments that may span multiple runs or sessions. Do not repeat an already disproven configuration unless the retest has a stated reason.

## Performance

Do not infer a performance problem from code shape alone.

Use:

`baseline -> bottleneck evidence -> smallest optimization -> same measurement`

Do not optimize unrelated systems when the measured target already meets the requirement.
