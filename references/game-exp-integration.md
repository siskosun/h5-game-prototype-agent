# game-exp integration

Use when a PROBE or H5 SLICE is handed to game-exp.

## Authority split

game-exp owns:

- experiment identity and protected Ledger/Manifest;
- lifecycle and canonical experiment branch;
- scope boundaries;
- Candidate identity;
- human Review;
- PROMISING / SELECTED / REJECTED decisions;
- Rehearsal, Integration, and Archive.

This H5 skill owns implementation and evidence only. It must never record Review or advance PROMISING, SELECTED, or REJECTED on its own.

## node-npm adapter contract

The H5 experiment must support:

```bash
npm ci
npm test
npm run build
```

Candidate output is `dist/`, and `dist/index.html` must exist.

Use the repository/project policy's pinned Node version when game-exp specifies one. The current validated example uses Node 26.10.0.

## Manifest hypothesis

When binding:

- either reuse the exact frozen probe-card hypothesis and kill criteria; or
- state a genuinely new next-stage question, such as whether the experience survives broader human sessions or repeated play.

Do not silently rewrite the old hypothesis to re-prove something already tested.

## Handoff evidence

Return:

- `source_sha`
- `build_identity`
- checks actually executed and their environment
- artifacts, each with `id`, `kind`, `location`, `digest`, and `portable`

Mark artifacts that exist only on the developer machine as `portable=false`.

## Repository layout

Verified against the current `siskosun/game-exp` `main` implementation on 2026-09-28: Candidate install/test/build commands run with repository-root `cwd=.`. Project-policy step objects contain only `argv`; `subject.root_path` is not used as a build working directory.

Therefore a repository containing several nested probes is **not automatically buildable per probe** merely by setting `subject.root_path`. For promotion, default to copying the selected probe into its own repository before Bind so repository-root `npm ci`, `npm test`, and `npm run build` operate on exactly that prototype. A custom repository-root wrapper could target a subdirectory, but that is repository policy, not subject-aware game-exp behavior.

## Human gates

Machine checks can make a probe `READY_FOR_PLAYTEST`; they do not authorize game-exp Review PASS, PROMISING, SELECTED, or REJECTED. Return evidence to the human/game-exp control plane.
