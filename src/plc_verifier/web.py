"""Loopback-only local UI; bounded workers, no arbitrary paths or PLC connections."""

import json
import secrets
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .ai import draft_info, explain, preview_payload
from .language import VerificationError
from .limits import HTTP_REQUEST_BYTES, compact
from .reports import csv_report, html_report, json_report, junit_report, validate_result
from .scenario import NOTICE


def isolated_verify(source: str, scenario: str):
    if not isinstance(source, str) or not isinstance(scenario, str):
        raise VerificationError("Program and scenario must be strings")
    if len(source.encode()) > 65536 or len(scenario.encode()) > 65536:
        raise VerificationError("Program/scenario exceed 64 KiB")
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "plc_verifier.worker"],
            input=json.dumps({"source": source, "scenario": scenario}),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as exc:
        raise VerificationError("Worker timed out (15 seconds); terminated") from exc
    if completed.returncode:
        raise VerificationError("Isolated worker failed; no passing result available")
    return validate_result(json.loads(completed.stdout))


def example_catalog(root: Path):
    result = []
    for case in ("lubrication", "alternating", "conveyor"):
        for name in ("normal", "fault"):
            folder = root / case
            if not (folder / f"{name}.yaml").is_file():
                continue
            scenario = (folder / f"{name}.yaml").read_text(encoding="utf-8")
            result.append(
                {
                    "name": f"{case} / {name}",
                    "source": (folder / "correct.st").read_text(encoding="utf-8"),
                    "scenario": scenario,
                }
            )
            mutations = {
                ("lubrication", "fault"): ["timeout_disabled", "auto_ack"],
                ("alternating", "normal"): ["overlap", "no_alternation"],
                ("conveyor", "normal"): ["reverse_start"],
                ("conveyor", "fault"): ["auto_restart"],
            }.get((case, name), [])
            for mutant in mutations:
                result.append(
                    {
                        "name": f"{case} / DEFECTO {mutant}",
                        "source": (folder / "defects" / f"{mutant}.st").read_text(encoding="utf-8"),
                        "scenario": scenario,
                    }
                )
    return result


def make_server(port=8765, examples: Path | None = None):
    token = secrets.token_urlsafe(32)
    slots = threading.BoundedSemaphore(2)
    catalog = example_catalog(examples or Path.cwd() / "examples")
    page = (
        Path(__file__)
        .with_name("ui.html")
        .read_text(encoding="utf-8")
        .replace("__TOKEN__", token)
        .replace("__NOTICE__", NOTICE)
    )

    class Handler(BaseHTTPRequestHandler):
        server: ThreadingHTTPServer

        def log_message(self, format, *args):
            pass  # No program, trace or credentials in HTTP logs.

        def respond(self, status, payload, kind="application/json; charset=utf-8"):
            body = payload.encode() if isinstance(payload, str) else compact(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def allowed(self):
            port = self.server.server_port
            hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
            return self.headers.get("Host") in hosts and self.headers.get("Origin") in {
                None,
                *(f"http://{h}" for h in hosts),
            }

        def do_GET(self):
            if not self.allowed():
                self.respond(403, {"error": "Local origin required"})
            elif self.path == "/":
                self.respond(200, page, "text/html; charset=utf-8")
            elif self.path == "/examples":
                self.respond(200, catalog)
            else:
                self.respond(404, {"error": "Not found"})

        def do_POST(self):
            if not self.allowed() or not secrets.compare_digest(
                self.headers.get("X-PLC-Token", ""), token
            ):
                self.respond(403, {"error": "Local request token required"})
                return
            if not slots.acquire(blocking=False):
                self.respond(429, {"error": "Two requests already active"})
                return
            try:
                self.connection.settimeout(25)
                size = int(self.headers.get("Content-Length", "0"))
                if (
                    not 0 < size <= HTTP_REQUEST_BYTES
                    or self.headers.get_content_type() != "application/json"
                ):
                    raise VerificationError(
                        f"Expected JSON body, maximum {HTTP_REQUEST_BYTES} bytes"
                    )
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise VerificationError("Expected object")
                if self.path == "/run":
                    response = isolated_verify(data["source"], data["scenario"])
                elif self.path == "/export":
                    result = validate_result(data["result"])
                    formatter = {
                        "html": html_report,
                        "json": json_report,
                        "csv": csv_report,
                        "xml": junit_report,
                    }[data["format"]]
                    self.respond(200, formatter(result), "application/octet-stream")
                    return
                elif self.path == "/ai/preview":
                    response = draft_info(
                        preview_payload(
                            validate_result(data["result"]),
                            data.get("source"),
                            False,
                            **data.get("selection", {}),
                        )
                    )
                elif self.path == "/ai/send":
                    response = explain(
                        data["payload"], send=data.get("send") is True, source=data.get("source")
                    )
                else:
                    self.respond(404, {"error": "Not found"})
                    return
                self.respond(200, response)
            except (
                VerificationError,
                ValueError,
                KeyError,
                TypeError,
                OSError,
                RecursionError,
            ) as exc:
                self.respond(400, {"error": str(exc)})
            finally:
                slots.release()

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(port=8765):
    server = make_server(port)
    print(
        f"PLC Logic Verifier: http://127.0.0.1:{server.server_port} (Ctrl+C para cerrar)",
        flush=True,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
