"""Record installed distribution versions and declared license metadata."""

import importlib.metadata
from pathlib import Path

rows = [
    "# Inventario de dependencias",
    "",
    "Versiones instaladas para validación local. Resolución completa y hashes en uv.lock.",
    "Licencias tomadas del metadata de distribución; no sustituye revisar sus textos.",
    "",
    "| Paquete | Versión | Licencia declarada |",
    "| --- | --- | --- |",
]
for dist in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata["Name"].lower()):
    if dist.metadata["Name"] == "plc-logic-verifier":
        continue
    license = dist.metadata.get("License-Expression") or dist.metadata.get("License")
    if not license:
        license = (
            "; ".join(
                c.split(" :: ")[-1]
                for c in dist.metadata.get_all("Classifier", [])
                if c.startswith("License ::")
            )
            or "No declarada en metadata"
        )
    license = license.splitlines()[0].replace("|", "/")[:150]
    rows.append(f"| {dist.metadata['Name']} | {dist.version} | {license} |")
rows += [
    "",
    "Lark/PyYAML/Pydantic son dependencias de ejecución; OpenAI y su transporte son opcionales.",
    "Pytest, Ruff, Mypy y tipos se usan en desarrollo/CI. No se redistribuye MatIEC.",
    "El repositorio privado no concede una licencia de distribución del proyecto; su publicación/licencia futura queda a decisión del propietario.",
]
Path(__file__).resolve().parents[1].joinpath("docs/DEPENDENCIES.md").write_text(
    "\n".join(rows) + "\n", encoding="utf-8"
)
