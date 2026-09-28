# Mechanic Probe

Use this only for completion level `PROBE`. The purpose is rapid gameplay screening, not a miniature release process.

## Fixed eight-step loop

1. Write one sentence describing the intended player experience.
2. Write the core mechanic, falsifiable hypothesis, and observable kill criteria in `probe_card.md`; validate and freeze it.
3. Build the smallest graybox repeatable loop inside the declared time box.
4. Run one complete browser player path using real click/keyboard/touch input without using QA hooks to force gameplay state.
5. Run machine checks: success, failure, retry, one boundary case, and degeneracy probes.
6. Capture screenshots at the target viewport and a short player-path video.
7. Batch human playtests when probes are ready.
8. Record `agent_verdict`, `human_verdict`, and the derived final status.

## Search previous probes first

Before implementation:

```bash
python scripts/probe_log.py search KEYWORD
```

If a similar probe exists, state the meaningful difference or the prior record's `revisit_when` condition that justifies retrying. Do not repeat a failed idea without new information.

## Freeze the question

The probe card contains:

- `probe_id`
- `experience_goal`
- `core_mechanic`
- `hypothesis`
- `kill_criteria`
- `intended_degenerate_strategies`
- `target_viewport` (default 390x844)
- `input_mode`: mouse/touch/keyboard
- `time_box`
- 2-3 `human_observation_points`
- `frozen_at`, `frozen_sha256`

`kill_criteria` must describe observable failure, not only “不好玩 / not fun”.

Freeze before broad implementation:

```bash
python scripts/probe_card.py validate probe_card.md
python scripts/probe_card.py freeze probe_card.md
python scripts/probe_card.py check probe_card.md
```

If the hypothesis or kill criteria must change after freeze, create a new `probe_id` or make an explicit revision and reset both verdicts. Never edit the frozen question silently.

## Time box and repair limit

Default time box: **4 hours actual work**. Record another value only when the task requires it.

For the same blocker, attempt at most **3 evidence-producing repair rounds**. When the time box or repair limit is exhausted, stop. Use:

- `UNCERTAIN` when the remaining blocker is harness/environment/presentation ambiguity;
- `MACHINE_REJECT` when an observed mechanic/implementation outcome meets a kill criterion.

Extending the probe requires user approval.

## Machine checks

Run `npm run probe:check` for the scaffold or an equivalent browser workflow.

Required checks:

- page/console/network health;
- manual-clock determinism;
- complete real-input player path;
- success;
- failure;
- retry;
- one boundary case;
- spam;
- idle;
- repeated-one-action strategy.

Scenario/seed/manual-clock hooks may prepare machine-check preconditions. For the player path itself, do not use the test interface to write success state.

### Degenerate strategy probes

Under manual clock + fixed seed:

- **spam**: trigger the main action at high frequency;
- **idle**: advance meaningful simulated time without player input;
- **repeat**: use only one legal action repeatedly.

If an undeclared degenerate strategy wins or produces an outcome equivalent to normal successful play, set `agent_verdict=MACHINE_REJECT`. If that strategy is explicitly listed in `intended_degenerate_strategies`, do not reject it for that reason.

## Evidence source

Use:

- `PLAYER` — normal browser click/keyboard path;
- `INJECTED` — QA/test API action or deterministic time/scenario setup;
- `EMULATED_TOUCH` — Playwright touch emulation.

If target input is touch, state that physical-device feel remains a human/device validation need.

A harness launch error, timeout, selector breakage, or browser/tool failure is `INCONCLUSIVE`; classify the reason as `HARNESS` and set `agent_verdict=UNCERTAIN`. Do not reject the mechanic from harness failure.

## Human playtest

Before playtesting, keep 2-3 observation points frozen in the card.

For each human session:

- first run gets no coaching;
- record observed behavior separately from interpretation;
- record participant statements separately from observation;
- pool several ready probes into one batch when efficient.

Do not fabricate participation. Until a real human record exists, `human_verdict=PENDING`.

## Verdict derivation

Agent verdict:

- `READY_FOR_PLAYTEST` — machine prerequisites hold;
- `MACHINE_REJECT` — an observed non-harness failure meets a kill condition or non-intended degeneracy succeeds;
- `UNCERTAIN` — evidence is incomplete or a harness/environment issue prevents a clean inference.

Human verdict:

- `PENDING`
- `PASS`
- `REJECT`
- `UNCERTAIN`

Final status:

- `MACHINE_REJECT` -> `REJECT`;
- otherwise use the human verdict;
- if human verdict is `PENDING`, status is `WAITING_FOR_PLAYTEST`.

## Handoff evidence

When a probe moves into game-exp, bind the exact source/build:

- `source_sha`
- `build_identity`
- executed checks and environment
- artifacts with `id`, `kind`, `location`, `digest`, `portable`

Local-only screenshots/video are `portable=false` unless copied to a durable shared location.
