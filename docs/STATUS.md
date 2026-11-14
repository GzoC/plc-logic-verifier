# Estado y punto de reanudación

2026-11-14: inicio desde carpeta vacía. Encargo conservado en BRIEF.md.
Repositorio privado solicitado: GzoC/plc-logic-verifier.
Cuota observada al inicio: 58% restante en ventana de 300 min; 40% semanal.

Checkpoint 2: parser Lark, AST localizado, comprobación de tipos, motor determinista,
YAML estricto y ocho clases de requisitos. Tres ejemplos correctos con seis escenarios
y seis mutantes separados. 46 pruebas pasan (pytest local Python 3.12.13).
Ruff detectó una captura de variable en una función local: corregida; revalidar.
Cuota observada: 41% restante / 37% semanal.

Pendiente: CLI, informes, interfaz local, IA opcional, documentación final y CI.
MatIEC evaluado: no hay iec2c, GCC/Clang, make, flex ni bison en PATH; comparación
externa no ejecutada. No se ha probado ningún PLC comercial.

Próximo paso: terminar CLI e informes, luego interfaz y IA, pruebas integrales y
validación en entorno limpio. No presentar aún como producto terminado.
