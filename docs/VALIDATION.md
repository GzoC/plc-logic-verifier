# Estado vigente — 2026-11-17

Estado vigente: `main` y `origin/main` en `ecd478c82ae9bdfe2af2898779daf909af2148a4`; CI Windows y Linux aprobada. Se verificaron los ocho archivos en Edge y ocho scans con IronPLC. Integración real con proveedor: pendiente. Véanse [evidencias, diferencias y comandos del 17 de noviembre](VERIFICATION_2026-11-17.md).

---

**Registro histórico:** las indicaciones de trabajo sólo local, CI pendiente o descarga XML pendiente describen la fecha de la sección siguiente.

# Evidencia histórica (2026-11-14/15)

Los resultados siguientes pertenecen a la versión anterior. Para las correcciones y
pruebas nuevas de 2026-11-16, ver [AUDIT_FIXES.md](AUDIT_FIXES.md).

# Validación y evidencia

Última comprobación: 2026-11-15. Entorno local observado: Windows, Python 3.12.13, uv 0.11.19.

58 pruebas automatizadas pasan también en un entorno nuevo instalado desde `uv.lock`.
Ruff lint/formato y mypy pasan. `uv build` genera sdist y wheel, con el HTML de la UI
incluido. CLI real: ejemplo normal código 0; defecto timeout_disabled código 1.
La generación de evidencia vuelve a confirmar seis PASS y seis FAIL esperados.
GitHub Actions también finalizó correctamente en Windows y Linux para el commit
`ac3043bffb8927473c0efcb3cd2ec1878e92d330`:
[ejecución 43726130985](https://github.com/GzoC/plc-logic-verifier/actions/runs/43726130985).
Instalación, lint, formato, tipos, suite y ejemplo CLI completados; artefactos subidos.
Incluyen tablas de TON
PT=0/200/250 con scans de 100 ms; primer instante, PT-scan/PT/PT+scan, saturación/reset,
cambios de PT, llamadas omitidas/duplicadas, instancias independientes, flancos iniciales,
orden/persistencia/imágenes, aritmética, parser/tipos, YAML inválido, repetibilidad,
no vacuidad, plazos, cancelación/timeout, seis escenarios correctos y seis mutantes.
Interfaces: códigos CLI, cuatro formatos, escaping HTML, JUnit de ERROR, HTTP local,
origen/token y equivalencia worker/motor. IA: dobles y ausencia de clave, sin red real.

La suite usa valores esperados independientes del intérprete: tablas escritas a mano
y requisitos de ejemplos definidos en `examples/REQUIREMENTS.md`. No es una demostración
formal de corrección. La cobertura enumerada no implica cubrir todos los casos de ST.

Registro previo de UI (2026-11-14) en Edge: carga de ejemplo, PASS de lubricación normal; FAIL de timeout_disabled;
primer fallo scan 4/400 ms; inspector de bloques y vista previa IA sin envío.
Captura real en `docs/evidence/ui-failure.jpg`. La espera automatizada de descarga del
navegador agotó el timeout; revisar el registro de cierre para su comprobación posterior.
En este checkpoint se inspeccionó la captura existente, sin repetir la interacción del
navegador. La descarga por navegador sigue pendiente; la exportación HTTP pasa en la suite.

## Comparación externa

Se evaluó [MatIEC de Beremiz](https://github.com/beremiz/matiec) y la
[guía oficial de compilación](https://beremiz.readthedocs.io/en/latest/install.html)
(documentación Beremiz 1.5.1, consultada 2026-11-14). Requiere compilación con herramientas
no disponibles en PATH de esta máquina: iec2c, GCC/Clang, make, flex y bison.
No se añadió como dependencia ni se ejecutó comparación diferencial. No hay versión de
runtime externo validada ni se declara equivalencia con un PLC comercial. Una integración
futura debe fijar commit/toolchain y contrastar tablas independientes de la semántica.

## Reproducción

`uv run python scripts/collect_evidence.py` ejecuta los seis escenarios y seis mutantes,
genera `docs/evidence/summary.json` y conserva el caso defectuoso en sus cuatro formatos.
Los resultados no se leen para simular ni se usan como sustituto del motor.
Las fuentes ST/YAML y sus hashes permiten recalcularlos. CI sube artefactos por sistema.
