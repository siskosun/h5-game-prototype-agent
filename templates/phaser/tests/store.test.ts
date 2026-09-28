import assert from "node:assert/strict";
import test from "node:test";
import { createInitialState, reducer } from "../src/state/store";
import { getClockMode, setClockMode } from "../src/core/clock";

test("same seed and actions produce the same state", () => {
  const run = () => {
    let state = createInitialState(9876);
    for (const action of [
      { type: "ROLL" as const },
      { type: "START" as const },
      { type: "ROLL" as const },
      { type: "TAP" as const },
      { type: "__TICK" as const, ms: 300 }
    ]) state = reducer(state, action);
    return state;
  };
  assert.deepEqual(run(), run());
});

test("manual clock is explicit", () => {
  setClockMode("manual");
  assert.equal(getClockMode(), "manual");
  setClockMode("realtime");
});
