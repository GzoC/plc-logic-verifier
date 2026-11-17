"""Exercise actual loopback HTTP, repeated runs and all four export representations."""

import argparse
import json
import re
import threading
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from plc_verifier.limits import HTTP_REQUEST_BYTES, bounded, compact
from plc_verifier.reports import csv_report, html_report, json_report, junit_report, validate_result
from plc_verifier.scenario import verify
from plc_verifier.web import make_server

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "docs/evidence/audit-2026-11-16")
    dest = parser.parse_args().output
    server = make_server(0, ROOT / "examples")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    summary = []
    try:
        with urllib.request.urlopen(base) as response:
            token = re.search(r"const token='([^']+)'", response.read().decode()).group(1)
        with urllib.request.urlopen(base + "/examples") as response:
            catalog = json.load(response)

        def post(path, data):
            raw = bounded(compact(data), HTTP_REQUEST_BYTES, "HTTP request").encode()
            request = urllib.request.Request(
                base + path,
                data=raw,
                headers={"Content-Type": "application/json", "X-PLC-Token": token},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read()
                assert len(content) == int(response.headers["Content-Length"])
                return content

        for item in catalog:
            inputs = dict(source=item["source"], scenario=item["scenario"])
            raw = post("/run", inputs)
            result = validate_result(json.loads(raw))
            expected = "FAIL" if "DEFECTO" in item["name"] else "PASS"
            assert result["status"] == expected, item["name"]
            assert json.loads(post("/run", inputs)) == result
            direct = verify(item["source"], item["scenario"])
            assert (
                direct["trace"] == result["trace"]
                and direct["requirements"] == result["requirements"]
            )
            sizes = {}
            for fmt, formatter in {
                "json": json_report,
                "csv": csv_report,
                "html": html_report,
                "xml": junit_report,
            }.items():
                document = post("/export", {"result": result, "format": fmt})
                assert document.decode() == formatter(result)
                sizes[fmt] = len(document)
                if fmt == "json":
                    assert validate_result(json.loads(document)) == result
                if fmt == "xml":
                    ET.fromstring(document)
            summary.append(
                {
                    "example": item["name"],
                    "status": expected,
                    "repeat_identical": True,
                    "direct_engine_equal": True,
                    "http_result_bytes": len(raw),
                    "export_bytes": sizes,
                }
            )
        assert len(summary) == 12
        out = dest
        out.mkdir(parents=True, exist_ok=True)
        (out / "http.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("HTTP: 12 expected results, 12 identical repeats, 48 exports, 12 JSON reimports PASS")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
