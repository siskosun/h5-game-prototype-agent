import Phaser from "phaser";
import { GameScene } from "../scenes/GameScene";

export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: "game",
  width: 390,
  height: 844,
  backgroundColor: "#10131f",
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    width: 390,
    height: 844
  },
  scene: [GameScene]
};
