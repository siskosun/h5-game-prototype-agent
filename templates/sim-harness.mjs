// Generic deterministic simulation harness template.
// Copy to <workspace>/tests/sim-harness.mjs and adapt ONLY loadCore(),
// chooseAction(), and project-specific invariants. Drive the same production
// core logic; do not reimplement gameplay rules here.

import fs from "node:fs";
import path from "node:path";

const RUNS = Number(process.env.SIM_RUNS || 1000);
const MAX_STEPS = Number(process.env.SIM_MAX_STEPS || 10000);
const OUT = process.env.SIM_REPORT || "logs/sim_report.json";

async function loadCore(seed) {
  // Preferred: import a pure production core module and return an adapter:
  // const { createGame } = await import("../game/src/core/game.js");
  // const game = createGame({ seed });
  // return { getState: game.getState, dispatch: game.dispatch, isTerminal: game.isTerminal };
  throw new Error("Adapt loadCore(seed) to the production core before running the harness");
}

function chooseAction(api, step) {
  // Replace with a deterministic policy that selects only legal production actions.
  // It may inspect api.getState(), but must not duplicate effect formulas.
  void api;
  void step;
  throw new Error("Adapt chooseAction(api, step)");
}

function checkInvariants(state) {
  // Add genre-specific assertions. Return an array of failure messages.
  void state;
  return [];
}

const report = {
  runs: 0,
  steps: 0,
  runtimeErrors: 0,
  invariantFailures: 0,
  softlocks: 0,
  failingSeeds: [],
  firstFailure: null,
};

for (let seed = 1; seed <= RUNS; seed += 1) {
  let api;
  const trace = [];
  try {
    api = await loadCore(seed);
    let terminal = false;
    for (let step = 0; step < MAX_STEPS; step += 1) {
      const before = api.getState();
      const failures = checkInvariants(before);
      if (failures.length) {
        report.invariantFailures += failures.length;
        throw new Error(`Invariant failure: ${failures.join("; ")}`);
      }
      if (api.isTerminal?.()) {
        terminal = true;
        break;
      }
      const action = chooseAction(api, step);
      trace.push(action);
      api.dispatch(action);
      report.steps += 1;
    }
    if (!terminal && !api.isTerminal?.()) {
      report.softlocks += 1;
      throw new Error(`No terminal/progress result within ${MAX_STEPS} steps`);
    }
    report.runs += 1;
  } catch (error) {
    report.runtimeErrors += 1;
    report.failingSeeds.push(seed);
    if (!report.firstFailure) {
      report.firstFailure = {
        seed,
        message: String(error?.stack || error),
        trace,
        state: api?.getState?.() ?? null,
      };
    }
    break;
  }
}

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
process.exitCode = report.runtimeErrors || report.invariantFailures || report.softlocks ? 1 : 0;
