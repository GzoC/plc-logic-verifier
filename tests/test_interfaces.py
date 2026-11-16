import copy
import json
import re
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

from plc_verifier.ai import Advice, explain, preview_payload
from plc_verifier.cli import main
from plc_verifier.language import VerificationError
from plc_verifier.reports import csv_report, html_report, junit_report
from plc_verifier.scenario import verify
from plc_verifier.web import isolated_verify, make_server

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples/lubrication/fault.yaml"
SOURCE = ROOT / "examples/lubrication/defects/timeout_disabled.st"


@pytest.fixture
def result():
    return verify(SOURCE.read_text(), SCENARIO.read_text(encoding="utf-8"))


def test_cli_exit_codes_and_exports(tmp_path):
    assert main(["validate", str(SCENARIO)]) == 0
    assert main(["run", str(SCENARIO), "--program", str(SOURCE), "--output", str(tmp_path)]) == 1
    assert {p.name for p in tmp_path.iterdir()} == {
        "result.json",
        "trace.csv",
        "report.html",
        "junit.xml",
    }
    assert main(["report", str(tmp_path / "result.json"), "--output", str(tmp_path / "again")]) == 0
    assert (tmp_path / "report.html").read_bytes() == (tmp_path / "again/report.html").read_bytes()
    assert main(["run", str(tmp_path / "missing.yaml")]) == 2


def test_no_false_junit_success_on_error(result):
    result["status"] = "ERROR"
    result["requirements"] = [{"id": "R", "status": "NOT_EVALUATED"}]
    xml = ET.fromstring(junit_report(result))
    assert xml.attrib["errors"] == "1" and xml.attrib["skipped"] == "1"


def test_report_escapes_untrusted_labels_and_includes_evidence(result):
    result["requirements"][0]["description"] = '<script>alert("injection")</script>'
    page = html_report(result)
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert result["program_sha256"] in page and "Ventana de evidencia" in page
    assert "blocks.PRESSURETIMER.ET" in csv_report(result)
    assert int(ET.fromstring(junit_report(result)).attrib["failures"]) > 0


def test_web_worker_equals_cli_engine(result):
    web_result = isolated_verify(SOURCE.read_text(), SCENARIO.read_text(encoding="utf-8"))
    assert web_result["trace"] == result["trace"]
    assert web_result["requirements"] == result["requirements"]


def test_http_local_token_run_and_export():
    server = make_server(0, ROOT / "examples")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(base) as response:
            page = response.read().decode()
        token = re.search(r"const token='([^']+)'", page).group(1)
        data = json.dumps(
            {"source": SOURCE.read_text(), "scenario": SCENARIO.read_text(encoding="utf-8")}
        ).encode()
        with pytest.raises(urllib.error.HTTPError) as denied:
            urllib.request.urlopen(
                urllib.request.Request(
                    base + "/run", data=data, headers={"Content-Type": "application/json"}
                )
            )
        assert denied.value.code == 403
        headers = {"Content-Type": "application/json", "X-PLC-Token": token}
        with urllib.request.urlopen(
            urllib.request.Request(base + "/run", data=data, headers=headers)
        ) as response:
            result = json.load(response)
        assert result["status"] == "FAIL"
        with pytest.raises(urllib.error.HTTPError) as denied:
            urllib.request.urlopen(
                urllib.request.Request(
                    base + "/run", data=data, headers={**headers, "Origin": "https://example.com"}
                )
            )
        assert denied.value.code == 403
        export_data = json.dumps({"result": result, "format": "html"}).encode()
        with urllib.request.urlopen(
            urllib.request.Request(base + "/export", data=export_data, headers=headers)
        ) as response:
            assert "<!doctype html>" in response.read().decode()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_ai_preview_does_not_send_or_change_result(result):
    before = copy.deepcopy(result)
    source = "(* private comment *) PROGRAM P // hidden\n END_PROGRAM"
    from plc_verifier.scenario import load_scenario

    scenario = SCENARIO.read_text(encoding="utf-8")
    simple = verify(
        source,
        __import__("yaml").safe_dump(
            {
                **load_scenario(scenario).model_dump(),
                "initial": {},
                "events": [],
                "requirements": [
                    {"id": "R", "description": "Test", "kind": "always", "expr": "TRUE"}
                ],
            }
        ),
    )
    payload = preview_payload(simple, source)
    assert "private" not in payload["program"] and "hidden" not in payload["program"]
    assert result == before
    with pytest.raises(VerificationError, match="Explicit send"):
        explain(payload)


def test_ai_missing_credentials(monkeypatch, result):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    with pytest.raises(VerificationError, match="OPENAI_MODEL"):
        explain(preview_payload(result), send=True)


@pytest.mark.parametrize("behavior", ["timeout", "invalid", "refusal", "valid"])
def test_ai_provider_paths_mocked(monkeypatch, result, behavior):
    monkeypatch.setenv("OPENAI_API_KEY", "test-not-a-real-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model-only")

    def parse(**kwargs):
        assert kwargs["text_format"] is Advice
        if behavior == "timeout":
            raise TimeoutError("deliberate")
        if behavior == "invalid":
            return SimpleNamespace(output_parsed={"arbitrary": "untrusted"})
        if behavior == "refusal":
            return SimpleNamespace(output_parsed=None)
        return SimpleNamespace(
            output_parsed=Advice(
                summary="Hipótesis",
                evidence=[],
                hypotheses=[],
                ambiguities=[],
                suggested_scenarios=["not: a scenario"],
                proposed_diff="",
            )
        )

    client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    if behavior == "valid":
        response = explain(preview_payload(result), send=True, client=client)
        assert response["scenario_validation"][0]["syntax_schema"] == "ERROR"
        assert response["scenario_validation"][0]["execution"] == "NOT_EVALUATED"
    else:
        with pytest.raises(VerificationError):
            explain(preview_payload(result), send=True, client=client)


def test_ai_payload_limit():
    with pytest.raises(VerificationError, match="24000"):
        explain({"program": "x" * 24001}, send=True)
