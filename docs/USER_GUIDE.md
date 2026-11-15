# Guía de uso

1. Clonar e instalar con los comandos del README. Ejecutar desde la raíz del repo.
2. Correr `uv run plc-verifier run examples/lubrication/normal.yaml --output outputs/normal`.
3. Repetir con `examples/lubrication/fault.yaml --program examples/lubrication/defects/timeout_disabled.st`.
   El estado FAIL es correcto: L03 detecta presión sin parada en scan 4.
4. Copiar un ejemplo compatible a una carpeta propia y escribir primero sus requisitos.
   Verificar tipos, unidades, duración y período del scan antes de analizar resultados.
5. Crear YAML siguiendo SCENARIOS.md. Validar con `validate escenario.yaml` (no ejecuta
   requisitos) y luego `run escenario.yaml --output outputs/propio`.
6. Abrir report.html; revisar requisito esperado, estado observado, primer scan,
   ventana de traza, últimas escrituras, hashes y semántica. Conservar result.json
   junto a los ST/YAML exactos. `report result.json` reexporta sin ejecutar nuevamente.

La UI ofrece el mismo flujo en localhost: elegir ejemplo o cargar dos archivos,
editar, ejecutar, pulsar «Ver scan», inspeccionar bloques y descargar evidencias.
Editar el texto invalida visualmente el resultado previo. Recargar la página pierde
los cambios no descargados; conservar los originales fuera del navegador.

`outputs/` no se versiona porque puede contener programas propios. Los ejemplos de
evidencia versionados se generan exclusivamente a partir de fixtures del proyecto.
Para una cancelación CLI usar Ctrl+C; no considerar el directorio de salida terminado
hasta que el comando concluya. La interfaz termina su worker al exceder 15 segundos.
