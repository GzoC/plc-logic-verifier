# IA opcional, envío explícito

Proveedor implementado: OpenAI, SDK Python `openai==2.8.0`, Responses API con
`responses.parse(text_format=Advice)`. No hay modelo predeterminado; configure un
ID real disponible en su cuenta mediante OPENAI_MODEL. OPENAI_API_KEY sólo en el
entorno del servidor/CLI. `.env.example` no contiene claves ni se carga automáticamente.

```powershell
uv sync --locked --extra ai
uv run plc-verifier explain outputs/defect/result.json --payload outputs/payload.json
# Revisar/editar el JSON. Opcional --include-program <archivo.st>; comentarios excluidos.
uv run plc-verifier explain --payload outputs/payload.json --send
```

La primera acción nunca envía. La segunda envía únicamente ese objeto JSON a
`https://api.openai.com/v1`, más instrucciones fijas del sistema y el esquema de respuesta.
La UI tiene el mismo paso de previsualización editable. Credenciales jamás se presentan
en la página. Se puede excluir cualquier campo o fragmento editando el payload.
Máximo 24.000 bytes canónicos, timeout 20 s, cero reintentos automáticos y salida
máxima 2500 tokens. Errores, rechazo o respuesta incompleta no alteran resultados.

Respuesta: resumen, evidencia, hipótesis, ambigüedades, escenarios propuestos y diff
revisable. Nada se aplica ni ejecuta. Los escenarios sugeridos se validan en sintaxis
YAML/esquema, se etiquetan NOT_EVALUATED hasta probarlos con ST compatible y revisión
humana. Contenido de programas, comentarios y trazas se trata como datos no confiables.
La etiqueta «SUGERENCIA DE IA — NO VERIFICADA» separa estas respuestas de los informes.

Pruebas realizadas con dobles: sin clave, timeout, respuesta inválida, rechazo,
respuesta estructurada y escenario sugerido inválido. No se hizo petición a un modelo
real; no se atribuye calidad técnica validada a sus sugerencias.

Fuentes oficiales consultadas 2026-11-14 (documentación web sin versión fija):
- [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [SDK Python, timeout y errores](https://developers.openai.com/api/reference/python)
- [SDK helpers](https://github.com/openai/openai-python/blob/main/helpers.md)
La dependencia ejecutable está fijada en pyproject.toml y uv.lock.

## Flujo corregido 2026-11-16

`preview_payload` devuelve borrador local incluso sobre 24.000 bytes. La UI muestra
su tamaño UTF-8 compacto y bloquea la autorización/envío hasta reducirlo. Selecciones
previas: IDs de requisitos, índices de scans y líneas inclusivas de ST. Vacío = todos
los requisitos/evidencia; `-` = ninguno. El manifiesto enumera requisitos omitidos y
scans incluidos; ninguna reducción es automática. Editar invalida la autorización anterior.

CLI: `explain result.json --requirements R0 --scans "" --payload draft.json`.
`--source-lines 1:20` limita el fragmento de `--include-program`. El borrador puede
guardarse sobre el límite; `--send` vuelve a verificar los 24.000 bytes sin truncar.
Para escenarios: `--suggest-scenarios --context-program executed.st` incluye el esquema
JSON de Scenario y variables/tipos/secciones del programa cuyo hash coincide con el
resultado. No incluye el código salvo `--include-program`. Al enviar, suministrar
`--context-program executed.st` para validar localmente referencias, expresiones y
eventos de las sugerencias. Sintaxis y tipos se reportan por separado; su ejecución
permanece NOT_EVALUATED. La UI usa siempre su instantánea ejecutada para ambas acciones.
No se realizó llamada externa; pruebas de proveedor siguen siendo dobles.
