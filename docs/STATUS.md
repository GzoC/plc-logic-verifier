# Estado y punto de reanudación

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
- La captura previa `docs/evidence/ui-failure.jpg` se conservó y se inspeccionó;
  no se presenta como una nueva prueba de navegador.

### Pendientes y límites

- Confirmar resultado de GitHub Actions después del push de este checkpoint.
- El registro previo de UI indica PASS/FAIL en Edge y timeout al esperar una descarga;
  la ruta HTTP de exportación y los cuatro formatos sí están probados por la suite.
  La descarga mediante el navegador sigue pendiente de nueva comprobación.
- No se ha enviado una solicitud a un modelo real. IA validada con dobles y sin clave.
- No se ejecutó comparación diferencial con MatIEC ni validación contra PLC comercial.
- Móviles y lectores de pantalla no tienen validación exhaustiva. No certifica seguridad.

### Cuota y continuidad

Última lectura durante esta etapa: **88% restante en ventana de 300 minutos**
(`usedPercent=12`), **29% semanal**. Es cuota compartida de la cuenta, no tiempo
de reloj ni un saldo diario fijo. Consultar de nuevo antes de continuar.

Consultar `mcp__codex_app.get_usage_limits` al cerrar cada etapa y antes de trabajo
costoso. Checkpoint preventivo al observar <=10%; al observar <=7%, guardar cualquier
avance posterior, commit y push, y detener nuevas etapas. La vigilancia sólo ocurre
durante trabajo activo; no existe un monitor permanente fuera del chat.

Próximo paso: comprobar que el commit local coincide con `origin/main`, consultar la
ejecución CI de ese SHA y registrar su resultado. Si falla, corregir el fallo concreto,
revalidar y crear otro checkpoint. Después retomar los pendientes anteriores según alcance.

### Historial conservado

- 2026-11-14: carpeta inicial vacía; encargo conservado en `docs/BRIEF.md`.
- `903cfd4`: parser y motor determinista.
- `9fc1d6e`: escenarios industriales, informes y CLI.
- El STATUS anterior registraba 46 pruebas y dejaba CLI/UI/IA pendientes; había avances
  adicionales sin commit. Este checkpoint actualiza ese registro con comprobaciones reales.
