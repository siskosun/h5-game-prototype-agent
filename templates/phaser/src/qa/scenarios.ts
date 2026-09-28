import { createInitialState, TIME_LIMIT_MS, WIN_SCORE, type GameState } from "../state/store";

export function scenarioState(name: string, seed = 1): GameState | null {
  const base = createInitialState(seed);
  if (name === "title") return base;
  if (name === "play-start") return { ...base, mode: "PLAY", visibleActions: ["TAP"] };
  if (name === "play-near-win") return { ...base, mode: "PLAY", score: WIN_SCORE - 1, visibleActions: ["TAP"] };
  if (name === "play-near-timeout") return { ...base, mode: "PLAY", timeMs: TIME_LIMIT_MS - 500, visibleActions: ["TAP"] };
  if (name === "result-lose") return { ...base, mode: "RESULT", result: "lose", visibleActions: ["RESTART"] };
  return null;
}
