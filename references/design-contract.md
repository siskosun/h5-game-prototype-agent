# Design and gameplay contract

## Resolve only material ambiguity

Use Requirement Grill when the request is vague, contradictory, oversized, or feasibility alternatives would produce materially different games. Resolve facts from files/tools/research before asking the user.

Use Design-Fork Grill only when two or more credible, non-dominated directions remain and the choice materially changes the loop, fantasy, decision density, pacing, risk/reward, controls, progression, content architecture, or scope.

Ask the current independent decision frontier, give a recommendation and main tradeoff, and require confirmation before locking the affected design. Do not ask routine implementation questions.

Use `templates/design_forks.md` and `scripts/validate_design_forks.py` when a material fork exists.

## Deconstruct references

For a referenced game or product, separate:

1. Transferable mechanics: player verbs, information structure, spatial/economic relationships, pacing, failure/recovery, progression logic.
2. Non-transferable surface: names, characters, story, visual identity, authored levels, copyrighted expression.
3. Originality delta: at least one meaningful mechanic/system/interaction change that makes the prototype more than a theme swap.

Research only implementation-relevant facts. Separate sourced facts from inference.

## Mechanic IR

Describe every P0 mechanic as:

`Trigger -> Preconditions -> Player Action -> State Delta -> Feedback -> Termination`

Also state invalid actions and recovery/restart behavior.

## Meaningful choices

Reject a recurring choice when A is no worse than B on every player-relevant dimension and strictly better on at least one, while B has no compensating cost, timing, risk, constraint, synergy, stacking, or future-option advantage.

For structured option systems, require at least one reachable rational context for each recurring option. Use `scripts/validate_choice_space.py` when data can express the comparison.

## Mechanic curriculum

For multi-level/encounter prototypes, organize core mechanics through useful learning stages rather than one-off introductions:

`Introduce -> Practice -> Combine -> Transfer -> Mastery`

Do not require every mechanic to use every stage mechanically; require the overall sequence to demonstrate reuse and increasing reasoning depth.

A new character/theme does not count as new gameplay unless it adds a distinct state transition/decision pattern and the intended teaching scenario actually requires it.

## Foundation Slice

Before broad expansion, build 2-4 representative scenarios that collectively cover:

- base loop;
- at least one interaction/combo case;
- smallest/largest or simplest/densest relevant layout;
- primary mobile gesture;
- role/icon semantic legibility;
- applicable persistence checkpoint;
- production-core headless execution.

Do not scale to 10+ levels, large option pools, or many roles before these are stable.
