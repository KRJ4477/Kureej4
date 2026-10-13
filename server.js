// Kurej dashboard: serves the page and saves your data to data/kurej_trading.json.
// Run:  node server.js      then open http://localhost:3010
const http = require("http"), fs = require("fs"), path = require("path");
const PORT = process.env.PORT || 3010;
const PAGE = path.join(__dirname, "kurej_dashboard.html");
const DATA_DIR = path.join(__dirname, "data");
const DATA = path.join(DATA_DIR, "kurej_trading.json");
const BACKUPS = path.join(DATA_DIR, "backups");
const MAX = 50 * 1024 * 1024;

const send = (res, code, body = "", type = "application/json") => {
  res.writeHead(code, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(body);
};

http.createServer((req, res) => {
  const p = req.url.split("?")[0];
  if (req.method === "GET") {
    if (["/", "/kurej_dashboard.html", "/index.html"].includes(p))
      return send(res, 200, fs.readFileSync(PAGE), "text/html; charset=utf-8");
    if (p === "/api/data")
      return fs.existsSync(DATA) ? send(res, 200, fs.readFileSync(DATA)) : send(res, 404, '{"error":"no data yet"}');
  }
  if (req.method === "POST" && p === "/api/data") {
    const chunks = []; let size = 0;
    req.on("data", c => { size += c.length; if (size > MAX) req.destroy(); else chunks.push(c); });
    req.on("end", () => {
      const raw = Buffer.concat(chunks);
      try { const b = JSON.parse(raw); if (!b || typeof b !== "object" || !("data" in b)) throw 0; }
      catch { return send(res, 400, '{"error":"bad json"}'); }
      fs.mkdirSync(BACKUPS, { recursive: true });
      if (fs.existsSync(DATA)) {
        const bak = path.join(BACKUPS, `kurej_trading-${new Date().toISOString().slice(0, 10)}.json`);
        if (!fs.existsSync(bak)) fs.copyFileSync(DATA, bak);
      }
      fs.writeFileSync(DATA + ".tmp", raw);
      fs.renameSync(DATA + ".tmp", DATA); // atomic
      send(res, 200, '{"ok":true}');
    });
    return;
  }
  send(res, 404, '{"error":"not found"}');
}).listen(PORT, "127.0.0.1", () =>
  console.log(`Dashboard: http://localhost:${PORT}\nData file: ${DATA}\nCtrl+C to stop`));
