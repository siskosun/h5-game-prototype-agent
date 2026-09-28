import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createReadStream, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, relative, resolve } from "node:path";
import { chromium } from "playwright";
import { runPlayerPath } from "./player-path.mjs";

const ROOT = process.cwd();
const DIST = join(ROOT, "dist");
const PROBE_DIR = join(ROOT, ".probe");
const SHOTS = join(PROBE_DIR, "screenshots");
mkdirSync(SHOTS, { recursive: true });

function parseCard() {
  const text = readFileSync(join(ROOT, "probe_card.md"), "utf8");
  const match = text.match(/```json\s*([\s\S]*?)```/);
  if (!match) throw new Error("probe_card.md must contain one json code block");
  return JSON.parse(match[1]);
}

function hashTree(dir, exclude = new Set()) {
  const hash = createHash("sha256");
  function visit(current) {
    for (const name of readdirSync(current).sort()) {
      const full = join(current, name);
      const rel = relative(dir, full).replaceAll("\\", "/");
      if (exclude.has(name) || [...exclude].some((x) => rel.startsWith(x + "/"))) continue;
      const stat = statSync(full);
      if (stat.isDirectory()) visit(full);
      else {
        hash.update(rel);
        hash.update("\0");
        hash.update(readFileSync(full));
        hash.update("\0");
      }
    }
  }
  visit(dir);
  return hash.digest("hex");
}

function sourceSha() {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).trim();
  } catch {
    return hashTree(ROOT, new Set(["node_modules", "dist", ".probe", ".git"]));
  }
}

function mime(path) {
  const ext = extname(path);
  return ({ ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json" })[ext] || "application/octet-stream";
}

async function startStaticServer() {
  const server = createServer((req, res) => {
    const raw = (req.url || "/").split("?")[0];
    const rel = raw === "/" ? "index.html" : raw.replace(/^\/+/, "");
    const file = resolve(DIST, rel);
    if (!file.startsWith(resolve(DIST)) || !existsSync(file) || statSync(file).isDirectory()) {
      res.writeHead(404); res.end("not found"); return;
    }
    res.writeHead(200, { "Content-Type": mime(file), "Cache-Control": "no-store" });
    createReadStream(file).pipe(res);
  });
  await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
  const address = server.address();
  return { server, url: `http://127.0.0.1:${address.port}/` };
}

const card = parseCard();
const viewport = card.target_viewport || { width: 390, height: 844 };
const inputMode = card.input_mode || "mouse";
const playerSource = inputMode === "touch" ? "EMULATED_TOUCH" : "PLAYER";
const intended = new Set(card.intended_degenerate_strategies || []);
const externalUrlIndex = process.argv.indexOf("--url");
const externalUrl = externalUrlIndex >= 0 ? process.argv[externalUrlIndex + 1] : null;

const hosted = externalUrl ? null : await startStaticServer();
const url = externalUrl || hosted.url;
async function launchBrowser() {
  try {
    return await chromium.launch({ headless: true });
  } catch (firstError) {
    const candidates = [
      process.env.PROGRAMFILES ? join(process.env.PROGRAMFILES, "Microsoft", "Edge", "Application", "msedge.exe") : "",
      process.env["PROGRAMFILES(X86)"] ? join(process.env["PROGRAMFILES(X86)"], "Microsoft", "Edge", "Application", "msedge.exe") : "",
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    ].filter(Boolean);
    for (const executablePath of candidates) {
      if (existsSync(executablePath)) {
        return chromium.launch({ headless: true, executablePath });
      }
    }
    throw firstError;
  }
}

const browser = await launchBrowser();
const browserVersion = browser.version();
const startedAt = Date.now();
const context = await browser.newContext({
  viewport,
  hasTouch: inputMode === "touch",
  isMobile: inputMode === "touch",
  recordVideo: { dir: join(PROBE_DIR, "video"), size: viewport }
});
const page = await context.newPage();
const video = page.video();
const runtimeErrors = [];
page.on("console", (msg) => { if (msg.type() === "error") runtimeErrors.push(`console: ${msg.text()}`); });
page.on("pageerror", (error) => runtimeErrors.push(`page: ${error.message}`));
page.on("requestfailed", (request) => runtimeErrors.push(`network: ${request.url()} ${request.failure()?.errorText || ""}`));

const checks = [];
let harnessFailure = false;

async function state() {
  return page.evaluate(() => JSON.parse(window.render_game_to_text()));
}
async function api(expression, arg) {
  return page.evaluate(({ expression, arg }) => {
    const api = window.__GAME_API__;
    if (!api) throw new Error("__GAME_API__ unavailable");
    if (expression === "scenario") return api.setScenario(arg);
    if (expression === "clock") return api.setClockMode(arg);
    if (expression === "advance") return window.advanceTime(arg);
    if (expression === "inputLog") return api.getInputLog();
    return null;
  }, { expression, arg });
}
async function shot(name) {
  const rel = `.probe/screenshots/${name}.png`;
  await page.screenshot({ path: join(ROOT, rel), fullPage: true });
  return rel;
}
async function addCheck(name, source, fn) {
  try {
    const outcome = await fn();
    checks.push({ name, input_source: source, status: outcome.ok ? "PASS" : "FAIL", evidence: await shot(name), note: outcome.note });
  } catch (error) {
    harnessFailure = true;
    checks.push({ name, input_source: source, status: "INCONCLUSIVE", evidence: await shot(name).catch(() => ""), note: String(error) });
  }
}

await page.goto(url, { waitUntil: "networkidle" });

await addCheck("browser_health", "PLAYER", async () => ({
  ok: runtimeErrors.length === 0,
  note: runtimeErrors.length ? runtimeErrors.join(" | ") : "No console, page, or failed-network errors."
}));

await addCheck("manual_clock", "INJECTED", async () => {
  await api("scenario", "play-start");
  await api("clock", "manual");
  const before = await state();
  await page.waitForTimeout(2000);
  const afterWait = await state();
  await api("advance", 1000);
  const afterAdvance = await state();
  const ok = afterWait.timeMs === before.timeMs && afterAdvance.timeMs === before.timeMs + 1000;
  return { ok, note: `before=${before.timeMs}, afterWait=${afterWait.timeMs}, afterAdvance=${afterAdvance.timeMs}` };
});

await addCheck("player_path", playerSource, async () => {
  await api("scenario", "title");
  await api("clock", "realtime");
  await runPlayerPath(page, inputMode);
  const s = await state();
  const log = await api("inputLog");
  const expectedSource = playerSource === "EMULATED_TOUCH" ? "PLAYER" : "PLAYER";
  const normalInputsArePlayer = log.length > 0 && log.every((entry) => entry.source === expectedSource);
  return { ok: s.result === "win" && normalInputsArePlayer, note: `result=${s.result}; logged=${log.length}; browserSource=${playerSource}` };
});

await addCheck("success_case", playerSource, async () => {
  await api("clock", "manual");
  await api("scenario", "play-near-win");
  const action = page.locator('[data-qa="action"]');
  if (inputMode === "touch") await action.tap(); else if (inputMode === "keyboard") { await action.focus(); await action.press("Enter"); } else await action.click();
  const s = await state();
  return { ok: s.result === "win", note: `result=${s.result}` };
});

await addCheck("failure_case", "INJECTED", async () => {
  await api("scenario", "play-near-timeout");
  await api("advance", 1000);
  const s = await state();
  return { ok: s.result === "lose", note: `result=${s.result}` };
});

await addCheck("retry_case", playerSource, async () => {
  await api("scenario", "result-lose");
  const restart = page.locator('[data-qa="restart"]');
  if (inputMode === "touch") await restart.tap(); else if (inputMode === "keyboard") { await restart.focus(); await restart.press("Enter"); } else await restart.click();
  const s = await state();
  return { ok: s.mode === "TITLE" && s.result === null, note: `mode=${s.mode}` };
});

await addCheck("edge_case", playerSource, async () => {
  await api("scenario", "play-start");
  await api("advance", 1450);
  const action = page.locator('[data-qa="action"]');
  if (inputMode === "touch") await action.tap(); else if (inputMode === "keyboard") { await action.focus(); await action.press("Enter"); } else await action.click();
  const s = await state();
  return { ok: s.dodges === 1 && s.result === null, note: `dodges=${s.dodges}; result=${s.result}` };
});

async function spamActions() {
  for (let i = 0; i < 12; i += 1) {
    const action = page.locator('[data-qa="action"]');
    if (!(await action.isVisible().catch(() => false))) break;
    if (inputMode === "touch") await action.tap(); else if (inputMode === "keyboard") { await action.focus(); await action.press("Enter"); } else await action.click();
  }
}
await addCheck("degenerate_spam", playerSource, async () => {
  await api("scenario", "play-start");
  await spamActions();
  const s = await state();
  const wins = s.result === "win";
  return { ok: intended.has("spam") || !wins, note: `result=${s.result}; intended=${intended.has("spam")}` };
});

await addCheck("degenerate_idle", "INJECTED", async () => {
  await api("scenario", "play-start");
  await api("advance", 2000);
  const s = await state();
  const wins = s.result === "win";
  return { ok: intended.has("idle") || !wins, note: `result=${s.result}; intended=${intended.has("idle")}` };
});

await addCheck("degenerate_repeat", playerSource, async () => {
  await api("scenario", "play-start");
  for (let i = 0; i < 5; i += 1) {
    await api("advance", 400);
    const action = page.locator('[data-qa="action"]');
    if (!(await action.isVisible().catch(() => false))) break;
    if (inputMode === "touch") await action.tap(); else if (inputMode === "keyboard") { await action.focus(); await action.press("Enter"); } else await action.click();
  }
  const s = await state();
  const wins = s.result === "win";
  return { ok: intended.has("repeat") || !wins, note: `result=${s.result}; intended=${intended.has("repeat")}` };
});

const elapsed = Date.now() - startedAt;
if (elapsed < 10000) await page.waitForTimeout(10000 - elapsed);
await context.close();
await browser.close();
if (hosted) await new Promise((ok) => hosted.server.close(ok));

let videoPath = "";
try {
  const actual = await video.path();
  videoPath = relative(ROOT, actual).replaceAll("\\", "/");
} catch {}

const inconclusive = checks.some((x) => x.status === "INCONCLUSIVE");
const failures = checks.filter((x) => x.status === "FAIL");
const degenerateFailures = failures.filter((x) => x.name.startsWith("degenerate_"));
let agentVerdict = "READY_FOR_PLAYTEST";
const reasons = [];
if (inconclusive || harnessFailure) {
  agentVerdict = "UNCERTAIN";
  reasons.push({ class: "HARNESS", message: "One or more browser checks were inconclusive." });
} else if (failures.length) {
  agentVerdict = "MACHINE_REJECT";
  if (degenerateFailures.length) reasons.push({ class: "MECHANIC", message: "A non-intended degenerate strategy matched the success outcome." });
  else reasons.push({ class: "IMPLEMENTATION", message: "One or more required machine checks failed." });
}

const report = {
  schema_version: 1,
  probe_id: card.probe_id,
  card_sha256: card.frozen_sha256,
  source_sha: sourceSha(),
  build_id: hashTree(DIST),
  viewport,
  input_mode: inputMode,
  browser: { name: "chromium", version: browserVersion || "unknown", url },
  checks,
  video: videoPath,
  agent_verdict: agentVerdict,
  human_verdict: "PENDING",
  reasons,
  generated_at: new Date().toISOString()
};
mkdirSync(PROBE_DIR, { recursive: true });
writeFileSync(join(PROBE_DIR, "report.json"), JSON.stringify(report, null, 2) + "\n", "utf8");
console.log(JSON.stringify(report, null, 2));
if (agentVerdict === "MACHINE_REJECT") process.exitCode = 1;
