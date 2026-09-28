import type { Action, GameState, Mode } from "../state/store";
import { DODGE_WINDOWS_MS } from "../state/store";

const app = document.getElementById("app") as HTMLElement;
let renderedMode: Mode | null = null;
let statusEl: HTMLParagraphElement | null = null;

function button(text: string, qa: string, onClick: () => void): HTMLButtonElement {
  const el = document.createElement("button");
  el.textContent = text;
  el.className = "btn";
  el.dataset.qa = qa;
  el.addEventListener("click", onClick);
  return el;
}

function heading(text: string): HTMLElement {
  const el = document.createElement("h1");
  el.textContent = text;
  return el;
}

function rebuild(state: GameState, dispatch: (a: Action) => void): void {
  app.replaceChildren();
  renderedMode = state.mode;
  statusEl = null;
  const root = document.createElement("div");
  root.className = "screen";
  root.dataset.qa = "screen";
  if (state.mode === "TITLE") {
    root.append(heading("节奏躲避 · 灰盒探针"));
    const info = document.createElement("p");
    info.textContent = "在三个时机点按一次。过早、过晚或乱按会失败。";
    root.append(info, button("开始", "start", () => dispatch({ type: "START" })));
  } else if (state.mode === "PLAY") {
    statusEl = document.createElement("p");
    statusEl.dataset.qa = "status";
    const action = button("躲避", "action", () => dispatch({ type: "DODGE" }));
    action.style.cssText = "width:100%;height:220px;font-size:32px;touch-action:none;";
    root.append(statusEl, action);
  } else {
    root.append(heading(state.result === "win" ? "通过" : "失败"));
    root.append(button("重试", "restart", () => dispatch({ type: "RESTART" })));
  }
  app.append(root);
}

export function renderScreen(state: GameState, dispatch: (a: Action) => void): void {
  if (state.mode !== renderedMode) rebuild(state, dispatch);
  if (state.mode === "PLAY" && statusEl) {
    const next = DODGE_WINDOWS_MS[state.nextWindowIndex] ?? state.timeMs;
    statusEl.textContent = `时间 ${Math.round(state.timeMs)}ms · 成功 ${state.dodges}/3 · 失误 ${state.strikes}/2 · 下一拍 ${next}ms`;
  }
}
