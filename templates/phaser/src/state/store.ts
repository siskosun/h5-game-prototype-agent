import { nextRandom, normalizeSeed } from "../core/rng";

export type Mode = "TITLE" | "PLAY" | "RESULT";
export interface GameState {
  mode: Mode;
  score: number;
  timeMs: number;
  result: "win" | "lose" | null;
  visibleActions: string[];
  seed: number;
  rngState: number;
  lastRandom: number | null;
}
export type Action =
  | { type: "START" }
  | { type: "TAP" }
  | { type: "ROLL" }
  | { type: "RESTART" }
  | { type: "__TICK"; ms: number }
  | { type: "__RESET"; seed?: number };

export const WIN_SCORE = 10;
export const TIME_LIMIT_MS = 30000;

export function createInitialState(seed = 1): GameState {
  const normalized = normalizeSeed(seed);
  return {
    mode: "TITLE",
    score: 0,
    timeMs: 0,
    result: null,
    visibleActions: ["START"],
    seed: normalized,
    rngState: normalized,
    lastRandom: null
  };
}
export const initialState = createInitialState();

export function reducer(state: GameState, action: Action): GameState {
  switch (action.type) {
    case "START":
      return { ...createInitialState(state.seed), mode: "PLAY", visibleActions: ["TAP"] };
    case "TAP": {
      if (state.mode !== "PLAY") return state;
      const score = state.score + 1;
      if (score >= WIN_SCORE) return { ...state, score, mode: "RESULT", result: "win", visibleActions: ["RESTART"] };
      return { ...state, score };
    }
    case "ROLL": {
      const [value, nextState] = nextRandom(state);
      return { ...nextState, lastRandom: value };
    }
    case "__TICK": {
      if (state.mode !== "PLAY") return state;
      const timeMs = state.timeMs + Math.max(0, action.ms);
      if (timeMs >= TIME_LIMIT_MS) return { ...state, timeMs, mode: "RESULT", result: "lose", visibleActions: ["RESTART"] };
      return { ...state, timeMs };
    }
    case "RESTART":
      return createInitialState(state.seed);
    case "__RESET":
      return createInitialState(action.seed ?? state.seed);
    default:
      return state;
  }
}
