#!/usr/bin/env python3
"""Kurej dashboard: serves the page and saves your data to data/kurej_trading.json.
Run:  python3 server.py      then open http://localhost:3010
"""
import json, os, shutil, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", 3010))
ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "kurej_dashboard.html")
DATA_DIR = os.path.join(ROOT, "data")
DATA = os.path.join(DATA_DIR, "kurej_trading.json")
BACKUPS = os.path.join(DATA_DIR, "backups")
MAX_BYTES = 50 * 1024 * 1024

class H(BaseHTTPRequestHandler):
    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/kurej_dashboard.html", "/index.html"):
            with open(PAGE, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if path == "/api/data":
            if os.path.exists(DATA):
                with open(DATA, "rb") as f:
                    return self._send(200, f.read())
            return self._send(404, b'{"error":"no data yet"}')
        self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        if self.path.split("?")[0] != "/api/data":
            return self._send(404, b'{"error":"not found"}')
        n = int(self.headers.get("Content-Length", 0))
        if n <= 0 or n > MAX_BYTES:
            return self._send(400, b'{"error":"bad size"}')
        raw = self.rfile.read(n)
        try:
            body = json.loads(raw)
            assert isinstance(body, dict) and "data" in body
        except Exception:
            return self._send(400, b'{"error":"bad json"}')
        os.makedirs(BACKUPS, exist_ok=True)
        # one backup per day of the previous version
        if os.path.exists(DATA):
            day = datetime.date.today().isoformat()
            bak = os.path.join(BACKUPS, f"kurej_trading-{day}.json")
            if not os.path.exists(bak):
                shutil.copy2(DATA, bak)
        tmp = DATA + ".tmp"
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, DATA)  # atomic: never leaves a half-written file
        self._send(200, b'{"ok":true}')

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Dashboard: http://localhost:{PORT}\nData file: {DATA}\nCtrl+C to stop")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
