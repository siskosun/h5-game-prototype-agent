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
  | { type: "TAP" }
  | { type: "RESTART" }
  | { type: "__TICK"; ms: number }
  | { type: "__RESET" };

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
      if (score >= 10) return { ...state, score, mode: "RESULT", result: "win", visibleActions: ["RESTART"] };
      return { ...state, score };
    }
    case "__TICK": {
      if (state.mode !== "PLAY") return state;
      const timeMs = state.timeMs + Math.max(0, action.ms);
      if (timeMs >= 30000) return { ...state, timeMs, mode: "RESULT", result: "lose", visibleActions: ["RESTART"] };
      return { ...state, timeMs };
    }
    case "RESTART":
    case "__RESET":
      return { ...initialState };
    default:
      return state;
  }
}
