"""Command line adapter for the shared engine."""

import argparse
import json
import shlex
import sys
from pathlib import Path

from .language import VerificationError, parse_program
from .reports import export, validate_result
from .scenario import load_scenario, prepare, verify

EXIT_CODES = {"PASS": 0, "FAIL": 1, "ERROR": 2, "UNSUPPORTED": 3, "NOT_EVALUATED": 4}


def read_text(path: Path, limit: int = 65536) -> str:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise VerificationError(f"File exceeds {limit} bytes: {path.name}")
    return raw.decode("utf-8-sig")


def inputs(path: Path, override: Path | None = None):
    scenario_text = read_text(path)
    scenario = load_scenario(scenario_text)
    source_path = override or path.parent / scenario.program
    return read_text(source_path), scenario_text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="plc-verifier")
    sub = parser.add_subparsers(dest="command", required=True)
    for verb in ("validate", "run"):
        p = sub.add_parser(verb)
        p.add_argument("path", type=Path)
        p.add_argument("--program", type=Path)
        if verb == "run":
            p.add_argument("--output", type=Path, default=Path("outputs/run"))
    p = sub.add_parser("report")
    p.add_argument("result", type=Path)
    p.add_argument("--output", type=Path, default=Path("outputs/report"))
    p = sub.add_parser("explain")
    p.add_argument("result", type=Path, nargs="?")
    p.add_argument("--include-program", type=Path)
    p.add_argument("--include-comments", action="store_true")
    p.add_argument("--payload", type=Path, default=Path("outputs/ai-payload.json"))
    p.add_argument("--send", action="store_true")
    p = sub.add_parser("serve")
    p.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            from .web import serve
            serve(args.port)
            return 0
        if args.command == "validate":
            if args.path.suffix.lower() == ".st":
                from .engine import Engine
                Engine(parse_program(read_text(args.path)))
            else:
                source, scenario_text = inputs(args.path, args.program)
                prepare(parse_program(source), load_scenario(scenario_text))
            print("VALID: syntax, types and configuration (requirements NOT_EVALUATED)")
            return 0
        if args.command == "run":
            source, text = inputs(args.path, args.program)
            command = f"plc-verifier run {shlex.quote(str(args.path))}"
            if args.program:
                command += f" --program {shlex.quote(str(args.program))}"
            result = verify(source, text, command)
            export(result, args.output)
            print(f'{result["status"]}: {args.output / "report.html"}')
            for r in result["requirements"]:
                print(f'  {r["id"]}: {r["status"]}')
            if result["error"]:
                print(result["error"]["message"], file=sys.stderr)
            return EXIT_CODES[result["status"]]
        if args.command == "report":
            export(validate_result(json.loads(read_text(args.result, 24 * 1024 * 1024))), args.output)
            print(args.output / "report.html")
            return 0
        if args.command == "explain":
            from .ai import explain, preview_payload
            if args.send:
                advice = explain(json.loads(read_text(args.payload, 24000)), send=True)
                print(json.dumps(advice, ensure_ascii=False, indent=2))
            else:
                if args.result is None:
                    raise VerificationError("Provide a result.json to preview, or --payload ... --send")
                result = validate_result(json.loads(read_text(args.result, 24 * 1024 * 1024)))
                payload = preview_payload(result, read_text(args.include_program) if args.include_program else None,
                                          args.include_comments)
                args.payload.parent.mkdir(parents=True, exist_ok=True)
                args.payload.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"Preview only; nothing sent. Review/edit {args.payload}, then explain --payload <file> --send")
            return 0
    except (VerificationError, OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_CODES[exc.status] if isinstance(exc, VerificationError) else 2
    except KeyboardInterrupt:
        print("Cancelled", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
