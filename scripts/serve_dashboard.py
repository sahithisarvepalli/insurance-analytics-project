"""Serve insurance analytics dashboards at http://localhost:8000/.

Supports two modes:

1. **Single dashboard** — ``--html outputs/dashboard.html``
   Serves the single file at the root URL.

2. **Multi-client directory** — ``--dir outputs``
   Discovers ``outputs/*/dashboard.html`` sub-folders and serves a landing
   page that links to each client dashboard.

VS Code detects the open port and shows an "Open in Browser" popup.

Usage:
    python scripts/serve_dashboard.py [--port PORT] [--dir outputs | --html path/to/dashboard.html]
"""

# Pylint: this script is a small dev helper; relax some style checks that are
# noisy in CI/dev containers.
# pylint: disable=arguments-differ,redefined-outer-name,consider-using-in

import argparse
import http.server
import pathlib
import urllib.parse

_DEFAULT_PORT = 8000


def _discover_dashboards(base: pathlib.Path) -> list[tuple[str, pathlib.Path]]:
    """Return ``[(client_id, html_path), ...]`` for every ``<base>/*/dashboard.html``."""
    results = []
    for child in sorted(base.iterdir()):
        html = child / "dashboard.html"
        if child.is_dir() and html.exists():
            results.append((child.name, html))
    return results


def _build_landing_page(dashboards: list[tuple[str, pathlib.Path]]) -> bytes:
    """Generate a simple landing page linking to each client dashboard."""
    links = ""
    for client_id, _ in dashboards:
        label = client_id.replace("_", " ").title()
        links += (
            f'<a href="/{client_id}/dashboard.html" '
            f'style="display:block;margin:12px 0;font-size:1.2em;">'
            f"{label}</a>\n"
        )
    html = f"""\
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Insurance Analytics</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 600px; margin: 60px auto; }}
  a {{ color: #0066cc; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style></head>
<body>
<h1>Insurance Analytics Dashboards</h1>
<p>Select a client to view its dashboard:</p>
{links}
</body></html>"""
    return html.encode()


class _MultiHandler(http.server.BaseHTTPRequestHandler):
    """Serve landing page at ``/`` and per-client dashboards at ``/<id>/dashboard.html``."""

    _base: pathlib.Path
    _landing: bytes = b""
    _dashboards: dict[str, bytes] = {}

    def do_GET(self) -> None:  # noqa: N802
        path = urllib.parse.unquote(self.path).strip("/")
        if path == "" or path == "index.html":
            body = self._landing
        elif path in self._dashboards:
            body = self._dashboards[path]
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: D102
        pass


class _SingleHandler(http.server.BaseHTTPRequestHandler):
    """Serve a single HTML file at every URL (original behaviour)."""

    _html: bytes = b""

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self._html)))
        self.end_headers()
        self.wfile.write(self._html)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: D102
        pass


def serve(
    html_path: str | None = None, base_dir: str | None = None, port: int = _DEFAULT_PORT
) -> None:
    """Serve dashboards.

    Provide *html_path* for single mode, *base_dir* for multi-client.
    """
    # Handler variable may hold different handler classes depending on mode.
    handler: type[http.server.BaseHTTPRequestHandler]

    if base_dir:
        base = pathlib.Path(base_dir)
        dashboards = _discover_dashboards(base)
        if not dashboards:
            # Fallback: serve outputs/dashboard.html if it exists
            fallback = base / "dashboard.html"
            if fallback.exists():
                _SingleHandler._html = fallback.read_bytes()
                handler = _SingleHandler
            else:
                raise SystemExit(f"No dashboards found in {base}/*/dashboard.html")
        else:
            _MultiHandler._base = base
            _MultiHandler._landing = _build_landing_page(dashboards)
            _MultiHandler._dashboards = {
                f"{cid}/dashboard.html": path.read_bytes() for cid, path in dashboards
            }
            handler = _MultiHandler
    elif html_path:
        _SingleHandler._html = pathlib.Path(html_path).read_bytes()
        handler = _SingleHandler
    else:
        raise SystemExit("Provide --html or --dir")

    # Bind to localhost by default to avoid exposing the server on all interfaces.
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    print(f"📊 Dashboard → http://localhost:{port}")
    print("   VS Code will show an 'Open in Browser' popup — click it to open the charts.")
    print("   Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Serve the insurance analytics dashboard.")
    ap.add_argument("--port", type=int, default=_DEFAULT_PORT, help="Port to listen on.")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--html", default=None, help="Path to a single dashboard HTML file.")
    group.add_argument(
        "--dir", default=None, help="Base outputs directory with per-client sub-folders."
    )
    args = ap.parse_args()
    serve(html_path=args.html, base_dir=args.dir, port=args.port)
