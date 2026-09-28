import assert from "node:assert/strict";
import test from "node:test";
import { createInitialState, reducer } from "../src/state/store";
import { getClockMode, setClockMode } from "../src/core/clock";

test("same seed and actions produce the same state", () => {
  const run = () => {
    let state = createInitialState(123456);
    const actions = [
      { type: "ROLL" as const },
      { type: "START" as const },
      { type: "ROLL" as const },
      { type: "TAP" as const },
      { type: "__TICK" as const, ms: 250 },
      { type: "ROLL" as const }
    ];
    for (const action of actions) state = reducer(state, action);
    return state;
  };
  assert.deepEqual(run(), run());
});

test("clock mode can be switched without advancing state", () => {
  setClockMode("manual");
  assert.equal(getClockMode(), "manual");
  setClockMode("realtime");
  assert.equal(getClockMode(), "realtime");
});

test("reset accepts a seed", () => {
  const state = reducer(createInitialState(1), { type: "__RESET", seed: 99 });
  assert.equal(state.seed, 99);
  assert.equal(state.rngState, 99);
});
