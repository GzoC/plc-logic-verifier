"""A single bounded verification job on stdin/stdout, invoked only by local UI."""

import json
import sys

from .scenario import verify


def main():
    raw = sys.stdin.read(150000)
    request = json.loads(raw)
    result = verify(
        request["source"],
        request["scenario"],
        "Save uploaded ST as program.st and YAML as scenario.yaml; plc-verifier run scenario.yaml --program program.st",
    )
    sys.stdout.write(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
