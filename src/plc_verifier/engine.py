"""Deterministic scan interpreter. Time is always virtual integer milliseconds."""

from copy import deepcopy
from typing import Any

from .language import Node, Program, VerificationError, expression_type, fail, time_ms

TIME_MAX = 2147483647


def checked(value: Any, typ: str, node: Node) -> Any:
    if typ == "BOOL":
        if type(value) is not bool:
            fail("BOOL value required", node)
    elif type(value) is not int or not ((-32768 <= value <= 32767) if typ == "INT"
                                      else (0 <= value <= TIME_MAX)):
        fail(f"{typ} range exceeded", node)
    return value


def evaluate(node: Node, values: dict[str, Any], program: Program) -> Any:
    k, a = node.kind, node.args
    if k == "integer":
        return checked(int(a[0]), "INT", node)
    if k == "time":
        return checked(time_ms(a[0]), "TIME", node)
    if k == "boolean":
        return a[0] == "TRUE"
    if k == "variable":
        return values[a[0]]
    if k == "member":
        return values[a[0]][a[1]]
    if k == "unary":
        if a[0] == "-" and a[1].kind == "integer":
            return checked(-int(a[1].args[0]), "INT", node)
        v = evaluate(a[1], values, program)
        return (not v) if a[0] == "NOT" else checked(-v if a[0] == "-" else v, "INT", node)
    value = evaluate(a[0], values, program)
    typ = expression_type(a[0], program.symbols)
    for op, right in zip(a[1::2], a[2::2], strict=True):
        r = evaluate(right, values, program)  # Deliberately no short circuit.
        if op == "+":
            value = checked(value + r, typ, node)
        elif op == "-":
            value = checked(value - r, typ, node)
        elif op == "*":
            value = checked(value * r, typ, node)
        elif op in {"/", "MOD"}:
            if r == 0:
                fail("Division by zero", node)
            quotient = (abs(value) // abs(r)) * (-1 if (value < 0) != (r < 0) else 1)
            value = checked(quotient if op == "/" else value - quotient * r, typ, node)
        elif op == "AND":
            value = value and r
        elif op == "OR":
            value = value or r
        elif op == "XOR":
            value = value != r
        elif op == "=":
            value = value == r
        elif op == "<>":
            value = value != r
        elif op == "<":
            value = value < r
        elif op == ">":
            value = value > r
        elif op == "<=":
            value = value <= r
        elif op == ">=":
            value = value >= r
        else:
            fail(f"Unsupported operator {op}", node, "UNSUPPORTED")
    return value


class Engine:
    def __init__(self, program: Program, scan_ms: int = 100,
                 initial: dict[str, Any] | None = None):
        if type(scan_ms) is not int or not 1 <= scan_ms <= 60000:
            raise VerificationError("scan_ms must be 1..60000")
        self.program, self.scan_ms = program, scan_ms
        self.scan, self.time_ms = 0, 0
        self.values: dict[str, Any] = {}
        self.writes: dict[str, dict[str, int]] = {}
        for name, symbol in program.symbols.items():
            if symbol.type == "TON":
                value: Any = {"IN": False, "PT": 0, "ET": 0, "Q": False, "start_ms": None}
            elif symbol.type == "R_TRIG":
                value = {"CLK": False, "Q": False, "memory": False}
            else:
                value = False if symbol.type == "BOOL" else 0
                if symbol.initial:
                    value = evaluate(symbol.initial, {}, program)
            self.values[name] = value
        self.set_values(initial or {}, inputs_only=False)

    def set_values(self, updates: dict[str, Any], inputs_only: bool = True) -> None:
        canonical = [name.upper() for name in updates]
        if len(set(canonical)) != len(canonical):
            raise VerificationError("Duplicate case-insensitive names")
        for raw, value in updates.items():
            name = raw.upper()
            symbol = self.program.symbols.get(name)
            if symbol is None or symbol.type in {"TON", "R_TRIG"}:
                raise VerificationError(f"Invalid scalar variable {raw}")
            if inputs_only and symbol.section != "VAR_INPUT":
                raise VerificationError(f"Input event cannot write {raw}")
            checked(value, symbol.type, Node("external", line=symbol.line, column=symbol.column))
        for raw, value in updates.items():
            self.values[raw.upper()] = value

    def step(self, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        self.set_values(inputs or {})
        before = deepcopy(self.values)
        previous_writes = self.writes.copy()
        self.called: set[str] = set()
        for symbol in self.program.symbols.values():
            if symbol.type == "R_TRIG":
                self.values[symbol.name]["Q"] = False
        try:
            self.execute(self.program.body)
        except VerificationError:
            self.values, self.writes = before, previous_writes
            raise
        row: dict[str, Any] = {"scan": self.scan, "time_ms": self.time_ms,
                               "inputs": {}, "outputs": {}, "variables": {}, "blocks": {},
                               "writes": deepcopy(self.writes), "assertions": []}
        for name, symbol in self.program.symbols.items():
            group = ("blocks" if symbol.type in {"TON", "R_TRIG"} else
                     {"VAR_INPUT": "inputs", "VAR_OUTPUT": "outputs", "VAR": "variables"}[symbol.section])
            row[group][name] = deepcopy(self.values[name])
        self.scan += 1
        self.time_ms += self.scan_ms
        return row

    def execute(self, node: Node) -> None:
        k, a = node.kind, node.args
        if k == "statements":
            for child in a:
                self.execute(child)
        elif k == "assign":
            self.values[a[0]] = evaluate(a[1], self.values, self.program)
            self.writes[a[0]] = {"line": node.line, "column": node.column, "scan": self.scan}
        elif k == "invoke":
            name = a[0]
            if name in self.called:
                fail(f"Multiple calls per scan to {name}", node)
            self.called.add(name)
            block = self.values[name]
            args = {arg.args[0]: evaluate(arg.args[1], self.values, self.program) for arg in a[1:]}
            block.update(args)
            if self.program.symbols[name].type == "TON":
                if not block["IN"]:
                    block.update(ET=0, Q=False, start_ms=None)
                else:
                    if block["start_ms"] is None:
                        block["start_ms"] = self.time_ms
                    block["ET"] = min(self.time_ms - block["start_ms"], block["PT"])
                    block["Q"] = block["ET"] >= block["PT"]
            else:
                block["Q"] = block["CLK"] and not block["memory"]
                block["memory"] = block["CLK"]
            self.writes[name] = {"line": node.line, "column": node.column, "scan": self.scan}
        elif k == "if_stmt":
            i = 0
            while i + 1 < len(a):
                if evaluate(a[i], self.values, self.program):
                    self.execute(a[i + 1])
                    return
                i += 2
            if i < len(a):
                self.execute(a[i])
        elif k == "case_stmt":
            value = evaluate(a[0], self.values, self.program)
            for arm in a[1:]:
                if arm.kind == "statements":
                    self.execute(arm)
                    return
                if value in [int(v) for v in arm.args[0].args]:
                    self.execute(arm.args[1])
                    return
        else:
            fail(f"Unsupported statement {k}", node, "UNSUPPORTED")
