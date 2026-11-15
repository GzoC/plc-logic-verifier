from pathlib import Path

import pytest
import yaml

from plc_verifier.scenario import verify

ROOT = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize("case", ["lubrication", "alternating", "conveyor"])
@pytest.mark.parametrize("scenario", ["normal", "fault"])
def test_correct_industrial(case, scenario):
    result = verify(
        (ROOT / case / "correct.st").read_text(),
        (ROOT / case / f"{scenario}.yaml").read_text(encoding="utf-8"),
    )
    assert result["status"] == "PASS", result


@pytest.mark.parametrize(
    "case,variant,scenario,requirement",
    [
        ("lubrication", "timeout_disabled", "fault", "L03"),
        ("lubrication", "auto_ack", "fault", "L05"),
        ("alternating", "overlap", "normal", "B02"),
        ("alternating", "no_alternation", "normal", "B04"),
        ("conveyor", "reverse_start", "normal", "C01-delay"),
        ("conveyor", "auto_restart", "fault", "C04"),
    ],
)
def test_each_intentional_defect(case, variant, scenario, requirement):
    result = verify(
        (ROOT / case / "defects" / f"{variant}.st").read_text(),
        (ROOT / case / f"{scenario}.yaml").read_text(encoding="utf-8"),
    )
    assert result["error"] is None
    assert result["status"] == "FAIL"
    assert next(r for r in result["requirements"] if r["id"] == requirement)["status"] == "FAIL"


SOURCE = "PROGRAM P VAR_INPUT A : BOOL; END_VAR VAR_OUTPUT Q : BOOL; END_VAR Q := A; END_PROGRAM"


def config(requirements, **kwargs):
    data = dict(
        id="test",
        description="Independent assertions",
        program="p.st",
        duration_ms=400,
        scan_ms=100,
        requirements=requirements,
        **kwargs,
    )
    return yaml.safe_dump(data)


def req(kind, **kwargs):
    return dict(id="R1", description="Reference assertion", kind=kind, **kwargs)


def test_repeated_trace_and_hashes():
    text = config([req("always", expr="Q = A")], events=[dict(scan=1, set={"A": True})])
    assert verify(SOURCE, text) == verify(SOURCE, text)


@pytest.mark.parametrize(
    "requirement",
    [
        req("response", trigger="A", expr="Q", within_ms=100),
        req("never", when="A", expr="Q"),
        req("latch", trigger="A", expr="Q", until="NOT A"),
        req("sequence", steps=["A", "NOT A"]),
    ],
)
def test_vacuity(requirement):
    result = verify(SOURCE, config([requirement]))
    # Sequence's second step at t=0 is an actual order violation, not a missing trigger.
    assert result["status"] == ("FAIL" if requirement["kind"] == "sequence" else "NOT_EVALUATED")


def test_deadline_beyond_observation_is_not_pass():
    text = config([req("response", trigger="A", expr="NOT Q", within_ms=1000)], initial={"A": True})
    assert verify(SOURCE, text)["status"] == "NOT_EVALUATED"


def test_response_late_and_exact_deadline():
    source = SOURCE.replace("Q := A;", "Q := FALSE;")
    text = config([req("response", trigger="A", expr="Q", within_ms=100)], initial={"A": True})
    result = verify(source, text)
    assert result["requirements"][0]["first_failure_scan"] == 1
    source = (
        "PROGRAM P VAR_INPUT A, B : BOOL; END_VAR VAR_OUTPUT Q : BOOL; END_VAR Q := B; END_PROGRAM"
    )
    text = config(
        [req("response", trigger="A", expr="Q", within_ms=100)],
        initial={"A": True},
        events=[dict(scan=1, set={"B": True})],
    )
    assert verify(source, text)["status"] == "PASS"


@pytest.mark.parametrize("bad", ["id: x\nid: y", "x: &a [*a]", "!!python/object:foo {}"])
def test_yaml_rejected(bad):
    assert verify(SOURCE, bad)["status"] == "ERROR"


def test_bad_event_and_empty_requirements():
    assert verify(SOURCE, config([]))["status"] == "ERROR"
    text = config([req("always", expr="TRUE")], events=[dict(scan=0, set={"Q": True})])
    result = verify(SOURCE, text)
    assert result["status"] == "ERROR"
    assert result["requirements"][0]["status"] == "NOT_EVALUATED"


def test_timeout_and_cancel():
    text = config([req("always", expr="TRUE")])
    assert verify(SOURCE, text, timeout_s=0)["status"] == "ERROR"
    assert verify(SOURCE, text, cancelled=lambda: True)["status"] == "ERROR"


def test_runtime_error_does_not_approve_requirements():
    source = "PROGRAM P VAR X : INT; END_VAR X := 1 / 0; END_PROGRAM"
    result = verify(source, config([req("always", expr="TRUE")]))
    assert result["status"] == "ERROR"
    assert result["trace"] == []
    assert result["requirements"][0]["status"] == "NOT_EVALUATED"
