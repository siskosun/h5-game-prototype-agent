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

## Optional upstream opportunity card

An externally supplied `game-opportunity` card is research context, never a required precondition for H5 PROBE. Keep its stable opportunity ID/source link and verified revision in ordinary brief context. If the card and PROBE test exactly the same falsifiable hypothesis and stop condition, preserve the precise wording when writing the existing `probe_card.md`. If the stage has changed (e.g., from player interest to mechanic experience), explicitly define the new testable hypothesis and kill criteria instead of silently treating demand evidence as proof of gameplay. Do not add unsupported `probe_card.md` fields or create a second probe history. The existing `scripts/probe_log.py` searches the selected local `probes.jsonl`; it is not a cross-project opportunity database. Return verified PROBE evidence for optional append to the upstream card; no automatic user promotion.

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

## Consequential-rule oracle calibration

For a rule that changes scoring, legal actions, time windows, terminal outcomes or resources, validate one behavioral boundary against the production core. In a disposable copy outside the project, demonstrate that the same test rejects a deliberately wrong implementation and accepts a semantically equivalent correct implementation. Preserve the exact check and outputs. Do not build a universal mutation system or elevate these local results to game-exp trusted evidence.

## Working-source identity

New PROBE reports include `source_tree_sha256` alongside legacy `source_sha` (often Git HEAD) and `build_id`. Hash source and configuration bytes from the project root, including uncommitted files but excluding only conventional generated directories directly under the project root (not same-named nested source folders). Validate `--source-root .` after QA to detect later changes. Legacy reports without the field are still readable but lack content-binding. This fingerprint does not establish a trusted Candidate identity, nor prove that a build was generated from the source.

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

### Optional preregistered external player test

When upstream `game-opportunity` provides a v0.4 local plan/digest for a **real player-behavior test**, preserve its plan identifier and exact metrics in ordinary context. Real testers may provide one anonymized aggregate of **unique eligible participants**, observed action count, window and sampling limitations after authorized sessions. An agent's QA runs, Playwright input, mock users and AI preference guesses are not real participants. Do not silently broaden the H5 frozen hypothesis or kill criteria to match a market threshold. Link source/build identity back to the opportunity record only as reported evidence; human PROBE verdict and game-exp Review remain separate.

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
