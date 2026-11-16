# Cierre de correcciones — 2026-11-16

Base comprobada: `0b5074965cb2de9d6633f25ef618cc5e0f01f995`, main, árbol limpio.
Los seis hallazgos seguían vigentes. Cambios sólo locales: sin push, merge, publicación,
cambio de visibilidad ni licencia. Evidencia anterior conservada en sus rutas originales.

| Hallazgo | Corrección y evidencia nueva |
| --- | --- |
| Respuestas obsoletas | ui.html conserva revisión e instantánea congelada por ejecución, comprueba ambos SHA-256 y descarta respuestas fuera de revisión. La IA usa esa instantánea. Tickets separados para borradores/respuestas y autorización ligada al texto exacto. Diez pruebas Node sobre el script real: ST/YAML editados, ejemplo cambiado, orden inverso, hashes incorrectos, preview/explicación tardíos y carga asíncrona. Edge: ejecución larga OLD, edición NEW mientras pendiente, respuesta antigua sin resultado visible. |
| Plazos de ejemplos | Transporte activa TON en el scan de la transición publicada: 200 ms con scans 10/50/100; 210 ms con scan 70. Se prueban muestras anterior, límite y posterior, stop durante arranque y nuevo arranque. Lubricación usa reloj de fase: 500/300 ms observables; timeout de presión a 300 ms. Pruebas a los mismos cuatro períodos. Motor TON sin cambios. |
| Reimportación | JSON compacto; presupuesto compartido 32 MiB al producir/importar. Caso 30 variables × 7000 scans PASS: JSON 11.867.943 bytes; HTML 35.061.029 bytes; CSV 13.287.710; XML 170. Exportación, importación, regeneración y hashes idénticos. Límites UTF-8, archivo excesivo y preflight antes de escribir exportación probados. |
| Informes inconsistentes | result_schema.py define v1 tipado: metadatos, hashes, estados, errores, trazas, posiciones y evidencia coherentes. Rechaza JSON mínimo, PASS contradictorio, versión desconocida, hashes/índices/tipos inválidos con código 2, sin traceback. Se prueban PASS/FAIL/ERROR/UNSUPPORTED/NOT_EVALUATED legítimos, incluidos errores previos a ejecución. El formato del hash no autentica el resultado. |
| IA sobredimensionada | Borrador local siempre accesible, selección previa de requisitos/scans/líneas, manifiesto de omisiones y tamaño visible. Envío validado a 24.000 bytes; edición requiere nueva autorización en UI. Caso de 30 descripciones de 500 caracteres: 42.856 bytes, reducible a 2.476 seleccionando R0 y sin scans. Comprobado en Python y Edge sin llamada externa. |
| Escenarios IA sin contexto | Al solicitarlos, payload incluye JSON Schema y variables/tipos/secciones del programa cuyo hash coincide. Fuente completa permanece local salvo inclusión explícita. Se validan sintaxis, estructura, referencias y tipos; ejecución sigue NOT_EVALUATED. Dobles prueban propuesta válida, variable inexistente y expresión de tipo incorrecto. |

## Resultados nuevos

- `uv sync --locked --python 3.12 --all-extras`: PASS.
- Ruff lint, formato (19 archivos) y mypy (11 fuentes): PASS.
- Pytest: **89 PASS, 0 FAIL, 0 SKIP**. Una prueba ejecuta los **10 casos Node** del JavaScript real.
- `uv build`: wheel y sdist generados.
- 12 fixtures: 6 PASS y 6 FAIL esperados, cada mutante detectado por su requisito.
- HTTP real: 12 resultados, 12 repeticiones idénticas, 48 exportaciones comparadas con
  sus renderizadores, 12 reimportaciones JSON. CLI/motor y worker HTTP coinciden.
- Entorno nuevo `.local/audit-clean`, instalación según README sin extra IA: transporte
  normal PASS, validación de lubricación válida; se comprobó ausencia de SDK OpenAI.
- Edge escritorio: ejemplos correcto/defectuoso, carrera OLD→NEW, preparación/reducción/
  edición de borrador. Consola sin errores capturados. JSON/CSV/HTML descargados realmente
  y comparados byte a byte con los renderizadores del resultado descargado.

Evidencia: `docs/evidence/audit-2026-11-16/`: JUnit de pruebas, resumen de fixtures,
matriz HTTP/tamaños, medidas del caso grande, descargas confirmadas y captura real.
El fallo inicial de permisos de la carpeta temporal se resolvió usando rutas locales;
los diagnósticos intermedios de formato/tipos fueron corregidos antes del cierre.

## Pendientes precisos

- XML desde navegador: se pulsó descarga, sin error de consola, pero no se encontró
  archivo resultante. Una comprobación adicional del evento de descarga agotó su
  espera de 12 segundos sin recibirlo. No se atribuye a una causa no demostrada. XML sí pasó generación,
  análisis XML y comparación por HTTP/CLI. Queda verificar el destino/flujo de descarga de Edge.
- No se envió solicitud a IA real ni se verificó calidad de un modelo real.
- Sin MatIEC, PLC comercial, validación móvil o lector de pantalla nuevos.
- CI remoto no ejecutado para estos cambios: no se hizo push por instrucción del usuario.

## Reproducir

Desde la raíz, con uv, Python 3.12 y Node.js 24:

```powershell
uv sync --locked --python 3.12 --all-extras
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run mypy src
uv run pytest -q
uv build
node --test tests/ui_races.test.cjs
uv run python scripts/audit_http.py
uv run python scripts/collect_evidence.py --output docs/evidence/audit-2026-11-16
uv run plc-verifier serve --port 8766
```

En este sandbox se usó `UV_CACHE_DIR=.local/uv-cache`, mypy `--cache-dir .local/mypy-audit`
y pytest `--basetemp .local/pytest-audit-final -o cache_dir=.local/pytest-cache-audit`
por permisos de cachés/temporales preexistentes. Para repetir, usar una carpeta temporal
dedicada distinta; pytest limpia su propio basetemp.

JSON es el formato completo reimportable. CSV, HTML y XML son salidas; no se promete
reconstruir el resultado completo a partir de ellas. Presupuestos: traza estimada 16 MiB,
JSON 32 MiB, petición HTTP 33 MiB, HTML 128 MiB, CSV 64 MiB, XML 8 MiB. Exportación HTTP
cruda evita envolver HTML en JSON. La validación estructural no vuelve a ejecutar ni
autentica un archivo editado. No es producto certificado ni declarado listo para producción.
