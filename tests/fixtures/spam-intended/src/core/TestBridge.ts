import type { ClockMode } from "./clock";
import type { Action, GameState } from "../state/store";
import type { InputLogEntry } from "../qa/inputLog";

export interface GameApi {
  version: "1";
  dispatch: (action: unknown) => void;
  getState: () => GameState;
  reset: (seed?: number) => void;
  setSeed: (seed: number) => void;
  setScenario: (name: string) => boolean;
  setClockMode: (mode: ClockMode) => void;
  getInputLog: () => InputLogEntry[];
}

export interface BridgeHooks {
  getState: () => GameState;
  dispatchInjected: (action: Action) => void;
  reset: (seed?: number) => void;
  setScenario: (name: string) => boolean;
  setClockMode: (mode: ClockMode) => void;
  getInputLog: () => InputLogEntry[];
}

export function installTestBridge(hooks: BridgeHooks): void {
  const w = window as unknown as {
    render_game_to_text?: () => string;
    advanceTime?: (ms: number) => void;
    __GAME_API__?: GameApi;
  };
  w.render_game_to_text = () => JSON.stringify(hooks.getState());
  w.advanceTime = (ms: number) => hooks.dispatchInjected({ type: "__TICK", ms });
  w.__GAME_API__ = {
    version: "1",
    dispatch: (action: unknown) => hooks.dispatchInjected(action as Action),
    getState: hooks.getState,
    reset: hooks.reset,
    setSeed: (seed: number) => hooks.reset(seed),
    setScenario: hooks.setScenario,
    setClockMode: hooks.setClockMode,
    getInputLog: hooks.getInputLog
  };
}
