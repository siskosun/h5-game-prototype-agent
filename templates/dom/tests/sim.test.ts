import assert from "node:assert/strict";
import test from "node:test";
import { createInitialState, reducer, type Action } from "../src/state/store";

function chooseAction(state: ReturnType<typeof createInitialState>): Action {
  if (state.mode === "TITLE") return { type: "START" };
  if (state.mode === "PLAY") return { type: "TAP" };
  return { type: "RESTART" };
}

test("headless demo simulation reports no runtime or invariant failures", () => {
  const report = {
    runs: 20,
    runtimeErrors: 0,
    invariantFailures: 0,
    softlocks: 0,
    failingSeeds: [] as number[],
    firstFailure: null as null | { seed: number; reason: string }
  };
  for (let seed = 1; seed <= report.runs; seed += 1) {
    try {
      let state = createInitialState(seed);
      for (let step = 0; step < 20 && state.result === null; step += 1) {
        state = reducer(state, chooseAction(state));
        if (state.score < 0 || state.timeMs < 0) throw new Error("negative state");
      }
      if (state.result !== "win") {
        report.softlocks += 1;
        report.failingSeeds.push(seed);
        report.firstFailure ??= { seed, reason: "did not reach win" };
      }
    } catch (error) {
      report.runtimeErrors += 1;
      report.failingSeeds.push(seed);
      report.firstFailure ??= { seed, reason: String(error) };
    }
  }
  assert.equal(report.runtimeErrors, 0);
  assert.equal(report.invariantFailures, 0);
  assert.equal(report.softlocks, 0);
});
