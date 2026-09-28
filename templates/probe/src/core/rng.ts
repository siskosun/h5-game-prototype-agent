import type { GameState } from "../state/store";

export function normalizeSeed(seed: number): number {
  const value = Number.isFinite(seed) ? Math.trunc(seed) >>> 0 : 1;
  return value === 0 ? 1 : value;
}

export function nextRandom(state: GameState): [number, GameState] {
  const nextState = (state.rngState + 0x6d2b79f5) >>> 0;
  let t = nextState;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  const value = ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  return [value, { ...state, rngState: nextState }];
}
