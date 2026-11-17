# Estado vigente — 2026-11-17

Estado vigente: `main` y `origin/main` en `ecd478c82ae9bdfe2af2898779daf909af2148a4`; CI Windows y Linux aprobada. Se verificaron los ocho archivos en Edge y ocho scans con IronPLC. Integración real con proveedor: pendiente. Véanse [evidencias, diferencias y comandos del 17 de noviembre](VERIFICATION_2026-11-17.md).

Checkpoint local de esta intervención. Cuota restante observada (300 minutos / semanal): 74% / 54%, 62% / 52%, 51% / 50%. Sin push, merge ni despliegue.

---

**Registro histórico:** las indicaciones de trabajo sólo local, CI pendiente o descarga XML pendiente describen la fecha de la sección siguiente.

# Estado y punto de reanudación

## Correcciones de auditoría — 2026-11-16

Base `0b5074965cb2de9d6633f25ef618cc5e0f01f995` comprobada; árbol inicialmente limpio.
Instrucción vigente: NO push, merge, publicación ni despliegue. Checkpoint sólo local.
Los seis hallazgos están corregidos. Detalle, archivos, comandos, evidencia y límites
se encuentran en `docs/AUDIT_FIXES.md`. Evidencia nueva separada en
`docs/evidence/audit-2026-11-16/`; no se reemplazaron pruebas históricas.

Validación nueva: 89 pytest PASS (0 FAIL/0 SKIP; incluyen 10 casos de JS real en Node),
Ruff/formato/mypy PASS, wheel/sdist construidos, instalación en entorno limpio sin SDK IA.
12 fixtures esperados, 12 repeticiones idénticas HTTP, 48 exportaciones y 12 reimportaciones.
Caso grande 30 INT/7000 scans: PASS; JSON compacto 11.867.943 bytes y roundtrip idéntico.
Edge: PASS/FAIL, descarte OLD→NEW, borrador de 42.856 bytes reducido a 2.476 y edición.
JSON/CSV/HTML descargados y comparados; XML por navegador pendiente (sin archivo observado).
XML por HTTP/CLI sí verificado. Ningún envío real de IA ni comparación externa nueva.

Lectura anterior: 14% restante de ventana 300 min; 2% semanal. Lectura posterior al
checkpoint: 90% restante de ventana 300 min y 98% semanal (usedPercent 10 y 2).
Guardado preventivo local; nunca confundir porcentajes con tiempo. No existe monitor
fuera del trabajo activo.
Próximo paso puntual: verificar descarga XML de Edge. No repetir toda la auditoría salvo
cambios nuevos. No hacer push sin nueva autorización. Servidor de prueba puerto 8766.

## Checkpoint de subida — 2026-11-15

Repositorio existente y confirmado **privado**: https://github.com/GzoC/plc-logic-verifier
Rama: `main`. El usuario autorizó subir el proyecto; conservar su visibilidad.
Base remota verificada antes de esta subida: `9fc1d6e`.

### Implementado y conservado

- Parser Lark, AST localizado, tipos y motor determinista con tiempo virtual.
- YAML estricto, ocho clases de requisitos, tres casos industriales, seis escenarios
  correctos y seis variantes defectuosas separadas.
- CLI `validate`, `run`, `report`, `explain` y `serve`; JSON, CSV, HTML y JUnit.
- Interfaz loopback y worker aislado que usa el mismo motor; inspector de trazas y bloques.
- IA opcional con previsualización editable, envío explícito y validación de respuestas;
  no modifica resultados ni ejecuta sugerencias.
- Documentación, inventario de dependencias y workflow Windows/Linux preparados.

### Comprobaciones realizadas en este checkpoint

- Instalación con `uv sync --locked --python .venv/Scripts/python.exe --all-extras`
  en un entorno nuevo `.local/clean-env`, usando caché local `.local/uv-cache`.
  El argumento de intérprete reutiliza Python 3.12.13, no las dependencias del entorno anterior.
  Se usó `UV_PROJECT_ENVIRONMENT=.local/clean-env` para mantener el entorno previo.
- **58 pruebas pasan** en el entorno nuevo; JUnit local en `outputs/tests.xml`.
- Ruff lint y formato pasan; mypy pasa para los nueve archivos de código fuente.
  Se corrigió la anotación del servidor HTTP y el formato de dos scripts.
- `scripts/collect_evidence.py`: **6 PASS y 6 FAIL esperados**; evidencia versionada
  en `docs/evidence/summary.json` y `docs/evidence/timeout-disabled/`.
- CLI desde el entorno nuevo: lubricación normal PASS (código 0); timeout desactivado
  FAIL (código 1), requisito L03 en scan 4 / 400 ms.
- `uv build` genera sdist y wheel; el wheel contiene `plc_verifier/ui.html`.
- Código y evidencias subidos en `ac3043bffb8927473c0efcb3cd2ec1878e92d330`;
  coincidencia local/remota comprobada. [CI 43726130985](https://github.com/GzoC/plc-logic-verifier/actions/runs/43726130985)
  finalizada con **success en Windows y Linux**, incluidos instalación, lint, formato,
  tipos, suite, ejemplo CLI y subida de artefactos. El cierre posterior sólo modifica
  documentación y omite una repetición de CI mediante `[skip ci]`.
- La captura previa `docs/evidence/ui-failure.jpg` se conservó y se inspeccionó;
  no se presenta como una nueva prueba de navegador.

### Pendientes y límites

- El registro previo de UI indica PASS/FAIL en Edge y timeout al esperar una descarga;
  la ruta HTTP de exportación y los cuatro formatos sí están probados por la suite.
  La descarga mediante el navegador sigue pendiente de nueva comprobación.
- No se ha enviado una solicitud a un modelo real. IA validada con dobles y sin clave.
- No se ejecutó comparación diferencial con MatIEC ni validación contra PLC comercial.
- Móviles y lectores de pantalla no tienen validación exhaustiva. No certifica seguridad.

### Cuota y continuidad

Última lectura durante esta etapa: **78% restante en ventana de 300 minutos**
(`usedPercent=22`), **27% semanal**. Es cuota compartida de la cuenta, no tiempo
de reloj ni un saldo diario fijo. Consultar de nuevo antes de continuar.

Consultar `mcp__codex_app.get_usage_limits` al cerrar cada etapa y antes de trabajo
costoso. Checkpoint preventivo al observar <=10%; al observar <=7%, guardar cualquier
avance posterior, commit y push, y detener nuevas etapas. La vigilancia sólo ocurre
durante trabajo activo; no existe un monitor permanente fuera del chat.

Próximo paso: consultar cuota y estado Git al retomar; revisar primero la descarga
de informes desde el navegador. Para iniciar la UI: `uv run plc-verifier serve`.
Mantener como pendientes separados la IA real y la comparación externa; requieren
credenciales o herramientas que no forman parte de las validaciones efectuadas.

### Historial conservado

- 2026-11-14: carpeta inicial vacía; encargo conservado en `docs/BRIEF.md`.
- `903cfd4`: parser y motor determinista.
- `9fc1d6e`: escenarios industriales, informes y CLI.
- El STATUS anterior registraba 46 pruebas y dejaba CLI/UI/IA pendientes; había avances
  adicionales sin commit. Este checkpoint actualiza ese registro con comprobaciones reales.
