"""Regenerate evidence by executing current sources, with expected mutant outcomes."""

import argparse
import json
from pathlib import Path

from plc_verifier.reports import export
from plc_verifier.scenario import verify

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    out = parser.parse_args().output
    summary = []
    for case in ("lubrication", "alternating", "conveyor"):
        folder = ROOT / "examples" / case
        for scenario in ("normal", "fault"):
            source_path = folder / "correct.st"
            scenario_path = folder / f"{scenario}.yaml"
            command = f"plc-verifier run {scenario_path.relative_to(ROOT).as_posix()}"
            result = verify(
                source_path.read_text(encoding="utf-8"),
                scenario_path.read_text(encoding="utf-8"),
                command,
            )
            assert result["status"] == "PASS", result
            summary.append(
                {
                    "case": case,
                    "scenario": scenario,
                    "variant": "correct",
                    "status": result["status"],
                    "program_sha256": result["program_sha256"],
                    "scenario_sha256": result["scenario_sha256"],
                }
            )
        for name, scenario, requirement in {
            "lubrication": [("timeout_disabled", "fault", "L03"), ("auto_ack", "fault", "L05")],
            "alternating": [("overlap", "normal", "B02"), ("no_alternation", "normal", "B04")],
            "conveyor": [
                ("reverse_start", "normal", "C01-delay"),
                ("auto_restart", "fault", "C04"),
            ],
        }[case]:
            source_path = folder / "defects" / f"{name}.st"
            scenario_path = folder / f"{scenario}.yaml"
            command = f"plc-verifier run {scenario_path.relative_to(ROOT).as_posix()} --program {source_path.relative_to(ROOT).as_posix()}"
            result = verify(
                source_path.read_text(encoding="utf-8"),
                scenario_path.read_text(encoding="utf-8"),
                command,
            )
            req = next(r for r in result["requirements"] if r["id"] == requirement)
            assert result["status"] == "FAIL" and req["status"] == "FAIL", result
            summary.append(
                {
                    "case": case,
                    "scenario": scenario,
                    "variant": name,
                    "status": result["status"],
                    "detected_by": requirement,
                    "first_failure_scan": req["first_failure_scan"],
                    "program_sha256": result["program_sha256"],
                    "scenario_sha256": result["scenario_sha256"],
                }
            )
            if case == "lubrication" and name == "timeout_disabled":
                export(result, out / "timeout-disabled")
    out.mkdir(exist_ok=True, parents=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"{len(summary)} executions verified: 6 PASS + 6 expected FAIL")


if __name__ == "__main__":
    main()
