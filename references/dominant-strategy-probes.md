# Adversarial dominant-strategy probes

Use when player feedback, procedural content or a material mechanic change reveals
a repeatable shortcut which could erase the intended player decision. This is
optional for ordinary fixes and release-only tasks, and supplements—not
replaces—the existing fast PROBE spam/idle/repeat checks.

## Define the player promise, not a universal difficulty score

Record which cue should be observable, what player choice or timing it enables,
what failure feedback teaches, and which shortcut would negate that experience.
Repeated inputs may be *desirable* in rhythm or idle games; never treat a high
win rate as intrinsically bad. For each scenario/seed, run a plausible player
policy as well as one or more deliberately simple policies.

The runner tests these policy shapes:

- idle and hold-jump (wait/spam);
- jump-pulse and right-jump (blind repetition or one-direction solution);
- edge-camp (move to a convenient edge, then repeat jump);
- micro-scout (small alternating horizontal movements revealing cues);
- dash-spam (use dash whenever possible);
- custom (project adapter implements a legitimate cue-reacting policy).

## Adapter must drive ONE authoritative production core

The project supplies a small ESM adapter imported by
scripts/run_strategy_probes.mjs. It exports:

    export async function createSession({scenario,seed}) {
      // Initialize real game logic with the named scenario and injected seed.
      return {
        observe() { return {status:'PLAYING',x:0,progress:0}; },
        step({left,right,jump,dash},dtMs) {
          // Advance the SAME production core and return fresh observation.
          return {status:'PLAYING',x:0,progress:0};
        }
      };
    }

The above illustrates the interface only, **not** a usable production adapter.
Return a real game observation with status PLAYING/WIN/LOSE, optional position
x/progress and stable decision_marker. Do not expose future hidden state to
strategy policies. For custom policies, export customPolicy(name, context)
which receives only tick, observed, scenario and seed.

Create a local JSON configuration from templates/strategy_probe_config.json.
Set the adapter path relative to that configuration, exact source_id (commit
or build identity), named scenarios, seeds, action budget and dt_ms. Define
max_win_rate ceilings only when the game-specific design justifies them.
No ceiling means descriptive diagnostic only, not PASS.

Run from a real project workspace:

    node /skill-root/scripts/run_strategy_probes.mjs \
       --config spec/strategy_probes.json --out logs/strategy_probes.json

Outputs: one JSON report with every attempt, seed, scenario, strategy,
outcome, action counts, maximum progress, observed decision markers and a
bounded input trace. Status and CLI exit meanings:

- RISK_DETECTED / exit 1: at least one strategy exceeded its declared ceiling;
  investigate whether this actually bypasses the intended mechanic.
- RUNTIME_ERRORS / exit 2: adapter/core/policy failed, **not** game rejection.
- UNSCOPED_DIAGNOSTIC / exit 0: no ceilings, only observations.
- NO_DECLARED_LIMIT_BREACHED / exit 0: for these tested policies/seeds only.
- Invalid config / exit 3: no experimental evidence; correct the input.

Reproduce a concerning seed with the same action trace. Fix the smallest
causal mechanic, then rerun that same seed and a normal player path. A model
can detect structural exploits, not certify human enjoyment or long-term
engagement. Preserve browser/physical-input evidence separately.

## Echo Tide regression shapes

- Blind jump repetition can bypass cues when platforms appear after a jump.
- One extreme edge plus jump repetition can trivialize stacked platform paths.
- Tiny horizontal movement can expose future opportunities cheaply, replacing
  the intended timing choice.
- A dash that can never recharge may add friction without adding repeated
  decisions; static platforms may similarly fail to exploit the new action.

These are counterexample *classes*, not fixed thresholds or universal rules.
Use project-specific actual cores, legal actions and input timing. Synthetic
tests/test_strategy_probes.mjs checks the probe runner, not Echo Tide itself.
