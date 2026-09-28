import assert from "node:assert/strict";
import test from "node:test";
import { createInitialState, reducer } from "../src/state/store";

test("same seed and actions are reproducible", () => {
  const run = () => {
    let s = reducer(createInitialState(42), { type: "START" });
    s = reducer(s, { type: "ROLL" });
    s = reducer(s, { type: "__TICK", ms: 1000 });
    s = reducer(s, { type: "DODGE" });
    s = reducer(s, { type: "ROLL" });
    return s;
  };
  assert.deepEqual(run(), run());
});

test("three timed dodges win", () => {
  let s = reducer(createInitialState(1), { type: "START" });
  for (const delta of [1000, 1000, 1000]) {
    s = reducer(s, { type: "__TICK", ms: delta });
    s = reducer(s, { type: "DODGE" });
  }
  assert.equal(s.result, "win");
});

test("immediate spam loses", () => {
  let s = reducer(createInitialState(1), { type: "START" });
  s = reducer(s, { type: "DODGE" });
  s = reducer(s, { type: "DODGE" });
  assert.equal(s.result, "lose");
});

test("idle past a window loses", () => {
  let s = reducer(createInitialState(1), { type: "START" });
  s = reducer(s, { type: "__TICK", ms: 1600 });
  assert.equal(s.result, "lose");
});
