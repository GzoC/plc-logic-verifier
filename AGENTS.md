# PLC Logic Verifier

Leer `docs/STATUS.md`, `docs/ARCHITECTURE.md` y `docs/SEMANTICS.md` antes de continuar.
El encargo íntegro está en `docs/BRIEF.md`. No inventar validaciones ni compatibilidad.

## Continuidad y presupuesto
- Durante trabajo activo consultar `mcp__codex_app.get_usage_limits` al terminar cada etapa y antes de trabajo costoso.
- Usar la ventana de 300 minutos: restante = 100 - usedPercent. Es cuota compartida, no tiempo de reloj.
- Al observar <=10% restante, guardar inmediatamente código, pruebas reales, pendientes y próximo paso en `docs/STATUS.md`; commit y push al repositorio privado autorizado. No empezar otra etapa costosa antes del checkpoint.
- Umbral solicitado por el usuario: al observar <=7% restante, actualizar el checkpoint, hacer commit y push de cualquier avance posterior y detener nuevas etapas. El 10% anterior es un resguardo preventivo; no esperar al 7% para guardar por primera vez.
- La vigilancia se realiza durante trabajo activo, no es un monitor permanente fuera del chat. Registrar cada lectura relevante como restante de la ventana de 300 minutos y también el límite semanal; nunca confundir usedPercent con restante ni con horas de reloj.
- Mantener checkpoints intermedios aunque no se alcance ese umbral. Si no hay contador, declarar el dato desconocido.
- No incluir credenciales, .env, entornos ni datos personales. El usuario autorizó crear el repositorio y subir este proyecto; no cambiar su visibilidad.

## Calidad
- Nunca ejecutar ST/YAML con eval/exec. Rechazar construcciones no soportadas.
- La UI y la CLI comparten motor. La IA nunca modifica resultados ni ejecuta sugerencias.
- Pruebas y evidencias se distinguen de pendientes. No representar esta herramienta como certificación.
