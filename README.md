# PLC Logic Verifier

Detecta errores de secuencia, temporización e interbloqueo en programas Structured Text
compatibles antes de probarlos en equipos. Ejecuta escenarios con tiempo virtual y
produce evidencia reproducible, sin PLC físico, API key ni servicio externo.

```powershell
uv sync --locked --python 3.12
uv run plc-verifier run examples/lubrication/normal.yaml --output outputs/normal
```

Resultado real observado: **PASS, 16 scans y 5 requisitos**. El mutante que elimina
el timeout de presión produce **FAIL en L03, scan 3, 300 ms**:

```powershell
uv run plc-verifier run examples/lubrication/fault.yaml --program examples/lubrication/defects/timeout_disabled.st --output outputs/defect
```

Ese código de salida `1` es el resultado esperado del verificador. La suite comprueba
que el defecto sea detectado; no representa un fallo de la suite.

**Verificación por simulación con alcance definido. No certifica seguridad funcional ni compatibilidad universal con PLC.**
No sustituye FAT, SAT ni revisión de ingeniería. Los escenarios no demuestran todos
los comportamientos posibles y los ejemplos no implementan funciones de seguridad.

## Instalación y uso

Para la suite necesitas además Node.js 24 (ejecuta el JavaScript real de la interfaz).
Para usar la aplicación necesitas Git y [uv](https://docs.astral.sh/uv/getting-started/installation/).
El repositorio es privado: hace falta acceso concedido por su propietario.

```powershell
git clone https://github.com/GzoC/plc-logic-verifier.git
cd plc-logic-verifier
uv sync --locked --python 3.12
uv run plc-verifier validate examples/lubrication/normal.yaml
uv run plc-verifier serve
```

Abre http://127.0.0.1:8765. El servidor escucha sólo en loopback. Selecciona ejemplos,
carga ST/YAML, ejecuta, examina el primer fallo y los estados TON/R_TRIG, y descarga
JSON, CSV, HTML autocontenido o JUnit. Cierra el servidor con Ctrl+C.

Los mismos comandos funcionan en Linux/macOS con uv. Sin uv, Python 3.12+ puede
instalar el paquete, pero `uv.lock` es la referencia reproducible de dependencias.
No hace falta activar el entorno para usar `uv run`.

## Qué incluye

- Parser Lark con AST localizado y tipos; ejecución sin `eval`/`exec` del usuario.
- BOOL, INT, TIME, IF/ELSIF/ELSE, CASE, TON y R_TRIG independientes.
- YAML estricto y ocho clases de requisitos con detección de evaluaciones vacías.
- Bomba de lubricación, bombas alternadas y transporte; seis escenarios correctos y seis defectos.
- CLI e interfaz sobre el mismo motor; hashes, trazas, ubicaciones e informes.
- Asistente OpenAI opcional con vista previa editable y envío explícito, sin aplicar cambios.

## CLI

```powershell
uv run plc-verifier validate programa.st
uv run plc-verifier validate escenario.yaml --program programa.st
uv run plc-verifier run escenario.yaml --program programa.st --output outputs/mi-prueba
uv run plc-verifier report outputs/mi-prueba/result.json --output outputs/informe
```

| Código | Significado |
| --- | --- |
| 0 | PASS, o validación/exportación realizada sin ejecutar requisitos |
| 1 | FAIL de requisitos |
| 2 | ERROR de configuración, uso, ejecución, timeout o cancelación |
| 3 | UNSUPPORTED: ST no soportado o sintaxis no reconocida |
| 4 | NOT_EVALUATED: observación insuficiente o desencadenante ausente |

`validate` nunca declara requisitos aprobados. Un error de ejecución marca los requisitos
NOT_EVALUATED y conserva únicamente scans publicados antes del error.

## Pruebas

```powershell
uv sync --locked --python 3.12 --all-extras
uv run pytest -q
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run mypy src
uv run python scripts/collect_evidence.py
```

Resultados realmente ejecutados, pruebas externas pendientes y evidencia en
[VALIDATION.md](docs/VALIDATION.md) y [STATUS.md](docs/STATUS.md).
CI ejecuta controles en Windows y Linux; su estado actual está en
[GitHub Actions](https://github.com/GzoC/plc-logic-verifier/actions).

## Documentación

[Guía de uso](docs/USER_GUIDE.md) · [Subconjunto ST](docs/ST_SUBSET.md) ·
[Semántica](docs/SEMANTICS.md) · [Escenarios](docs/SCENARIOS.md) ·
[Arquitectura](docs/ARCHITECTURE.md) · [IA](docs/AI.md) ·
[Límites](docs/LIMITATIONS.md) · [Demo de 5 minutos](docs/DEMO.md) ·
[Licencias de dependencias](docs/DEPENDENCIES.md)

## English summary

PLC Logic Verifier is a local, deterministic simulator and scenario checker for a
strictly defined Structured Text subset. It includes a source-located AST, type checking,
scan semantics, independent TON/R_TRIG instances, YAML requirements and reproducible
JSON/CSV/HTML/JUnit evidence. CLI and local UI share the same engine. Optional AI
suggestions require explicit data submission and never change deterministic verdicts.
It does not certify functional safety, implement universal IEC 61131-3 compatibility,
replace FAT/SAT, or control physical equipment. External runtime and live AI validation
have not been performed; see the validation record.

## Integridad de resultados (corrección de auditoría)

La interfaz liga cada resultado a una revisión y una instantánea ST/YAML con hashes
comprobados. Editar o cargar otras entradas invalida resultados y respuestas IA pendientes.
`report` importa sólo JSON v1 completo y coherente; archivos contradictorios devuelven
código 2. Validar el formato SHA-256 no autentica un informe. CSV/HTML/XML son exportaciones,
no formatos de reimportación. Límites y regresiones en [cierre de auditoría](docs/AUDIT_FIXES.md).

IA: primero selecciona requisitos/scans/fragmentos, prepara un borrador, revisa su tamaño,
reduce o edita y autoriza ese borrador. Enviar sigue siendo una acción separada explícita.
No se transmite información al preparar ni autorizar localmente.
