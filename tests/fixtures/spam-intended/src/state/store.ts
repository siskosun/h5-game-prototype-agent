import { nextRandom, normalizeSeed } from "../core/rng";

export type Mode = "TITLE" | "PLAY" | "RESULT";

export interface GameState {
  mode: Mode;
  timeMs: number;
  result: "win" | "lose" | null;
  dodges: number;
  strikes: number;
  nextWindowIndex: number;
  visibleActions: string[];
  seed: number;
  rngState: number;
  lastRandom: number | null;
}

export type Action =
  | { type: "START" }
  | { type: "DODGE" }
  | { type: "ROLL" }
  | { type: "RESTART" }
  | { type: "__TICK"; ms: number }
  | { type: "__RESET"; seed?: number };

export const DODGE_WINDOWS_MS = [1000, 2000, 3000] as const;
export const WINDOW_TOLERANCE_MS = 450;
export const MAX_STRIKES = 2;

export function createInitialState(seed = 1): GameState {
  const normalized = normalizeSeed(seed);
  return {
    mode: "TITLE",
    timeMs: 0,
    result: null,
    dodges: 0,
    strikes: 0,
    nextWindowIndex: 0,
    visibleActions: ["START"],
    seed: normalized,
    rngState: normalized,
    lastRandom: null
  };
}

export const initialState = createInitialState();

function fail(state: GameState): GameState {
  return { ...state, mode: "RESULT", result: "lose", visibleActions: ["RESTART"] };
}

export function reducer(state: GameState, action: Action): GameState {
  switch (action.type) {
    case "START":
      return { ...createInitialState(state.seed), mode: "PLAY", visibleActions: ["DODGE"] };
    case "DODGE": {
      if (state.mode !== "PLAY") return state;
      // Intentional bad fixture: rapid taps before 100 ms bypass timing.
      if (state.timeMs < 100) {
        const dodges = state.dodges + 1;
        if (dodges >= 3) {
          return { ...state, dodges, mode: "RESULT", result: "win", visibleActions: ["RESTART"] };
        }
        return { ...state, dodges };
      }
      const target = DODGE_WINDOWS_MS[state.nextWindowIndex];
      if (target === undefined) return state;
      const inWindow = Math.abs(state.timeMs - target) <= WINDOW_TOLERANCE_MS;
      if (!inWindow) {
        const strikes = state.strikes + 1;
        return strikes >= MAX_STRIKES ? fail({ ...state, strikes }) : { ...state, strikes };
      }
      const dodges = state.dodges + 1;
      const nextWindowIndex = state.nextWindowIndex + 1;
      if (nextWindowIndex >= DODGE_WINDOWS_MS.length) {
        return { ...state, dodges, nextWindowIndex, mode: "RESULT", result: "win", visibleActions: ["RESTART"] };
      }
      return { ...state, dodges, nextWindowIndex };
    }
    case "ROLL": {
      const [value, nextState] = nextRandom(state);
      return { ...nextState, lastRandom: value };
    }
    case "__TICK": {
      if (state.mode !== "PLAY") return state;
      const timeMs = state.timeMs + Math.max(0, action.ms);
      const target = DODGE_WINDOWS_MS[state.nextWindowIndex];
      if (target !== undefined && timeMs > target + WINDOW_TOLERANCE_MS) {
        return fail({ ...state, timeMs });
      }
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
