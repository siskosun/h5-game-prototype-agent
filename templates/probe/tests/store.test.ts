import assert from "node:assert/strict";
import test from "node:test";
import { createInitialState, reducer, DODGE_WINDOWS_MS, WINDOW_TOLERANCE_MS } from "../src/state/store";

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

test("dodge window endpoints are valid, adjacent milliseconds are not", () => {
  const begin = () => reducer(createInitialState(1), { type: "START" });
  const target = DODGE_WINDOWS_MS[0];
  const lower = target - WINDOW_TOLERANCE_MS;
  const upper = target + WINDOW_TOLERANCE_MS;
  const at = (ms: number) => reducer(begin(), { type: "__TICK", ms });
  assert.equal(reducer(at(lower), { type: "DODGE" }).dodges, 1);
  assert.equal(reducer(at(upper), { type: "DODGE" }).dodges, 1);
  const tooEarly = reducer(at(lower - 1), { type: "DODGE" });
  assert.equal(tooEarly.dodges, 0);
  assert.equal(tooEarly.strikes, 1);
  assert.equal(at(upper + 1).result, "lose");
});
