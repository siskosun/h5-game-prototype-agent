// One authoritative state store. All game logic lives here as a pure
// reducer, independent of DOM/rendering, so tests can drive it directly
// with node/tsx. Replace the demo mechanics with the prototype's own.
//
// The store exposes `dispatch(action)` and `advanceTime(ms)`; the test
// bridge in core/TestBridge.ts maps them onto window.*.

export type Mode = "TITLE" | "PLAY" | "RESULT";

export interface GameState {
  mode: Mode;
  score: number;
  timeMs: number;
  result: "win" | "lose" | null;
  visibleActions: string[];
}

export type Action =
  | { type: "START" }
  | { type: "TAP" } // demo primary action; replace with contract actions
  | { type: "RESTART" }
  | { type: "__TICK"; ms: number }
  | { type: "__RESET" };

/** Demo rules: reach 10 taps within 30 seconds. Replace per contract. */
export const WIN_SCORE = 10;
export const TIME_LIMIT_MS = 30000;

export const initialState: GameState = {
  mode: "TITLE",
  score: 0,
  timeMs: 0,
  result: null,
  visibleActions: ["START"]
};

export function reducer(state: GameState, action: Action): GameState {
  switch (action.type) {
    case "START":
      return { ...initialState, mode: "PLAY", visibleActions: ["TAP"] };
    case "TAP": {
      if (state.mode !== "PLAY") return state;
      const score = state.score + 1;
      if (score >= WIN_SCORE) {
        return { ...state, score, result: "win", mode: "RESULT", visibleActions: ["RESTART"] };
      }
      return { ...state, score };
    }
    case "RESTART":
      return { ...initialState };
    case "__TICK": {
      if (state.mode !== "PLAY") return state;
      const timeMs = state.timeMs + Math.max(0, action.ms);
      if (timeMs >= TIME_LIMIT_MS) {
        return { ...state, timeMs, result: "lose", mode: "RESULT", visibleActions: ["RESTART"] };
      }
      return { ...state, timeMs };
    }
    case "__RESET":
      return { ...initialState };
    default:
      return state;
  }
}
