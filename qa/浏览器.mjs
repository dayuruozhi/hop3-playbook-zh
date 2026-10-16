// usage: node cdp.mjs <url> <width> <outprefix> [segments] [evalJS] [theme]
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
const [url, width = "1280", out = "shot", segs = "0", evalJs = "", theme = ""] = process.argv.slice(2);
const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn("google-chrome", ["--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${port}`, `--window-size=${width},1000`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, id = 0; const pending = new Map(); const logs = [];
async function main() {
  let target;
  for (let i = 0; i < 50; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/json`); const j = await r.json(); target = j.find((t) => t.type === "page"); if (target) break; } catch {}
    await sleep(200);
  }
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener("open", r));
  ws.addEventListener("message", (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === "Runtime.consoleAPICalled") logs.push("console." + m.params.type + ": " + m.params.args.map((a) => a.value ?? a.description).join(" "));
    if (m.method === "Runtime.exceptionThrown") logs.push("EXCEPTION: " + JSON.stringify(m.params.exceptionDetails).slice(0, 400));
    if (m.method === "Log.entryAdded" && m.params.entry.level === "error") logs.push("LOG: " + m.params.entry.text);
  });
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Runtime.enable"); await send("Log.enable"); await send("Page.enable");
  const w = +width;
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: 900, deviceScaleFactor: 1, mobile: w < 640 });
  const nojs = process.env.NOJS === "1";
  if (nojs) await send("Emulation.setScriptExecutionDisabled", { value: true });
  const feats = [];
  if (theme) feats.push({ name: "prefers-color-scheme", value: theme });
  if (process.env.REDUCE === "1") feats.push({ name: "prefers-reduced-motion", value: "reduce" });
  if (feats.length) await send("Emulation.setEmulatedMedia", { features: feats });
  await send("Page.navigate", { url });
  await sleep(3500);
  const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result?.result?.value;
  const metrics = await ev(`JSON.stringify({sw:document.documentElement.scrollWidth, iw:innerWidth, h:document.documentElement.scrollHeight})`);
  console.log("metrics", metrics);
  const wide = await ev(`(function(){var r=[];document.querySelectorAll('main *').forEach(function(e){var b=e.getBoundingClientRect();if(b.right>innerWidth+1&&b.width>0){var p=e.parentElement;var clipped=false;while(p){var cs=getComputedStyle(p);if(/(auto|scroll|hidden|clip)/.test(cs.overflowX)&&p.getBoundingClientRect().right<=innerWidth+1){clipped=true;break;}p=p.parentElement;}if(!clipped)r.push(e.tagName+'.'+e.className+'#'+e.id+' r='+Math.round(b.right));}});return r.slice(0,15).join('\\n');})()`);
  if (wide) console.log("OVERFLOWING:\n" + wide);
  if (evalJs) console.log("eval:", await ev(evalJs));
  if (process.env.EVAL2) { await send("Page.reload", {}); await sleep(3000); console.log("eval2:", await ev(process.env.EVAL2)); }
  const H = JSON.parse(metrics).h;
  const parts = segs.split(","); const n = segs === "auto" ? Math.ceil(H / 2400) : parts.length;
  for (let k = 0; k < (segs==="0"?0:n); k++) {
    let y = k * 2400; if (segs !== "auto") { const t = parts[k]; y = /^\d+$/.test(t) ? +t : await ev("(function(){var e=document.getElementById('" + t + "');return e?Math.round(e.getBoundingClientRect().top+scrollY-50):0})()"); }
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: 2400, deviceScaleFactor: 1, mobile: w < 640 });
    await ev("window.scrollTo(0," + y + ")"); await sleep(400);
    const sy = await ev("window.scrollY");
    const r = await send("Page.captureScreenshot", { format: "png", clip: { x: 0, y: sy, width: w, height: 2400, scale: w < 640 ? 1 : 0.6 } });
    writeFileSync(`${out}-${k}.png`, Buffer.from(r.result.data, "base64"));
  }
  console.log(logs.length ? logs.join("\n") : "no console errors");
  ws.close(); chrome.kill();
}
main().catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
