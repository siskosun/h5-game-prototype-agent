// Demo screen renderers. Each screen renders into #app from the current
// state and wires user input to dispatch. Replace with contract screens;
// keep the same shape (mode switch + buttons) so the test bridge contract
// stays intact.

import type { GameState, Action } from "../state/store";
import { TIME_LIMIT_MS, WIN_SCORE } from "../state/store";

const app = document.getElementById("app") as HTMLElement;

function button(text: string, onClick: () => void): HTMLButtonElement {
  const el = document.createElement("button");
  el.textContent = text;
  el.className = "btn";
  el.addEventListener("click", onClick);
  return el;
}

function heading(text: string): HTMLElement {
  const el = document.createElement("h1");
  el.textContent = text;
  return el;
}

export function renderScreen(state: GameState, dispatch: (a: Action) => void): void {
  app.replaceChildren();
  const root = document.createElement("div");
  root.className = "screen";
  // 竖版手机布局由 src/style.css 提供（#app max-width:430px 手机容器，桌面居中）

  if (state.mode === "TITLE") {
    root.append(heading("H5 Game Prototype"));
    root.append(button("开始游戏", () => dispatch({ type: "START" })));
  } else if (state.mode === "PLAY") {
    const score = document.createElement("p");
    score.textContent = `得分 ${state.score} / ${WIN_SCORE} · 剩余 ${Math.max(0, Math.ceil((TIME_LIMIT_MS - state.timeMs) / 1000))}s`;
    const zone = button(`点击（当前 ${state.score}）`, () => dispatch({ type: "TAP" }));
    zone.style.cssText = "width:100%;height:200px;font-size:20px;touch-action:none;";
    root.append(score, zone);
  } else {
    root.append(heading(state.result === "win" ? "胜利！" : "失败…"));
    root.append(button("再来一局", () => dispatch({ type: "RESTART" })));
  }

  app.append(root);
}
