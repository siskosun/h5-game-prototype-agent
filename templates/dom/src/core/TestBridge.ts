// Mandatory deterministic test bridge (Prototype Contract §13).
// render_game_to_text reports the CURRENT playable state, not history.
// advanceTime steps the simulation deterministically for tests.
// __GAME_API__ gives tests a stable programmatic input path.

import type { GameState, Action } from "../state/store";

export interface GameApi {
  dispatch: (action: unknown) => unknown;
  getState: () => GameState;
  reset: () => void;
}

export function installTestBridge(
  getState: () => GameState,
  dispatch: (action: Action) => void
): void {
  const w = window as unknown as {
    render_game_to_text?: () => string;
    advanceTime?: (ms: number) => void;
    __GAME_API__?: GameApi;
  };
  w.render_game_to_text = () => JSON.stringify(getState());
  w.advanceTime = (ms: number) => dispatch({ type: "__TICK", ms });
  w.__GAME_API__ = {
    dispatch: (action: unknown) => dispatch(action as Action),
    getState: () => getState(),
    reset: () => dispatch({ type: "__RESET" })
  };
}
