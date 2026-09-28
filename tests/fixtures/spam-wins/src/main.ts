import "./style.css";
import { getClockMode, setClockMode } from "./core/clock";
import { installTestBridge } from "./core/TestBridge";
import { clearInputLog, getInputLog, recordInput, type InputSource } from "./qa/inputLog";
import { scenarioState } from "./qa/scenarios";
import { createInitialState, reducer, type Action, type GameState } from "./state/store";
import { renderScreen } from "./views/screens";

let state: GameState = createInitialState();

function dispatch(action: Action, source: InputSource = "PLAYER"): void {
  recordInput(action, source, state.timeMs);
  state = reducer(state, action);
  render();
}

function render(): void {
  renderScreen(state, (action) => dispatch(action, "PLAYER"));
}

let last = performance.now();
function frame(now: number): void {
  const dt = Math.min(now - last, 100);
  last = now;
  if (getClockMode() === "realtime" && state.mode === "PLAY") {
    dispatch({ type: "__TICK", ms: dt }, "PLAYER");
  }
  requestAnimationFrame(frame);
}

const qaEnabled = import.meta.env.DEV || import.meta.env.VITE_QA === "1";
if (qaEnabled) {
  setClockMode("manual");
  installTestBridge({
    getState: () => state,
    dispatchInjected: (action) => dispatch(action, "INJECTED"),
    reset: (seed) => {
      clearInputLog();
      state = createInitialState(seed ?? state.seed);
      render();
    },
    setScenario: (name) => {
      const next = scenarioState(name, state.seed);
      if (!next) return false;
      clearInputLog();
      state = next;
      render();
      return true;
    },
    setClockMode,
    getInputLog
  });
}

render();
requestAnimationFrame(frame);
