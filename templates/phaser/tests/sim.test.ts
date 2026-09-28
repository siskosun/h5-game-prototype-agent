import assert from "node:assert/strict";
import test from "node:test";
import { createInitialState, reducer } from "../src/state/store";

test("headless production core reaches the demo win", () => {
  for (let seed = 1; seed <= 20; seed += 1) {
    let state = reducer(createInitialState(seed), { type: "START" });
    for (let i = 0; i < 10; i += 1) state = reducer(state, { type: "TAP" });
    assert.equal(state.result, "win");
  }
});
