import copy
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from plc_verifier.ai import Advice, draft_info, explain, preview_payload, validate_payload
from plc_verifier.cli import main, read_text
from plc_verifier.engine import Engine
from plc_verifier.language import VerificationError, parse_program
from plc_verifier.limits import FORMAT_BYTES, RESULT_BYTES, bounded
from plc_verifier.reports import export, html_report, json_report, validate_result
from plc_verifier.scenario import verify

ROOT = Path(__file__).resolve().parents[1]


def config(requirements=None, **kwargs):
    return yaml.safe_dump(
        dict(
            id="audit",
            description="Audit regression",
            program="program.st",
            duration_ms=400,
            scan_ms=100,
            requirements=requirements
            or [dict(id="R", description="Always", kind="always", expr="TRUE")],
            **kwargs,
        )
    )


def test_actual_shipped_javascript():
    done = subprocess.run(
        ["node", "--test", "tests/ui_races.test.cjs"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert done.returncode == 0, done.stdout + done.stderr


@pytest.mark.parametrize("scan", [10, 50, 100, 70])
def test_conveyor_observable_deadlines(scan):
    e = Engine(parse_program((ROOT / "examples/conveyor/correct.st").read_text()), scan)
    deadline = ((200 + scan - 1) // scan) * scan
    rows = [e.step({"Start": i == 0}) for i in range(deadline // scan + 2)]
    assert rows[0]["outputs"] == {"A": False, "B": True, "FAULT": False}
    for row in rows:
        assert row["outputs"]["A"] == (row["time_ms"] >= deadline)
    stop_at = e.time_ms
    rows = [e.step({"Stop": True}) for _ in range(deadline // scan + 2)]
    for row in rows:
        assert row["outputs"]["A"] is False
        assert row["outputs"]["B"] == (row["time_ms"] - stop_at < deadline)


@pytest.mark.parametrize("scan", [10, 50, 100, 70])
def test_stop_during_start_and_explicit_restart(scan):
    e = Engine(parse_program((ROOT / "examples/conveyor/correct.st").read_text()), scan)
    e.step({"Start": True})
    stop_at = e.time_ms
    deadline = ((200 + scan - 1) // scan) * scan
    rows = [e.step({"Stop": True, "Start": False}) for _ in range(deadline // scan + 2)]
    assert all(not row["outputs"]["A"] for row in rows)
    assert next(row["time_ms"] for row in rows if not row["outputs"]["B"]) == stop_at + deadline
    assert not e.step({"Stop": False})["outputs"]["B"]
    restart = e.time_ms
    rows = [e.step({"Start": i == 0}) for i in range(deadline // scan + 2)]
    assert next(row["time_ms"] for row in rows if row["outputs"]["A"]) == restart + deadline


@pytest.mark.parametrize("scan", [10, 50, 100, 70])
def test_lubrication_observable_cycle(scan):
    e = Engine(parse_program((ROOT / "examples/lubrication/correct.st").read_text()), scan)
    on = ((500 + scan - 1) // scan) * scan
    off = ((300 + scan - 1) // scan) * scan
    rows = [
        e.step({"Start": i == 0, "LevelOK": True, "Pressure": True})
        for i in range((on + off) // scan + 2)
    ]
    assert next(r["time_ms"] for r in rows if not r["outputs"]["PUMP"]) == on
    assert (
        next(r["time_ms"] for r in rows if r["time_ms"] > on and r["outputs"]["PUMP"]) == on + off
    )


@pytest.fixture
def legitimate():
    return verify("PROGRAM P END_PROGRAM", config())


@pytest.mark.parametrize(
    "mutation",
    [
        "empty",
        "contradiction",
        "hash",
        "indices",
        "version",
        "row",
        "error",
        "missing",
        "boolean_version",
    ],
)
def test_invalid_imports_are_controlled(tmp_path, legitimate, mutation, capsys):
    r = copy.deepcopy(legitimate)
    if mutation == "empty":
        r = dict(schema_version=1, status="PASS", trace=[], requirements=[])
    elif mutation == "contradiction":
        r["requirements"][0]["status"] = "FAIL"
    elif mutation == "hash":
        r["program_sha256"] = "invalid"
    elif mutation == "indices":
        r["requirements"][0]["evidence_scans"] = [-1, 100]
    elif mutation == "version":
        r["schema_version"] = 2
    elif mutation == "boolean_version":
        r["schema_version"] = True
    elif mutation == "row":
        r["trace"][0]["time_ms"] = "0"
    elif mutation == "error":
        r["error"] = dict(message="failure", line=1, column=1)
    else:
        del r["notice"]
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(r), encoding="utf-8")
    assert main(["report", str(path), "--output", str(tmp_path / "out")]) == 2
    assert "Traceback" not in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "source,req,status",
    [
        ("PROGRAM P END_PROGRAM", "TRUE", "PASS"),
        ("PROGRAM P END_PROGRAM", "FALSE", "FAIL"),
        ("PROGRAM P VAR X : INT; END_VAR X := 1/0; END_PROGRAM", "TRUE", "ERROR"),
        ("PROGRAM P WHILE TRUE DO END_WHILE; END_PROGRAM", "TRUE", "UNSUPPORTED"),
    ],
)
def test_legitimate_roundtrip(tmp_path, source, req, status):
    text = config([dict(id="R", description="Test", kind="always", expr=req)])
    result = verify(source, text)
    assert result["status"] == status
    export(result, tmp_path)
    restored = validate_result(json.loads(read_text(tmp_path / "result.json", RESULT_BYTES)))
    assert restored == result
    assert main(["report", str(tmp_path / "result.json"), "--output", str(tmp_path / "again")]) == 0
    for name in ["result.json", "trace.csv", "report.html", "junit.xml"]:
        assert (tmp_path / name).read_bytes() == (tmp_path / "again" / name).read_bytes()


def test_not_evaluated_and_early_error_roundtrip():
    text = config(
        [
            dict(
                id="R",
                description="No trigger",
                kind="response",
                trigger="FALSE",
                expr="TRUE",
                within_ms=0,
            )
        ]
    )
    for r in [verify("PROGRAM P END_PROGRAM", text), verify("", "invalid YAML")]:
        assert validate_result(json.loads(json_report(r))) == r


def test_exact_large_result_roundtrip(tmp_path):
    names = [f"X{i}" for i in range(30)]
    source = (
        "PROGRAM P VAR "
        + ",".join(names)
        + " : INT; END_VAR "
        + " ".join(f"{n} := {n}+1;" for n in names)
        + " END_PROGRAM"
    )
    scenario = yaml.safe_load(config())
    scenario["duration_ms"] = 700000
    r = verify(source, yaml.safe_dump(scenario))
    assert r["status"] == "PASS", r["error"]
    assert r["trace"][-1]["variables"] == {name: 7000 for name in names}
    export(r, tmp_path)
    restored = validate_result(json.loads(read_text(tmp_path / "result.json", RESULT_BYTES)))
    assert restored == r
    assert len(json_report(r).encode()) < RESULT_BYTES
    assert len(html_report(r).encode()) < FORMAT_BYTES["html"]
    assert main(["report", str(tmp_path / "result.json"), "--output", str(tmp_path / "again")]) == 0
    for name in ["result.json", "trace.csv", "report.html", "junit.xml"]:
        assert (
            hashlib.sha256((tmp_path / name).read_bytes()).digest()
            == hashlib.sha256((tmp_path / "again" / name).read_bytes()).digest()
        )


def test_byte_boundaries_and_atomic_preflight(tmp_path, legitimate, monkeypatch):
    assert bounded("é" * 8, 16, "test") == "é" * 8
    with pytest.raises(VerificationError):
        bounded("é" * 8, 15, "test")
    path = tmp_path / "large.json"
    with path.open("wb") as stream:
        stream.seek(RESULT_BYTES)
        stream.write(b"x")
    assert main(["report", str(path), "--output", str(tmp_path / "out")]) == 2
    monkeypatch.setitem(FORMAT_BYTES, "html", 100)
    with pytest.raises(VerificationError, match="HTML"):
        export(legitimate, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_large_ai_draft_can_be_reduced_without_network(tmp_path, monkeypatch):
    reqs = [dict(id=f"R{i}", description="d" * 500, kind="always", expr="TRUE") for i in range(30)]
    text = config(reqs)
    source = "PROGRAM P END_PROGRAM"
    result = verify(source, text)
    draft = preview_payload(result)
    assert draft_info(draft)["size_bytes"] > 24000
    assert not draft_info(draft)["sendable"]
    with pytest.raises(VerificationError, match="24000"):
        validate_payload(draft)
    reduced = preview_payload(result, requirement_ids=["R0"], scan_indices=[])
    assert len(reduced["selection"]["omitted_requirements"]) == 29
    assert draft_info(reduced)["sendable"]
    validate_payload(reduced)
    result_path = tmp_path / "result.json"
    result_path.write_text(json_report(result), encoding="utf-8")
    payload_path = tmp_path / "draft.json"
    assert main(["explain", str(result_path), "--payload", str(payload_path)]) == 0
    assert json.loads(payload_path.read_text(encoding="utf-8")) == draft


def test_suggestion_schema_variables_and_local_type_check(monkeypatch):
    source = "PROGRAM P VAR_INPUT Enable : BOOL; END_VAR VAR_OUTPUT Q : BOOL; END_VAR Q := Enable; END_PROGRAM"
    r = verify(source, config())
    draft = preview_payload(r, source, suggest_scenarios=True, include_program=False)
    assert "program" not in draft
    assert draft["variables"]["ENABLE"]["type"] == "BOOL"
    assert "$defs" in draft["scenario_schema"]
    validate_payload(draft)
    monkeypatch.setenv("OPENAI_MODEL", "mock-only")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-only")
    suggestions = [
        config([dict(id="R", description="Valid", kind="always", expr="Q = Enable")]),
        config([dict(id="R", description="Undeclared", kind="always", expr="Missing")]),
        config([dict(id="R", description="Wrong type", kind="always", expr="Q + 1")]),
    ]
    advice = Advice(
        summary="Mock",
        evidence=[],
        hypotheses=[],
        ambiguities=[],
        suggested_scenarios=suggestions,
        proposed_diff="",
    )
    client = SimpleNamespace(
        responses=SimpleNamespace(parse=lambda **kwargs: SimpleNamespace(output_parsed=advice))
    )
    out = explain(draft, send=True, source=source, client=client)
    assert out["scenario_validation"][0]["references_types"] == "PASS"
    assert all(v["execution"] == "NOT_EVALUATED" for v in out["scenario_validation"])
    assert [v["syntax_schema"] for v in out["scenario_validation"]] == ["PASS", "PASS", "PASS"]
    assert [v["references_types"] for v in out["scenario_validation"]] == ["PASS", "ERROR", "ERROR"]
    with pytest.raises(VerificationError, match="hash"):
        preview_payload(r, "PROGRAM Other END_PROGRAM")
