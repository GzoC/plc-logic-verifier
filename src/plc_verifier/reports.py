"""Escaped, self-contained reports derived exclusively from saved engine results."""

import csv
import html
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from .limits import FORMAT_BYTES, bounded, compact
from .result_schema import validate_result


def json_report(result):
    return bounded(compact(validate_result(result)), FORMAT_BYTES["json"], "Result JSON")


def csv_report(result):
    rows = []
    for row in result["trace"]:
        flat = {"scan": row["scan"], "time_ms": row["time_ms"]}
        for group in ("inputs", "outputs", "variables", "blocks"):
            for name, value in row[group].items():
                if isinstance(value, dict):
                    for member, v in value.items():
                        flat[f"{group}.{name}.{member}"] = v
                else:
                    flat[f"{group}.{name}"] = value
        flat["assertions"] = json.dumps(row.get("assertions", []), ensure_ascii=False)
        flat["writes"] = json.dumps(row.get("writes", {}))
        rows.append(flat)
    fields = list(dict.fromkeys(k for row in rows for k in row)) or ["scan", "time_ms"]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return bounded(out.getvalue(), FORMAT_BYTES["csv"], "CSV")


def junit_report(result):
    cases = list(result["requirements"])
    if result["status"] in {"ERROR", "UNSUPPORTED"} or not cases:
        cases.append(
            {"id": "engine", "status": result["status"], "reason": str(result.get("error"))}
        )
    suite = ET.Element(
        "testsuite",
        name=result.get("scenario", {}).get("id", "PLC Logic Verifier"),
        tests=str(len(cases)),
        failures=str(sum(r["status"] == "FAIL" for r in cases)),
        errors=str(sum(r["status"] in {"ERROR", "UNSUPPORTED"} for r in cases)),
        skipped=str(sum(r["status"] == "NOT_EVALUATED" for r in cases)),
    )
    for r in cases:
        case = ET.SubElement(suite, "testcase", name=r["id"], classname="plc.requirement")
        kind = {
            "FAIL": "failure",
            "ERROR": "error",
            "UNSUPPORTED": "error",
            "NOT_EVALUATED": "skipped",
        }.get(r["status"])
        if kind:
            item = ET.SubElement(case, kind, message=r.get("reason", r["status"]))
            item.text = json.dumps(r, ensure_ascii=False)
    return bounded(
        ET.tostring(suite, encoding="unicode", xml_declaration=True),
        FORMAT_BYTES["xml"],
        "JUnit XML",
    )


def html_report(result):
    def esc(v):
        return html.escape(str(v))

    def pretty(v):
        return esc(json.dumps(v, ensure_ascii=False, indent=2))

    requirements = []
    for r in result["requirements"]:
        evidence = ""
        if r.get("evidence_scans"):
            low, high = r["evidence_scans"]
            evidence = f"<h4>Ventana de evidencia: scans {low}–{high}</h4><pre>{pretty(result['trace'][low : high + 1])}</pre>"
        requirements.append(
            f"<article><h3>{esc(r['id'])} · {esc(r['status'])}</h3><p>{esc(r.get('description', ''))}</p><pre>{pretty(r)}</pre>{evidence}</article>"
        )
    page = f"""<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>PLC Logic Verifier · {esc(result["status"])}</title><style>
body{{font:16px system-ui;margin:40px auto;max-width:1100px;padding:0 24px;color:#172b35;background:#f5f6f3}}
h1{{font-size:32px}}article,details{{background:white;padding:20px;margin:16px 0;border:1px solid #d2dbd6;border-radius:8px}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:13px ui-monospace,monospace}}.notice{{border-left:5px solid #d26b26;padding:16px;background:#fff1dc}}
</style><h1>PLC Logic Verifier</h1><h2>Resultado: {esc(result["status"])}</h2>
<p class="notice">{esc(result["notice"])}</p><p>Escenarios observados, no prueba formal exhaustiva. No sustituye FAT, SAT ni revisión de ingeniería.</p>
<p>Motor {esc(result["engine_version"])} · esquema {esc(result["schema_version"])}</p>
<pre>Programa SHA-256: {esc(result["program_sha256"])}\nEscenario SHA-256: {esc(result["scenario_sha256"])}\nReproducir: {esc(result["reproduce"])}</pre>
<h2>Alcance y semántica</h2><pre>{pretty(result["semantics"])}</pre>
<details><summary>Configuración del escenario</summary><pre>{pretty(result.get("scenario"))}</pre></details>
<h2>Requisitos y evidencia</h2>{"".join(requirements)}<pre>{pretty(result.get("error"))}</pre>
<details><summary>Traza completa ({len(result["trace"])} scans)</summary><pre>{pretty(result["trace"])}</pre></details>
<p>Las ubicaciones son últimas escrituras ejecutadas; una causa raíz requiere revisión. No hay conclusiones de IA en este informe determinista.</p></html>"""
    return bounded(page, FORMAT_BYTES["html"], "HTML")


def export(result, folder: Path):
    validate_result(result)
    contents = {
        "result.json": json_report(result),
        "trace.csv": csv_report(result),
        "report.html": html_report(result),
        "junit.xml": junit_report(result),
    }
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in contents.items():
        (folder / name).write_text(content, encoding="utf-8", newline="")
