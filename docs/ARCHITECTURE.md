# Arquitectura de la primera versión

Aplicación Python local sin equipos físicos ni servicios obligatorios.
`language`: gramática Lark -> AST con posiciones -> comprobación de tipos.
`engine`: intérprete acotado, estado por instancia y reloj virtual entero en ms.
`scenario`: YAML estricto -> requisitos declarativos -> resultados no vacuos.
`reports`: JSON, CSV, HTML autocontenido y JUnit a partir del mismo resultado.
`cli` y `web`: adaptadores del mismo motor; servidor sólo en loopback.
`ai`: envío opcional explícito de un payload previsualizado, sin cambiar veredictos.

Se prioriza un único proceso con límites de fuente, profundidad, scans, variables y traza;
la interfaz ejecutará verificaciones en un subproceso con timeout. No hay almacenamiento
remoto, cuentas de usuario, conexiones a PLC ni despliegue.

Decisiones: tiempo entero, INT con signo de 16 bits, subconjunto cerrado, expresiones
de aserción con el mismo parser tipado, errores explícitos y sin ejecución dinámica.
