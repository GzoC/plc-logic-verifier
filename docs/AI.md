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
