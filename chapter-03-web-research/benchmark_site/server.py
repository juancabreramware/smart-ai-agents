"""Tiny versioned pricing site used by the reproducible Chapter 3 benchmark.

The server reads current_version.txt on every request. Another process can therefore
switch v1 -> v2 while the server remains alive, simulating a production website change.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION_FILE = ROOT / "current_version.txt"


def current_html() -> bytes:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    path = ROOT / version / "pricing.html"
    if not path.exists():
        raise FileNotFoundError(f"Unknown benchmark site version {version!r}")
    return path.read_bytes()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path in {"/", "/pricing", "/pricing/"}:
            body = current_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/health":
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def log_message(self, format, *args):  # noqa: A003
        # Keep experiment output readable. Re-enable super().log_message for HTTP debugging.
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Chapter 3 benchmark site: http://{args.host}:{args.port}/pricing")
    print(f"Current version: {VERSION_FILE.read_text().strip()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
