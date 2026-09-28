// DOM/UI-heavy template bootstrap: one state store, a render function that
// redraws the current screen, and a rAF loop that advances simulated time.
// Replace the demo screen renderers with the contract's own views.

import "./style.css";
import { reducer, initialState, type GameState, type Action } from "./state/store";
import { installTestBridge } from "./core/TestBridge";
import { renderScreen } from "./views/screens";

let state: GameState = initialState;

function dispatch(action: Action): void {
  state = reducer(state, action);
  render();
}

function render(): void {
  renderScreen(state, dispatch);
}

// Real-time clock for the browser session; tests use __GAME_API__/advanceTime
// instead, so simulation stays deterministic under test.
let last = performance.now();
function frame(now: number): void {
  const dt = Math.min(now - last, 100);
  last = now;
  if (state.mode === "PLAY") dispatch({ type: "__TICK", ms: dt });
  requestAnimationFrame(frame);
}

installTestBridge(() => state, dispatch);
render();
requestAnimationFrame(frame);
