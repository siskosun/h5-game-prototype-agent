# Probe Card

Edit the JSON block, validate it, then freeze it before implementation. After freezing, changing the hypothesis or kill criteria requires a new probe id or an explicit revision record.

```json
{
  "probe_id": "fixture-spam-intended",
  "title": "单键节奏躲避灰盒",
  "experience_goal": "玩家能否仅凭三个明确节奏点形成“观察时机而非乱按”的单键决策。",
  "core_mechanic": "在三个节奏窗口内按下躲避；过早、过晚或连续乱按会累积失误并失败。",
  "hypothesis": "如果时机窗口可读且错误点击有代价，玩家会等待节奏点而不是持续连点。",
  "kill_criteria": [
    "连续快速点击无需读取时机就能稳定获胜",
    "完全不输入仍能获胜或进入等价成功状态",
    "正常三次定时输入无法稳定完成一局"
  ],
  "intended_degenerate_strategies": [
    "spam"
  ],
  "target_viewport": {
    "width": 390,
    "height": 844
  },
  "input_mode": "mouse",
  "time_box": "4h",
  "human_observation_points": [
    "第一局是否会先观察节奏再按，而不是立即连点",
    "第一次失败后是否能说出失败与按键时机有关",
    "第二局是否主动调整按键节奏"
  ],
  "frozen_at": "2026-09-28T13:42:15Z",
  "frozen_sha256": "97a3b72d48574d4fe6fecfcbacddecee40465855cc721245d4e0031b99ca290a"
}
```
