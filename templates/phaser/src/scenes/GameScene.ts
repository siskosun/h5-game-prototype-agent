import Phaser from "phaser";
import { initialState, reducer, type Action, type GameState } from "../state/store";
import { installTestBridge } from "../core/TestBridge";

export class GameScene extends Phaser.Scene {
  private state: GameState = { ...initialState };
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
      if (this.state.mode === "TITLE") this.dispatch({ type: "START" });
      else if (this.state.mode === "PLAY") this.dispatch({ type: "TAP" });
      else this.dispatch({ type: "RESTART" });
    });

    installTestBridge(() => this.state, (action) => this.dispatch(action));
    this.renderState();
  }

  update(_time: number, delta: number): void {
    if (this.state.mode === "PLAY") this.dispatch({ type: "__TICK", ms: Math.min(delta, 100) }, false);
  }

  private dispatch(action: Action, render = true): void {
    this.state = reducer(this.state, action);
    if (render) this.renderState();
  }

  private renderState(): void {
    const s = this.state;
    if (s.mode === "TITLE") this.text.setText("H5 Game Prototype\n点击开始");
    else if (s.mode === "PLAY") this.text.setText(`得分 ${s.score}/10\n剩余 ${Math.max(0, Math.ceil((30000 - s.timeMs) / 1000))}s\n点击屏幕`);
    else this.text.setText(`${s.result === "win" ? "胜利" : "失败"}\n点击重新开始`);
  }
}
