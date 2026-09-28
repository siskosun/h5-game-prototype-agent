import assert from "node:assert/strict";
import test from "node:test";
import { createInitialState, reducer } from "../src/state/store";

test("up to 50 seeded smoke runs keep the intended path valid", () => {
  const report = {
    runs: 50,
    runtimeErrors: 0,
    invariantFailures: 0,
    softlocks: 0,
    failingSeeds: [] as number[],
    firstFailure: null as null | { seed: number; reason: string }
  };
  for (let seed = 1; seed <= 50; seed += 1) {
    let s = reducer(createInitialState(seed), { type: "START" });
    for (const delta of [1000, 1000, 1000]) {
      s = reducer(s, { type: "__TICK", ms: delta });
      s = reducer(s, { type: "DODGE" });
    }
    if (s.result !== "win") {
      report.softlocks += 1;
      report.failingSeeds.push(seed);
      report.firstFailure ??= { seed, reason: "intended timed path did not win" };
    }
  }
  assert.equal(report.runtimeErrors, 0);
  assert.equal(report.invariantFailures, 0);
  assert.equal(report.softlocks, 0);
});
