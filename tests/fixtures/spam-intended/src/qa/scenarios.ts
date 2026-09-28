import { createInitialState, DODGE_WINDOWS_MS, type GameState } from "../state/store";

export function scenarioState(name: string, seed = 1): GameState | null {
  const base = createInitialState(seed);
  if (name === "title") return base;
  if (name === "play-start") return { ...base, mode: "PLAY", visibleActions: ["DODGE"] };
  if (name === "play-near-win") {
    return {
      ...base,
      mode: "PLAY",
      timeMs: DODGE_WINDOWS_MS[2],
      dodges: 2,
      nextWindowIndex: 2,
      visibleActions: ["DODGE"]
    };
  }
  if (name === "play-near-timeout") {
    return { ...base, mode: "PLAY", timeMs: 500, visibleActions: ["DODGE"] };
  }
  if (name === "result-lose") {
    return { ...base, mode: "RESULT", result: "lose", visibleActions: ["RESTART"] };
  }
  return null;
}
