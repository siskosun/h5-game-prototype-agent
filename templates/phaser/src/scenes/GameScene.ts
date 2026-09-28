import Phaser from "phaser";
import { getClockMode, setClockMode } from "../core/clock";
import { installTestBridge } from "../core/TestBridge";
import { clearInputLog, getInputLog, recordInput, type InputSource } from "../qa/inputLog";
import { scenarioState } from "../qa/scenarios";
import { createInitialState, reducer, TIME_LIMIT_MS, WIN_SCORE, type Action, type GameState } from "../state/store";

export class GameScene extends Phaser.Scene {
  private state: GameState = createInitialState();
  private text!: Phaser.GameObjects.Text;

  constructor() {
    super("game");
  }

  create(): void {
    this.text = this.add.text(195, 360, "H5 Game Prototype\n点击开始", {
      fontFamily: "sans-serif",
      fontSize: "28px",
      color: "#ffffff",
      align: "center"
    }).setOrigin(0.5);

    this.input.on("pointerdown", () => {
      if (this.state.mode === "TITLE") this.dispatch({ type: "START" }, "PLAYER");
      else if (this.state.mode === "PLAY") this.dispatch({ type: "TAP" }, "PLAYER");
      else this.dispatch({ type: "RESTART" }, "PLAYER");
    });

    const qaEnabled = import.meta.env.DEV || import.meta.env.VITE_QA === "1";
    if (qaEnabled) {
      setClockMode("manual");
      installTestBridge({
        getState: () => this.state,
        dispatchInjected: (action) => this.dispatch(action, "INJECTED"),
        reset: (seed) => {
          clearInputLog();
          this.state = createInitialState(seed ?? this.state.seed);
          this.renderState();
        },
        setScenario: (name) => {
          const next = scenarioState(name, this.state.seed);
          if (!next) return false;
          clearInputLog();
          this.state = next;
          this.renderState();
          return true;
        },
        setClockMode,
        getInputLog
      });
    }
    this.renderState();
  }

  update(_time: number, delta: number): void {
    if (getClockMode() === "realtime" && this.state.mode === "PLAY") {
      this.dispatch({ type: "__TICK", ms: Math.min(delta, 100) }, "PLAYER", false);
    }
  }

  private dispatch(action: Action, source: InputSource, render = true): void {
    recordInput(action, source, this.state.timeMs);
    this.state = reducer(this.state, action);
    if (render) this.renderState();
  }

  private renderState(): void {
    const s = this.state;
    if (s.mode === "TITLE") this.text.setText("H5 Game Prototype\n点击开始");
    else if (s.mode === "PLAY") {
      this.text.setText(`得分 ${s.score}/${WIN_SCORE}\n剩余 ${Math.max(0, Math.ceil((TIME_LIMIT_MS - s.timeMs) / 1000))}s\n点击屏幕`);
    } else {
      this.text.setText(`${s.result === "win" ? "胜利" : "失败"}\n点击重新开始`);
    }
  }
}
