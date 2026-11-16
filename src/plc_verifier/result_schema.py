"""Version 1 result contract. Structural consistency is not authenticity."""

from typing import Annotated, Literal

from pydantic import Field, ValidationError, model_validator

from .language import VerificationError
from .limits import RESULT_BYTES, bounded, compact
from .scenario import Requirement, Scenario, StrictModel

Status = Literal["PASS", "FAIL", "ERROR", "UNSUPPORTED", "NOT_EVALUATED"]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Scalar = bool | Annotated[int, Field(ge=-32768, le=2147483647)]


class Position(StrictModel):
    line: int = Field(ge=1)
    column: int = Field(ge=1)
    scan: int = Field(ge=0)


class Timer(StrictModel):
    IN: bool
    PT: int = Field(ge=0, le=2147483647)
    ET: int = Field(ge=0, le=2147483647)
    Q: bool
    start_ms: int | None = Field(ge=0)

    @model_validator(mode="after")
    def elapsed(self):
        if self.ET > self.PT:
            raise ValueError("ET exceeds PT")
        return self


class Edge(StrictModel):
    CLK: bool
    Q: bool
    memory: bool


class Assertion(StrictModel):
    id: str
    status: Literal["PASS", "FAIL", "NOT_EVALUATED"]
    reason: str | None = None


class Row(StrictModel):
    scan: int = Field(ge=0)
    time_ms: int = Field(ge=0)
    inputs: dict[str, Scalar]
    outputs: dict[str, Scalar]
    variables: dict[str, Scalar]
    blocks: dict[str, Timer | Edge]
    writes: dict[str, Position]
    assertions: list[Assertion] = Field(max_length=100)


class ExecutionError(StrictModel):
    message: str
    line: int = Field(ge=1)
    column: int = Field(ge=1)


class Semantics(StrictModel):
    version: str
    scan: str
    duration: str
    INT: str
    TIME: str
    TON: str
    R_TRIG: str
    multiple_calls: str
    retention: str


class RequirementResult(StrictModel):
    id: str = Field(min_length=1, max_length=80)
    description: str
    status: Literal["PASS", "FAIL", "NOT_EVALUATED"]
    reason: str
    kind: str | None = None
    expected: Requirement | None = None
    observations: int | None = Field(default=None, ge=0)
    first_failure_scan: int | None = Field(default=None, ge=0)
    observed: dict[str, Scalar | Timer | Edge] | None = None
    related_writes: dict[str, Position] | None = None
    evidence_scans: list[int] | None = Field(default=None, min_length=2, max_length=2)
    notes: str | None = None
    release_observed: bool | None = None


class ResultV1(StrictModel):
    schema_version: Literal[1]
    engine_version: str = Field(min_length=1)
    status: Status
    notice: str = Field(min_length=1)
    semantics: Semantics
    program_sha256: Hash
    scenario_sha256: Hash
    reproduce: str
    scenario: Scenario | None = None
    requirements: list[RequirementResult] = Field(max_length=100)
    trace: list[Row] = Field(max_length=10000)
    error: ExecutionError | None

    @model_validator(mode="after")
    def consistent(self):
        aborted = self.status in {"ERROR", "UNSUPPORTED"}
        if aborted != (self.error is not None):
            raise ValueError("Execution error and global status disagree")
        if self.scenario is None:
            if not aborted or self.trace or self.requirements:
                raise ValueError("Missing scenario outside an early configuration error")
            return self
        if [r.id for r in self.requirements] != [r.id for r in self.scenario.requirements]:
            raise ValueError("Requirements do not match scenario IDs/order")
        total = self.scenario.duration_ms // self.scenario.scan_ms
        if len(self.trace) > total or (not aborted and len(self.trace) != total):
            raise ValueError("Incomplete or excessive trace")
        ids = {r.id for r in self.requirements}
        for i, row in enumerate(self.trace):
            if row.scan != i or row.time_ms != i * self.scenario.scan_ms:
                raise ValueError("Trace scan/time sequence invalid")
            names = [
                n for group in (row.inputs, row.outputs, row.variables, row.blocks) for n in group
            ]
            if len(set(names)) != len(names) or len(names) > 128:
                raise ValueError("Invalid trace variable groups")
            for name, pos in row.writes.items():
                if name not in names or pos.scan > i:
                    raise ValueError("Invalid write location")
            aids = [a.id for a in row.assertions]
            if len(aids) != len(set(aids)) or not set(aids) <= ids:
                raise ValueError("Invalid trace assertion IDs")
        for r, definition in zip(self.requirements, self.scenario.requirements, strict=True):
            if r.description != definition.description:
                raise ValueError("Requirement description disagrees with scenario")
            if aborted:
                if r.status != "NOT_EVALUATED" or r.first_failure_scan is not None:
                    raise ValueError("Aborted run cannot approve/fail requirements")
                continue
            if r.expected != definition or r.kind != definition.kind or r.observations is None:
                raise ValueError("Missing or contradictory requirement metadata")
            if (
                not {
                    "observed",
                    "related_writes",
                    "evidence_scans",
                    "notes",
                    "release_observed",
                    "first_failure_scan",
                }
                <= r.model_fields_set
            ):
                raise ValueError("Incomplete evaluated requirement")
            if r.status == "PASS" and r.observations == 0:
                raise ValueError("PASS without observations")
            if r.status != "FAIL" and any(
                a.id == r.id and a.status == "FAIL" for row in self.trace for a in row.assertions
            ):
                raise ValueError("Requirement status contradicts trace assertions")
            if r.status == "FAIL":
                n, interval = r.first_failure_scan, r.evidence_scans
                if (
                    n is None
                    or interval is None
                    or not 0 <= interval[0] <= n <= interval[1] < len(self.trace)
                ):
                    raise ValueError("Invalid failure evidence indices")
                row = self.trace[n]
                observed = {**row.inputs, **row.outputs, **row.variables, **row.blocks}
                if r.observed != observed or r.related_writes != row.writes:
                    raise ValueError("Failure evidence disagrees with trace")
            elif (
                r.first_failure_scan is not None
                or r.evidence_scans is not None
                or r.observed is not None
            ):
                raise ValueError("Non-failed requirement has failure evidence")
        if not aborted:
            states = {r.status for r in self.requirements}
            expected = (
                "FAIL"
                if "FAIL" in states
                else "NOT_EVALUATED"
                if "NOT_EVALUATED" in states
                else "PASS"
            )
            if self.status != expected:
                raise ValueError("Global status contradicts requirement statuses")
        return self


def validate_result(result):
    try:
        if (
            not isinstance(result, dict)
            or type(result.get("schema_version")) is not int
            or result["schema_version"] != 1
        ):
            raise ValueError("Unsupported result schema_version (expected 1)")
        bounded(compact(result), RESULT_BYTES, "Result JSON")
        ResultV1.model_validate(result)
    except (ValidationError, ValueError, TypeError, RecursionError) as exc:
        # Bound diagnostics: never dump an entire imported trace in an exception.
        if isinstance(exc, ValidationError):
            first = exc.errors(include_input=False, include_url=False)[0]
            message = f"{first['loc']}: {first['msg']}"
        else:
            message = str(exc)
        raise VerificationError(f"Invalid result: {message}") from exc
    return result
