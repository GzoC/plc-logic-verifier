import pytest

from plc_verifier.engine import Engine
from plc_verifier.language import VerificationError, parse_program


def program(body, variables="X : INT;", inputs="", outputs=""):
    return parse_program(
        f"PROGRAM Test VAR {variables} END_VAR {inputs} {outputs} {body} END_PROGRAM"
    )


def test_order_persistence_and_images():
    p = program(
        "X := X + 1; Y := X + A;",
        inputs="VAR_INPUT A : INT; END_VAR",
        outputs="VAR_OUTPUT Y : INT; END_VAR",
    )
    e = Engine(p)
    a = e.step({"A": 4})
    b = e.step({"A": 7})
    assert a["outputs"] == {"Y": 5}
    assert b["outputs"] == {"Y": 9}
    assert a["inputs"] == {"A": 4}  # Frozen image, no reference aliasing.
    assert (a["time_ms"], b["time_ms"]) == (0, 100)


@pytest.mark.parametrize(
    "pt,table",
    [
        (0, [(0, True), (0, True), (0, True), (0, True)]),
        (200, [(0, False), (100, False), (200, True), (200, True)]),
        (250, [(0, False), (100, False), (200, False), (250, True)]),
    ],
)
def test_ton_reference_table(pt, table):
    p = program(f"T(IN := TRUE, PT := T#{pt}ms);", "T : TON;")
    e = Engine(p)
    actual = [(r["blocks"]["T"]["ET"], r["blocks"]["T"]["Q"]) for r in [e.step() for _ in table]]
    assert actual == table


def test_ton_reset_independence_dynamic_pt_and_skip():
    p = program(
        "IF Call THEN T(IN := On, PT := Delay); END_IF; U(IN := TRUE, PT := T#0ms);",
        "T, U : TON;",
        "VAR_INPUT Call, On : BOOL; Delay : TIME; END_VAR",
    )
    e = Engine(p)
    assert e.step({"Call": True, "On": True, "Delay": 100})["blocks"]["T"]["ET"] == 0
    assert e.step()["blocks"]["T"]["Q"] is True
    assert e.step({"Delay": 400})["blocks"]["T"]["Q"] is False
    assert e.step({"Call": False})["blocks"]["T"]["ET"] == 200
    assert e.step({"Call": True})["blocks"]["T"]["ET"] == 400
    blocks = e.step({"On": False})["blocks"]
    assert blocks["T"]["ET"] == 0 and not blocks["T"]["Q"]
    assert blocks["U"]["Q"]
    assert e.step({"On": True})["blocks"]["T"]["ET"] == 0


def test_edges_initial_independent_and_skipped():
    p = program(
        "IF Call THEN R(CLK := A); END_IF; S(CLK := B);",
        "R, S : R_TRIG;",
        "VAR_INPUT A, B, Call : BOOL; END_VAR",
    )
    e = Engine(p)
    table = [
        ({"A": True, "B": False, "Call": True}, (True, False)),
        ({"B": True}, (False, True)),
        ({"Call": False}, (False, False)),
        ({"Call": True, "A": False}, (False, False)),
        ({"A": True}, (True, False)),
    ]
    for inputs, expected in table:
        row = e.step(inputs)["blocks"]
        assert (row["R"]["Q"], row["S"]["Q"]) == expected


@pytest.mark.parametrize(
    "source,status",
    [
        ("PROGRAM P VAR X : REAL; END_VAR END_PROGRAM", "UNSUPPORTED"),
        ("PROGRAM P Missing := 1; END_PROGRAM", "ERROR"),
        ("PROGRAM P VAR X : BOOL; END_VAR X := 1; END_PROGRAM", "ERROR"),
        ("PROGRAM P WHILE TRUE DO END_WHILE; END_PROGRAM", "UNSUPPORTED"),
        ("PROGRAM P VAR_INPUT X : INT; END_VAR X := 1; END_PROGRAM", "ERROR"),
    ],
)
def test_parser_rejects(source, status):
    with pytest.raises(VerificationError) as info:
        parse_program(source)
    assert info.value.status == status
    assert info.value.line >= 1 and info.value.column >= 1


@pytest.mark.parametrize(
    "expr,expected", [("-7 / 3", -2), ("-7 MOD 3", -1), ("-32768", -32768), ("2 + 3 * 4", 14)]
)
def test_arithmetic(expr, expected):
    assert Engine(program(f"X := {expr};")).step()["variables"]["X"] == expected


@pytest.mark.parametrize("body", ["X := 32767 + 1;", "X := 1 / 0;", "X := -32768 / -1;"])
def test_arithmetic_error_rolls_back(body):
    e = Engine(program("X := 5; " + body))
    with pytest.raises(VerificationError):
        e.step()
    assert e.values["X"] == 0 and e.scan == 0


def test_duplicate_call_error():
    with pytest.raises(VerificationError, match="Multiple calls"):
        Engine(program("T(IN := TRUE, PT := T#1s); T(IN := FALSE, PT := T#1s);", "T : TON;")).step()


def test_if_case_and_locations():
    p = program(
        "IF X = 0 THEN X := 2; ELSIF X = 1 THEN X := 3; ELSE X := 4; END_IF;\n"
        "CASE X OF 1: X := 10; 2, 3: X := 20; ELSE X := 30; END_CASE;"
    )
    e = Engine(p)
    row = e.step()
    assert row["variables"]["X"] == 20
    assert row["writes"]["X"]["line"] == 2
    assert e.step()["variables"]["X"] == 30


def test_limits_and_input_validation():
    with pytest.raises(VerificationError):
        parse_program(" " * 65537)
    with pytest.raises(VerificationError):
        Engine(program(""), scan_ms=0)
    with pytest.raises(VerificationError):
        Engine(program(""), initial={"X": True})
