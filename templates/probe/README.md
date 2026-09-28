# H5 Mechanic Probe template

A graybox probe scaffold for one repeatable mechanic loop.

Workflow:

1. Edit `probe_card.md`.
2. Run `python <skill-root>/scripts/probe_card.py validate probe_card.md`.
3. Freeze it with `python <skill-root>/scripts/probe_card.py freeze probe_card.md`.
4. Run `npm ci`, `npm test`, and `npm run probe:check`.
5. Inspect `.probe/report.json`, screenshots, and video.
6. Do not set `human_verdict` without an actual human playtest record.

The QA bridge exists only in Vite dev mode or `build:qa`. A normal `npm run build` removes it.
