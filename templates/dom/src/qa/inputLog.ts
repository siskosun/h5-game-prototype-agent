import type { Action } from "../state/store";

export type InputSource = "PLAYER" | "INJECTED" | "EMULATED_TOUCH";

export interface InputLogEntry {
  seq: number;
  timeMs: number;
  action: string;
  source: InputSource;
}

const entries: InputLogEntry[] = [];

export function recordInput(action: Action, source: InputSource, timeMs: number): void {
  if (action.type.startsWith("__")) return;
  entries.push({ seq: entries.length + 1, timeMs, action: action.type, source });
}

export function getInputLog(): InputLogEntry[] {
  return entries.map((entry) => ({ ...entry }));
}

export function clearInputLog(): void {
  entries.length = 0;
}
