"""Strict YAML scenarios and observable, non-vacuous requirement evaluation."""

import hashlib
import json
import time
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import __version__
from .engine import Engine, evaluate
from .language import Program, VerificationError, parse_expression, parse_program

NOTICE = "Verificación por simulación con alcance definido. No certifica seguridad funcional ni compatibilidad universal con PLC"
SEMANTICS = {"version": "0.1.0", "scan": "inputs -> sequential execution -> outputs/assertions -> clock advance",
             "duration": "[0,duration_ms)", "INT": "signed 16 bit; overflow ERROR; division toward zero",
             "TIME": "0..2147483647 integer ms", "TON": "first true call ET=0; ET=min(now-start,PT); Q=ET>=PT; false resets; skipped holds; PT changes keep start",
             "R_TRIG": "initial memory FALSE; Q cleared each scan; memory updated only on call",
             "multiple_calls": "ERROR", "retention": "between scans only; new run resets"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Event(StrictModel):
    scan: int | None = Field(default=None, ge=0)
    time_ms: int | None = Field(default=None, ge=0)
    set: dict[str, bool | int]

    @model_validator(mode="after")
    def one_time(self):
        if (self.scan is None) == (self.time_ms is None):
            raise ValueError("Event needs exactly one of scan/time_ms")
        if not self.set:
            raise ValueError("Empty event")
        return self


class Requirement(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=1000)
    kind: Literal["always", "never", "eventually", "hold", "mutex", "sequence", "response", "latch"]
    expr: str | None = Field(default=None, max_length=2000)
    when: str | None = Field(default=None, max_length=2000)
    trigger: str | None = Field(default=None, max_length=2000)
    until: str | None = Field(default=None, max_length=2000)
    steps: list[str] | None = Field(default=None, min_length=2, max_length=16)
    start_ms: int = Field(default=0, ge=0)
    end_ms: int | None = Field(default=None, ge=0)
    within_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def shape(self):
        allowed = {"always": {"expr", "when"}, "never": {"expr", "when"},
                   "eventually": {"expr", "when"}, "hold": {"expr", "when"},
                   "mutex": {"steps", "when"}, "sequence": {"steps"},
                   "response": {"trigger", "expr", "within_ms"},
                   "latch": {"trigger", "expr", "until"}}[self.kind]
        required = allowed - {"when"}
        for name in {"expr", "when", "trigger", "until", "steps", "within_ms"}:
            v = getattr(self, name)
            if (name in required and v is None) or (name not in allowed and v is not None):
                raise ValueError(f"Invalid {name} for {self.kind}")
        if self.kind == "hold" and self.end_ms is None:
            raise ValueError("hold requires an explicit end_ms")
        return self


class Scenario(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=2000)
    program: str = Field(min_length=1, max_length=500)
    duration_ms: int = Field(gt=0, le=3600000)
    scan_ms: int = Field(gt=0, le=60000)
    initial: dict[str, bool | int] = Field(default_factory=dict)
    events: list[Event] = Field(default_factory=list, max_length=10000)
    requirements: list[Requirement] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def timing(self):
        if self.duration_ms % self.scan_ms or self.duration_ms // self.scan_ms > 10000:
            raise ValueError("Duration must be scan-aligned, at most 10000 scans")
        ids = [r.id for r in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate requirement IDs")
        seen = set()
        for e in self.events:
            t = e.time_ms if e.time_ms is not None else int(e.scan or 0) * self.scan_ms
            if t >= self.duration_ms or t % self.scan_ms or t in seen:
                raise ValueError("Events must be unique, scan-aligned and inside duration")
            seen.add(t)
        for r in self.requirements:
            end = self.duration_ms - self.scan_ms if r.end_ms is None else r.end_ms
            if r.start_ms > end or end >= self.duration_ms or r.start_ms % self.scan_ms or end % self.scan_ms:
                raise ValueError("Requirement windows must be scan-aligned and inside duration")
        return self


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_scenario(source: str) -> Scenario:
    if len(source.encode()) > 65536:
        raise VerificationError("Scenario exceeds 64 KiB")
    try:
        depth = 0
        for token in yaml.scan(source):
            if isinstance(token, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)):
                raise ValueError("YAML aliases/anchors are not supported")
            if isinstance(token, (yaml.tokens.BlockMappingStartToken, yaml.tokens.BlockSequenceStartToken,
                                  yaml.tokens.FlowMappingStartToken, yaml.tokens.FlowSequenceStartToken)):
                depth += 1
            if isinstance(token, (yaml.tokens.BlockEndToken, yaml.tokens.FlowMappingEndToken,
                                  yaml.tokens.FlowSequenceEndToken)):
                depth -= 1
            if depth > 20:
                raise ValueError("YAML nesting limit exceeded")
        return Scenario.model_validate(yaml.load(source, Loader=UniqueLoader))
    except (ValueError, yaml.YAMLError, RecursionError) as exc:
        raise VerificationError(f"Invalid scenario: {exc}") from exc


def prepare(program: Program, scenario: Scenario) -> dict[str, dict[str, Any]]:
    engine = Engine(program, scenario.scan_ms, scenario.initial)
    for event in scenario.events:
        engine.set_values(event.set)
    compiled = {}
    for r in scenario.requirements:
        compiled[r.id] = {name: parse_expression(getattr(r, name), program)
                          for name in ("expr", "when", "trigger", "until") if getattr(r, name) is not None}
        if r.steps:
            compiled[r.id]["steps"] = [parse_expression(s, program) for s in r.steps]
    return compiled


def values_of(row):
    return {**row["inputs"], **row["outputs"], **row["variables"], **row["blocks"]}


def assess(r: Requirement, nodes: dict[str, Any], trace: list[dict[str, Any]], program: Program):
    window = [row for row in trace if row["time_ms"] >= r.start_ms and
              (r.end_ms is None or row["time_ms"] <= r.end_ms)]
    failures = []
    observations = 0
    satisfied = False
    previous_trigger = False
    deadlines: list[int] = []
    latched = False
    released = False
    index = 0
    previous_steps = [False] * len(nodes.get("steps", []))
    for row in window:
        values = values_of(row)
        def ev(name, values=values):
            return evaluate(nodes[name], values, program)
        if "when" in nodes and not ev("when"):
            row["assertions"].append({"id": r.id, "status": "NOT_EVALUATED", "reason": "when false"})
            continue
        ok: bool | None = True
        if r.kind in {"always", "hold", "never", "eventually"}:
            observations += 1
            actual = ev("expr")
            ok = not actual if r.kind == "never" else actual
            if r.kind == "eventually":
                satisfied |= actual
                ok = True if actual else None
        elif r.kind == "mutex":
            observations += 1
            ok = sum(evaluate(s, values, program) for s in nodes["steps"]) <= 1
        elif r.kind == "sequence":
            if satisfied:
                row["assertions"].append({"id": r.id, "status": "NOT_EVALUATED", "reason": "Sequence already completed"})
                continue
            current = [evaluate(s, values, program) for s in nodes["steps"]]
            rising = [i for i, v in enumerate(current) if v and not previous_steps[i]]
            if len(rising) > 1:
                ok = False
            for i in rising:
                if i == index:
                    observations += 1
                    index += 1
                else:
                    ok = False
            previous_steps = current
            satisfied = index == len(current)
            if not rising:
                ok = None
        else:
            trigger = ev("trigger")
            if trigger and not previous_trigger:
                observations += 1
                if r.kind == "response":
                    deadlines.append(row["time_ms"] + int(r.within_ms or 0))
                else:
                    latched = True
            previous_trigger = trigger
            if observations == 0:
                ok = None
            if r.kind == "response":
                # A response at the deadline is valid; one after it cannot erase failure.
                expired = [d for d in deadlines if row["time_ms"] > d]
                if expired:
                    ok = False
                deadlines = [d for d in deadlines if d >= row["time_ms"]]
                if ev("expr"):
                    deadlines.clear()
                elif any(d == row["time_ms"] for d in deadlines):
                    ok = False
                    deadlines = [d for d in deadlines if d != row["time_ms"]]
            else:
                if latched and ev("until"):
                    latched, released = False, True
                if latched:
                    ok = ev("expr")
        row["assertions"].append({"id": r.id, "status": "FAIL" if ok is False else
                                   "PASS" if ok is True else "NOT_EVALUATED"})
        if ok is False:
            failures.append(row)
    reason = "Requirement satisfied in observed window"
    status = "PASS"
    if failures:
        status, reason = "FAIL", "Observed requirement violation"
    elif not observations:
        status, reason = "NOT_EVALUATED", "No eligible sample or trigger occurred"
    elif r.kind == "eventually" and not satisfied:
        status, reason = "FAIL", "Expression never true in window"
        failures = window[-1:]
    elif r.kind == "sequence" and not satisfied:
        status, reason = "FAIL", "Sequence did not complete in window"
        failures = window[-1:]
    elif deadlines:
        status, reason = "NOT_EVALUATED", "Response deadline exceeds observed window"
    first = failures[0] if failures else None
    return {"id": r.id, "description": r.description, "kind": r.kind, "status": status,
            "expected": r.model_dump(exclude_none=True), "reason": reason,
            "observations": observations, "first_failure_scan": first["scan"] if first else None,
            "observed": values_of(first) if first else None,
            "related_writes": first["writes"] if first else {},
            "evidence_scans": [max(0, first["scan"] - 2), min(len(trace) - 1, first["scan"] + 2)] if first else None,
            "notes": "Last executed writes are evidence, not proof of root cause.",
            "release_observed": released if r.kind == "latch" else None}


def verify(source: str, scenario_source: str, command: str = "plc-verifier run <scenario.yml>",
           timeout_s: float = 10.0, cancelled=None) -> dict[str, Any]:
    result: dict[str, Any] = {"schema_version": 1, "engine_version": __version__, "status": "ERROR",
                              "notice": NOTICE, "semantics": SEMANTICS,
                              "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
                              "scenario_sha256": hashlib.sha256(scenario_source.encode()).hexdigest(),
                              "reproduce": command, "requirements": [], "trace": [], "error": None}
    scenario = None
    try:
        scenario = load_scenario(scenario_source)
        result["scenario"] = scenario.model_dump()
        program = parse_program(source)
        compiled = prepare(program, scenario)
        engine = Engine(program, scenario.scan_ms, scenario.initial)
        events = {(e.scan if e.scan is not None else int(e.time_ms or 0) // scenario.scan_ms): e.set
                  for e in scenario.events}
        start = time.monotonic()
        size = 0
        for scan in range(scenario.duration_ms // scenario.scan_ms):
            if time.monotonic() - start >= timeout_s or (cancelled and cancelled()):
                raise VerificationError("Execution timeout or cancellation")
            row = engine.step(events.get(scan, {}))
            size += len(json.dumps(row)) + len(scenario.requirements) * 160
            if size > 16 * 1024 * 1024:
                raise VerificationError("Trace exceeds 16 MiB budget")
            result["trace"].append(row)
        for r in scenario.requirements:
            if time.monotonic() - start > timeout_s:
                raise VerificationError("Requirement evaluation timeout")
            result["requirements"].append(assess(r, compiled[r.id], result["trace"], program))
        statuses = {r["status"] for r in result["requirements"]}
        result["status"] = "FAIL" if "FAIL" in statuses else "NOT_EVALUATED" if "NOT_EVALUATED" in statuses else "PASS"
    except VerificationError as exc:
        result["status"] = exc.status
        result["error"] = {"message": str(exc), "line": exc.line, "column": exc.column}
        if scenario:
            result["requirements"] = [{"id": r.id, "description": r.description,
                                        "status": "NOT_EVALUATED", "reason": "Run did not complete"}
                                       for r in scenario.requirements]
    return result
