# Escenarios YAML

Campos obligatorios: id, description, program, duration_ms, scan_ms, requirements.
`program` es una ruta relativa al YAML en CLI (o `--program` la reemplaza).
La UI usa siempre el texto ST cargado y nunca abre esa ruta desde una petición.
`initial` sobreescribe escalares declarados; BOOL usa true/false y INT/TIME enteros
(TIME en ms). No permite inicializar internamente bloques de función.

```yaml
id: pressure-stop
description: Parada cuando falta permiso
program: program.st
duration_ms: 1000
scan_ms: 100
initial:
  Enable: true
events:
  - time_ms: 500
    set:
      Enable: false
requirements:
  - id: R-stop
    description: No debe existir salida sin permiso
    kind: never
    when: NOT Enable
    expr: Ready
  - id: R-start
    description: Activar dentro de la ventana
    kind: eventually
    expr: Ready
    start_ms: 0
    end_ms: 400
```

Duración excluye su extremo final; ventanas de requisitos incluyen ambos extremos.
Todos los tiempos de eventos y ventanas deben coincidir con scans. Un evento usa
`scan` o `time_ms`, nunca ambos; no se admiten dos eventos en el mismo scan. Los cambios
persisten hasta otro evento y sólo escriben entradas. Initial se aplica antes del scan 0.
Campos desconocidos, claves duplicadas, anchors, aliases, tags de objetos, IDs repetidos,
ventanas vacías y listas de requisitos vacías son errores. Las expresiones usan el parser
ST tipado y sólo pueden producir BOOL; nunca Python.

| kind | Campos | Comprobación |
| --- | --- | --- |
| always | expr; when opcional | Expr debe ser TRUE en cada muestra elegible |
| never | expr; when opcional | Expr nunca TRUE en muestras elegibles |
| hold | expr, end_ms; when opcional | Expr TRUE durante el intervalo explícito |
| eventually | expr; when opcional | Al menos una muestra TRUE dentro de la ventana |
| mutex | steps; when opcional | Como máximo una expresión TRUE por scan |
| sequence | steps | Flancos TRUE en orden, en scans distintos; una secuencia por ventana |
| response | trigger, expr, within_ms | Cada flanco del trigger exige expr antes o en el plazo |
| latch | trigger, expr, until | Tras flanco del trigger, expr sigue TRUE hasta until válido |

En sequence, expresiones ya TRUE al comienzo se consideran flancos iniciales; una
expresión fuera de turno falla; tras completar la secuencia no se exigen repeticiones.
Para varias secuencias definir ventanas separadas. Incompleta tras empezar es FAIL;
sin pasos activados es NOT_EVALUATED. Simultaneidad de pasos es FAIL.
En response, expr TRUE en el scan disparador satisface la respuesta. Un trigger
sostenido no crea solicitudes nuevas. Plazo fuera de la ventana observada significa
NOT_EVALUATED aunque otra respuesta sí se haya satisfecho.
En latch, until libera en ese mismo scan; `release_observed` indica si se vio liberación.
Un PASS sólo prueba retención durante la ventana, no que hubo reconocimiento.
Agregar un requisito hold/response separado para probar el borrado válido.

Un `when` nunca verdadero o un trigger ausente no produce PASS. El estado global
prioriza ERROR/UNSUPPORTED, luego FAIL, luego NOT_EVALUATED y finalmente PASS.
Las aserciones por scan se anotan después de completar ejecución; un run abortado
no contiene una evaluación completa de requisitos.
