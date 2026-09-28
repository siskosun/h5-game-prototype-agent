import type { Action, GameState, Mode } from "../state/store";
import { TIME_LIMIT_MS, WIN_SCORE } from "../state/store";

const app = document.getElementById("app") as HTMLElement;
let renderedMode: Mode | null = null;
let statusEl: HTMLParagraphElement | null = null;
let actionEl: HTMLButtonElement | null = null;

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
  actionEl = null;
  const root = document.createElement("div");
  root.className = "screen";
  root.dataset.qa = "screen";
  if (state.mode === "TITLE") {
    root.append(heading("H5 Game Prototype"));
    root.append(button("开始游戏", "start", () => dispatch({ type: "START" })));
  } else if (state.mode === "PLAY") {
    statusEl = document.createElement("p");
    statusEl.dataset.qa = "status";
    actionEl = button("", "action", () => dispatch({ type: "TAP" }));
    actionEl.style.cssText = "width:100%;height:200px;font-size:20px;touch-action:none;";
    root.append(statusEl, actionEl);
  } else {
    root.append(heading(state.result === "win" ? "胜利！" : "失败…"));
    root.append(button("再来一局", "restart", () => dispatch({ type: "RESTART" })));
  }
  app.append(root);
}

export function renderScreen(state: GameState, dispatch: (a: Action) => void): void {
  if (state.mode !== renderedMode) rebuild(state, dispatch);
  if (state.mode === "PLAY" && statusEl && actionEl) {
    statusEl.textContent = `得分 ${state.score} / ${WIN_SCORE} · 剩余 ${Math.max(0, Math.ceil((TIME_LIMIT_MS - state.timeMs) / 1000))}s`;
    actionEl.textContent = `点击（当前 ${state.score}）`;
  }
}
