# Player-facing browser, mobile, visual, and asset QA

## Real-browser rule

Use a real browser for claims about controls, layout, rendering, asset loading, storage behavior, audio unlock, focus/click/touch behavior, or final playability.

Capture relevant console errors, page errors, failed network requests, screenshots, critical bounding boxes, final state, and action/path coverage.

Logic-only tests cannot replace browser evidence for player-facing claims.

## Mobile-first checks

For new mobile-first projects, default to 390x844 and 360x800 minimum unless the project defines other targets. Preserve existing targets in established projects.

Verify:

- no unintended horizontal overflow;
- primary repeated touch gesture is practical;
- swipe/touch does not conflict with page scroll/zoom;
- one discrete gesture does not emit unintended multiple actions;
- primary controls meet reasonable touch size (44 CSS px baseline where applicable);
- safe-area behavior is acceptable;
- player/avatar, objective/goal, exit/next step, and primary controls remain visible in materially different layout classes.

Always include the largest/densest layout and final composite scenario when they differ materially from simpler screens.

## Semantic visual legibility

Mechanically distinct roles must remain recognizable at the minimum actual gameplay size without relying on color alone. Prefer at least two non-color identity cues such as silhouette, equipment, pose, symbol, direction, or action intent.

Do not treat different SVG source code or different colors as proof of human legibility. Inspect screenshots at runtime size.

## Runtime assets

Prove important assets through:

`source file -> manifest -> runtime path -> loader -> runtime node -> rendered screenshot`

File existence is not integration. For transparent generated/processed images, inspect visible alpha/content when alignment or emptiness is a risk. Use `scripts/analyze_asset_bounds.py` when useful.

Use `templates/visual_canon.json` and `templates/asset_manifest.json` when multiple assets/identities need tracking.

## Audio and motion

When present, verify first-interaction audio unlock, BGM/SFX toggles, no autoplay exception, reduced-motion behavior, and that decorative motion/VFX do not block critical controls or state.

## Subjective feel

Separate technical correctness from taste. For control feel, pacing, feedback intensity, camera, and similar subjective issues, expose a playable preview when possible and ask focused questions. Mark human feel as unverified when no human playtest occurred.

When using structured evidence files, run `scripts/validate_asset_manifest.py` for asset manifests and `scripts/validate_responsive_layout.py` for mobile layout reports. These validators support evidence collection; they do not replace screenshot inspection.
