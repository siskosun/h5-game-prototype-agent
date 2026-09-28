export type ClockMode = "realtime" | "manual";

let clockMode: ClockMode = "realtime";

export function getClockMode(): ClockMode {
  return clockMode;
}

export function setClockMode(mode: ClockMode): void {
  clockMode = mode;
}
