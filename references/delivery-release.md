# Delivery target and release evidence

## DeliveryTarget

When a runnable deliverable is required and the user has not chosen, ask once for exactly one target:

### LOCALHOST_URL
Serve the project locally and provide an exact `http://127.0.0.1:<port>/...` URL plus start command and server root. The release artifact for hashing is the frozen server-root directory snapshot.

### ZIP_BUNDLE
Deliver a ZIP containing the promised project/build layout. Record the root entrypoint and exact start/open instructions. If the ZIP requires a local server or install/build step, say so explicitly.

### SINGLE_HTML
Deliver one self-contained runnable HTML file. Do not introduce this shape unless the user chose it or already requested it.

Do not silently default between these targets.

If the user explicitly requests online deployment, handle it as a project-specific extension rather than silently adding a deployment service to this default local-delivery contract.

## Release freeze

Before final release evidence:

1. freeze the final file/ZIP/server directory;
2. calculate SHA-256 (deterministic tree hash for LOCALHOST_URL directory);
3. run the promised smoke/playthrough against that exact result;
4. record the same `artifactSha256` in `browser_report.json`;
5. ensure blocking console/page/network/input errors are empty;
6. ensure the intended loop completed;
7. deliver without post-QA edits.

Any byte/content change after evidence capture invalidates previous release evidence.

## Evidence shape

A minimal browser report may contain:

```json
{
  "artifactSha256": "...",
  "completedLoop": true,
  "testedUrl": "http://127.0.0.1:8000/",
  "consoleErrors": [],
  "pageErrors": [],
  "networkFailures": [],
  "blockedInputs": []
}
```

`testedUrl` is required for LOCALHOST_URL and should use 127.0.0.1.

Use `templates/delivery_contract.md`, `scripts/validate_delivery.py`, and `scripts/validate_release_artifact.py`.
