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

## Iteration delivery

After each completed H5 implementation pass, return one `iteration_delivery` object for game-exp:

```json
{
  "changes": ["player-visible change"],
  "playable": {
    "kind": "SHAREABLE_URL | LOCAL_URL | ARTIFACT_ONLY | MISSING",
    "verified": true,
    "url": "https://... or http://127.0.0.1:...",
    "artifact_url": "https://...",
    "launch_hint": "optional short instruction"
  },
  "focus_points": ["1-3 things the human should feel/check"],
  "producer": "h5-game-prototype-agent",
  "build_id": "optional build identity",
  "previous_candidate_id": "optional real prior Candidate id"
}
```

Rules:

- report only URLs or artifacts verified against this exact source/build;
- use `SHAREABLE_URL` only for an intended cross-device URL;
- use `LOCAL_URL` for localhost/LAN or another environment-bound URL;
- use `ARTIFACT_ONLY` when a verified downloadable artifact exists but there is no direct playable URL;
- use `MISSING` with `verified=false` when no verified playable entry exists; never invent a URL;
- include `previous_candidate_id` only when it names a real Candidate from this experiment;
- this object is `participant_reported`; `READY_FOR_PLAYTEST` still does not become human PASS.

When releasing the game-exp Work Claim, place this object under `delivery`. game-exp may project it as `experiment_panel.delivery_card`.

## Public shareable playable

When the game-exp handoff includes `delivery_request.prefer_shareable_url=true`, the repository is public, and the final production build has passed the normal local browser/player checks:

1. keep the production Vite build subpath-safe; the bundled templates use `base: "./"`;
2. use the exact pushed `result_source_sha` as the immutable version key;
3. publish the frozen `dist/` directory with:

```bash
python <skill-root>/scripts/publish_github_pages.py \
  --repo owner/repo \
  --source dist \
  --version-key <result_source_sha> \
  --producer h5-game-prototype-agent \
  --require-relative-entrypoint \
  --json
```

The publisher writes only the dedicated `gh-pages` delivery branch. It never edits the canonical experiment branch, protected Ledger, Candidate refs, or lifecycle state. Each version lives under `play/<result_source_sha>/`; the same version key with different bytes is rejected rather than overwritten. The repository root redirects to the latest published version.

The publisher verifies that GitHub Pages serves the expected immutable marker and index, but that is deployment evidence only. Open the returned HTTPS URL in a real browser and rerun the normal player-input smoke before returning `playable.kind=SHAREABLE_URL` with `verified=true`.

If Pages is unavailable, the repository is private, Pages already uses a different source, permission is insufficient, or deployed gameplay/browser verification fails, do not reconfigure unrelated hosting automatically. Fall back honestly to `LOCAL_URL`, `ARTIFACT_ONLY`, or `MISSING` according to what was actually verified.

## Repository layout

Verified against the current `siskosun/game-exp` `main` implementation on 2026-09-28: Candidate install/test/build commands run with repository-root `cwd=.`. Project-policy step objects contain only `argv`; `subject.root_path` is not used as a build working directory.

Therefore a repository containing several nested probes is **not automatically buildable per probe** merely by setting `subject.root_path`. For promotion, default to copying the selected probe into its own repository before Bind so repository-root `npm ci`, `npm test`, and `npm run build` operate on exactly that prototype. A custom repository-root wrapper could target a subdirectory, but that is repository policy, not subject-aware game-exp behavior.

## Human gates

Machine checks can make a probe `READY_FOR_PLAYTEST`; they do not authorize game-exp Review PASS, PROMISING, SELECTED, or REJECTED. Return evidence to the human/game-exp control plane.
