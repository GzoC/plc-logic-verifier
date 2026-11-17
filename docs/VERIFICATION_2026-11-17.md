# Verificación del 17 de noviembre de 2026

Base: `main` y `origin/main` en `ecd478c82ae9bdfe2af2898779daf909af2148a4`. [CI de esa revisión](https://github.com/GzoC/plc-logic-verifier/actions/runs/43878082590): se consultó el run y ambos trabajos, Windows y Ubuntu, terminaron con éxito. No es una CI de los scripts locales que acompañan este informe.

Esta intervención ejecutó la instalación bloqueada con todos los extras, Ruff y formato, mypy, pytest (89 aprobadas, cero fallidas u omitidas), el archivo JavaScript en Node (10 aprobadas; no sumar a pytest como casos independientes), y la construcción de wheel y sdist. [HTTP](evidence/verification-2026-11-17/http.json): 12 ejemplos, seis PASS y seis FAIL esperados; 12 repeticiones idénticas, 48 exportaciones comparadas y 12 reimportaciones JSON. El script acepta un directorio de salida para preservar el registro anterior.

## Qué guardó Edge

Microsoft Edge 157.0.4341.46, sin ventana, perfil temporal, sandbox habilitado, servidor de loopback. En transporte normal y en el defecto `reverse_start`, cada botón produjo un `POST /export` con el resultado exacto de `/run`, respuesta 200, un evento de descarga y el nombre esperado. Se leyó el archivo guardado y se comparó íntegro con el cuerpo HTTP y el generador correspondiente. [Manifiesto con MIME, nombres, tamaños, SHA-256 y consola](evidence/verification-2026-11-17/edge.json). No hubo excepciones de página. El único error de consola fue un 404 de `favicon.ico`. No se reprodujo un defecto XML ni se modificó la aplicación. La automatización guarda el archivo indicado por el evento: no prueba el diálogo interactivo ni la carpeta predeterminada del perfil personal.

| Resultado | result.json | trace.csv | report.html | junit.xml | JUnit: pruebas / fallos / errores / omitidas |
|---|---:|---:|---:|---:|---|
| PASS | 15438 | 9031 | 40671 | 413 | 5 / 0 / 0 / 0 |
| FAIL | 16885 | 8600 | 75259 | 4273 | 5 / 3 / 0 / 0 |

Tamaños en bytes. Se conservaron los ocho archivos bajo `evidence/verification-2026-11-17/{PASS,FAIL}` sin conversión de fin de línea de Git.

## Comparación ejecutada con IronPLC

Se eligió la VM WebAssembly del [playground oficial](https://playground.ironplc.com/) del [proyecto IronPLC](https://github.com/ironplc/ironplc) porque su API permite cargar ST con un intervalo en microsegundos y avanzar exactamente un scan. Los únicos artefactos externos descargados para esta ejecución fueron el módulo JS y su WASM; sus hashes se comprueban antes de importarlos. Versión devuelta por el propio módulo: **0.254.0**. Se ejecutaron con Node local, sin el frontend del sitio ni equipos físicos. La distribución online puede cambiar: conservar `.local/ironplc/runtime.{mjs,wasm}` para repetir esta versión. Si el hash no coincide, el comparador se detiene; no sustituir el runtime manteniendo esta evidencia.

[Programa común](evidence/verification-2026-11-17/shared.st), [escenario](evidence/verification-2026-11-17/shared.yaml) y [ambas trazas](evidence/verification-2026-11-17/runtime.json). Instancia nueva, variables inicialmente cero/falso, ocho scans; la primera muestra es t=0 y la última t=350 ms. En cada ciclo primero se actualizan contador y habilitación, luego IF/CASE, después los bloques y finalmente se leen sus salidas. El reloj interno de IronPLC se comprobó en las ocho muestras; no se utilizó tiempo de pared. La entrada baja a 200 ms y sube de nuevo a 250 ms.

Coincidieron aritmética, booleanos, IF, CASE, acumulación, pulso ascendente y las salidas Q de TON con PT=100 y 125 ms (primer cumplimiento a 100 y 150 ms). De ocho variables escalares por ocho muestras, 62 de 64 valores coincidieron. Las dos diferencias son el mismo comportamiento: para PT=0, en ambos flancos de habilitación (0 y 250 ms) el verificador publica TRUE inmediatamente, IronPLC FALSE hasta el siguiente scan. Se clasifica como diferencia respecto de la semántica explícita de [SEMANTICS.md](SEMANTICS.md), no como defecto demostrado de uno u otro motor. No se compararon ET ni estados internos de las instancias. Sin afirmación de equivalencia general.

## Integración real con proveedor: pendiente

No se detectaron `OPENAI_MODEL` ni `OPENAI_API_KEY` configurados, y no había autorización de gasto. No se llamó al proveedor. Se ejecutó el flujo de borrador con el defecto sintético de transporte: FAIL determinista y borrador de 16.252/24.000 bytes, con contexto y esquema para sugerencias. Para una prueba posterior, generar borrador y resultado juntos por CLI (comandos abajo). En Windows el editor web usa LF y un archivo CLI puede contener CRLF: durante esta verificación el intento de usar ese archivo con el resultado de Edge fue rechazado correctamente por hash distinto. Mantener los bytes exactos del programa ejecutado.

Sólo tras acordar modelo y tope, configurar las dos variables localmente y revisar el JSON exacto. Para una única solicitud: `uv run plc-verifier explain --payload .local/ai-review.json --context-program examples/conveyor/defects/reverse_start.st --send`. Registrar fecha/modelo, comprobar la explicación contra las tres evidencias FAIL, los diagnósticos de sintaxis/tipos y la etiqueta no verificada; comparar SHA-256 del result.json antes y después y comprobar que ninguna sugerencia fue ejecutada. Una respuesta correcta en este caso sólo acreditaría integración básica.

## Reproducir en PowerShell desde la raíz

```powershell
$env:UV_CACHE_DIR="$PWD/.local/uv-cache"
uv sync --locked --python 3.12 --all-extras
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run mypy src --cache-dir .local/mypy-audit
uv run pytest -q --basetemp .local/pytest-repro-new -o cache_dir=.local/pytest-cache-audit
node --test tests/ui_races.test.cjs
uv build
uv run python scripts/audit_http.py --output .local/repro-http
uv pip install --python .venv/Scripts/python.exe --target .local/browser-verification playwright==1.55.0
$env:PYTHONPATH=(Resolve-Path .local/browser-verification).Path
.venv/Scripts/python scripts/verify_edge_downloads.py .local/repro-edge
```

Para la VM opcional, descargar los dos archivos si aún no están guardados. El comparador comprueba las huellas antes de ejecutarlos y escribe nuevamente `runtime.json`.

```powershell
New-Item -ItemType Directory -Force .local/ironplc | Out-Null
Invoke-WebRequest https://playground.ironplc.com/pkg/ironplc_playground.js -OutFile .local/ironplc/runtime.mjs
Invoke-WebRequest https://playground.ironplc.com/pkg/ironplc_playground_bg.wasm -OutFile .local/ironplc/runtime.wasm
uv run plc-verifier run docs/evidence/verification-2026-11-17/shared.yaml --output .local/ironplc
node scripts/compare_ironplc.mjs
```

Preparación de IA local, sin envío (el primer comando devuelve 1 por el FAIL esperado):

```powershell
uv run plc-verifier run examples/conveyor/normal.yaml --program examples/conveyor/defects/reverse_start.st --output .local/ai-fixture
uv run plc-verifier explain .local/ai-fixture/result.json --context-program examples/conveyor/defects/reverse_start.st --suggest-scenarios --payload .local/ai-review.json
```
