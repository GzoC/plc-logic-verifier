import argparse
import hashlib
import json
import threading
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from plc_verifier.reports import csv_report, html_report, json_report, junit_report
from plc_verifier.web import make_server


def main():
    parser = argparse.ArgumentParser(description="Verify files saved by Microsoft Edge")
    parser.add_argument("output", type=Path)
    out = parser.parse_args().output
    server = make_server(0, Path(__file__).resolve().parents[1] / "examples")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    manifest = {"downloads": [], "console": [], "page_errors": []}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge", chromium_sandbox=True)
            manifest["browser"] = "Microsoft Edge " + browser.version
            page = browser.new_page(accept_downloads=True)
            page.on("pageerror", lambda err: manifest["page_errors"].append(str(err)))
            page.on(
                "console",
                lambda msg: manifest["console"].append(
                    [msg.type, msg.text, msg.location.get("url", "").split("/")[-1]]
                ),
            )
            page.goto(f"http://127.0.0.1:{server.server_port}")
            for status, label in [("PASS", "normal"), ("FAIL", "DEFECTO reverse_start")]:
                page.locator("#examples").select_option(label=f"conveyor / {label}")
                page.locator("#load").click()
                with page.expect_response(lambda r: r.url.endswith("/run")) as run:
                    page.locator("#run").click()
                result = run.value.json()
                assert result["status"] == status and run.value.status == 200
                expect(page.locator("#verdict")).to_have_text(status)
                for fmt, name, formatter in [
                    ("json", "result.json", json_report),
                    ("csv", "trace.csv", csv_report),
                    ("html", "report.html", html_report),
                    ("xml", "junit.xml", junit_report),
                ]:
                    with (
                        page.expect_download() as event,
                        page.expect_response(lambda r: r.url.endswith("/export")) as export,
                    ):
                        page.locator(f'[data-format="{fmt}"]').click()
                    download, response = event.value, export.value
                    assert download.suggested_filename == name and download.failure() is None
                    target = out / status / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    download.save_as(target)
                    raw = target.read_bytes()
                    assert response.status == 200 and response.request.method == "POST"
                    assert response.request.post_data_json == {"format": fmt, "result": result}
                    assert raw == response.body() == formatter(result).encode()
                    row = dict(
                        file=f"{status}/{name}",
                        bytes=len(raw),
                        sha256=hashlib.sha256(raw).hexdigest(),
                        request="POST /export",
                        status=response.status,
                        mime=response.headers["content-type"],
                        event="download",
                    )
                    if fmt == "xml":
                        root = ET.fromstring(raw)
                        totals = {
                            k: int(root.attrib[k])
                            for k in ("tests", "failures", "errors", "skipped")
                        }
                        statuses = [r["status"] for r in result["requirements"]]
                        assert totals == dict(
                            tests=len(statuses),
                            failures=statuses.count("FAIL"),
                            errors=0,
                            skipped=0,
                        )
                        assert list(totals.values()) == [
                            len(root.findall(path))
                            for path in (
                                "testcase",
                                "testcase/failure",
                                "testcase/error",
                                "testcase/skipped",
                            )
                        ]
                        row["junit"] = totals
                    manifest["downloads"].append(row)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        out.mkdir(parents=True, exist_ok=True)
        (out / "edge.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    assert not manifest["page_errors"]
    print(manifest["browser"], len(manifest["downloads"]), "files verified")


if __name__ == "__main__":
    main()
