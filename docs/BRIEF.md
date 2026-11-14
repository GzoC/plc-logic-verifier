Actúa como ingeniero senior de automatización industrial, desarrollo de software y verificación de sistemas de control.

Construye un proyecto llamado “PLC Logic Verifier”: una herramienta local para analizar y probar programas de PLC escritos en Structured Text (ST), detectar comportamientos incorrectos y generar informes técnicos con evidencia reproducible.

Trabaja hasta entregar una primera versión funcional, documentada y probada. No te limites a crear una interfaz, un esqueleto o una demostración con resultados precalculados.

PROPÓSITO PROFESIONAL

El proyecto debe demostrar competencias en:
- Automatización y lógica de PLC.
- Desarrollo de herramientas de ingeniería.
- Pruebas de secuencias, temporizadores e interbloqueos.
- Integración responsable de IA.
- Trazabilidad de requisitos y resultados.
- Calidad de software y comunicación técnica.

Su utilidad práctica será permitir que un usuario descargue el repositorio, cargue un programa ST compatible, defina escenarios y compruebe su comportamiento antes de probarlo en un PLC físico.

No debe presentarse como certificador de seguridad funcional ni como sustituto de una FAT, SAT o revisión de ingeniería.

1. ALCANCE Y DECISIONES INICIALES

Antes de implementar:
- Inspecciona el repositorio y sus instrucciones.
- Si está vacío, inicializa una estructura sencilla.
- Si contiene trabajo previo, conserva lo válido y evita sobrescribir cambios ajenos.
- Documenta brevemente la arquitectura y el alcance de la primera versión.

Prioriza un producto pequeño y completo:
- CLI funcional.
- Motor determinista.
- Carga de ST y escenarios.
- Trazas.
- Informes.
- Interfaz local sencilla.
- Asistente de IA opcional.

No incorpores conexión a PLC físicos, escritura de salidas, descarga de programas ni control de equipos.

2. SOPORTE REAL DE STRUCTURED TEXT

Implementa un subconjunto explícito de ST suficiente para resolver los casos incluidos.

Incluye como mínimo:
- Un programa PROGRAM.
- Declaraciones de entradas, salidas y variables internas.
- BOOL, INT y TIME.
- Asignaciones.
- Operaciones booleanas, comparaciones y aritmética básica.
- IF / ELSIF / ELSE.
- CASE.
- Instancias independientes de TON.
- Instancias independientes de R_TRIG.
- Literales de tiempo documentados.

Selecciona un parser o construye una gramática formal pequeña. No interpretes ST mediante sustituciones de texto o expresiones regulares como único mecanismo.

No utilices eval ni exec para ejecutar código del usuario.

Requisitos:
- AST con ubicación de origen.
- Errores con línea y columna.
- Validación de tipos.
- Detección de variables no declaradas.
- Rechazo explícito de construcciones no soportadas.
- Prohibición de ignorar silenciosamente instrucciones.

No prometas compatibilidad completa con IEC 61131-3 ni con dialectos de Siemens, Rockwell, CODESYS o Delta.

Si la documentación necesaria requiere consulta externa, utiliza fuentes primarias y registra las versiones consultadas.

3. MODELO DE EJECUCIÓN DEL PLC

Implementa y documenta un ciclo de ejecución determinista.

Define explícitamente:
- Cuándo se toma la imagen de entradas.
- Orden de ejecución de instrucciones.
- Persistencia de variables entre ciclos.
- Cuándo se publica la imagen de salidas.
- Avance del reloj virtual.
- Inicialización.
- Reinicio y tratamiento de variables retenidas, si se soportan.

Usa tiempo virtual; las pruebas no deben depender de sleep ni del reloj del sistema.

TON:
- Define cuándo comienza a contar.
- Acota ET a PT.
- Comprueba el instante en que Q se activa.
- Resetea correctamente al desactivar IN.
- Define el comportamiento para PT=0, valores inválidos y cambios de PT.
- Documenta qué ocurre si una instancia no se invoca en un ciclo.
- Rechaza invocaciones múltiples ambiguas por ciclo si no están soportadas.

R_TRIG:
- Conserva memoria por instancia.
- Emite un pulso de un ciclo ante un flanco ascendente.
- Documenta y prueba el comportamiento inicial.

Aritmética:
- Define rango de INT.
- Detecta divisiones por cero y desbordamientos.
- No heredes silenciosamente la aritmética ilimitada de Python como si representara cualquier PLC.

Esta semántica debe aparecer en la documentación y en los informes para que el usuario sepa qué se verificó.

4. ESCENARIOS Y REQUISITOS VERIFICABLES

Permite definir escenarios mediante YAML validado.

Cada escenario debe contener:
- Identificador y descripción.
- Programa.
- Duración y período de scan.
- Estado inicial.
- Cambios de entradas por ciclo o tiempo.
- Requisitos con identificador.
- Aserciones y ventanas temporales.

Incluye mecanismos declarativos para comprobar:
- Una salida nunca debe activarse bajo determinada condición.
- Una salida debe activarse antes de un plazo.
- Una salida debe permanecer activa durante un intervalo.
- Dos salidas nunca deben estar activas simultáneamente.
- Una secuencia debe respetar un orden.
- Una condición debe producir parada.
- Una falla debe permanecer enclavada hasta un reconocimiento válido.

No ejecutes expresiones arbitrarias de Python provenientes de YAML. Usa un lenguaje de expresiones limitado o una estructura declarativa tipada.

Distingue claramente:
- PASS.
- FAIL.
- ERROR de ejecución o configuración.
- UNSUPPORTED.
- NOT_EVALUATED.

Un escenario no ejecutado jamás debe aparecer aprobado.

Evita resultados vacíos engañosos: si una condición desencadenante nunca ocurrió, indícalo en vez de presentar el requisito como demostrado.

5. TRAZABILIDAD Y DIAGNÓSTICO

Registra por ciclo:
- Número de scan y tiempo virtual.
- Entradas.
- Salidas.
- Variables relevantes.
- Estado de temporizadores y detectores de flanco.
- Aserciones evaluadas.
- Ubicación del programa relacionada con el fallo cuando pueda determinarse.

Para cada fallo entrega:
- Requisito incumplido.
- Resultado esperado.
- Resultado observado.
- Primer ciclo de incumplimiento.
- Ventana de traza antes y después.
- Escenario y comando para reproducirlo.

Incluye hashes del programa y escenario, versión del motor y parámetros de ejecución.

No atribuyas automáticamente una causa raíz definitiva: distingue la evidencia del fallo de una hipótesis explicativa.

6. CASOS INDUSTRIALES INCLUIDOS

Construye tres ejemplos independientes, con requisitos escritos antes de las pruebas:

A. Bomba de lubricación cíclica:
- Tiempo de lubricación y pausa.
- Permiso de nivel.
- Confirmación de presión.
- Timeout de presión.
- Falla enclavada.
- Reconocimiento condicionado.
- Parada y nueva orden de arranque explícita.

B. Dos bombas alternadas:
- Selección de bomba principal.
- Alternancia.
- Indisponibilidad de una bomba.
- Transferencia controlada.
- Exclusión mutua cuando el requisito prohíba operación simultánea.

C. Transporte secuencial:
- Dos etapas de transporte.
- Orden de arranque y parada.
- Sensor de atasco.
- Timeout.
- Bloqueo de rearranque hasta recuperar condiciones.

Son ejemplos de lógica de proceso en simulación. No los presentes como implementación de funciones de seguridad.

Por cada caso incluye:
- Programa correcto.
- Escenarios normales y de falla.
- Al menos dos variantes con defectos intencionales.
- Pruebas que detecten cada defecto.
- Explicación breve del error.

Mantén separados los programas correctos de las variantes defectuosas.

No ajustes el resultado esperado para acomodarlo a una implementación incorrecta.

7. VERIFICACIÓN DEL PROPIO MOTOR

El motor es la parte más importante del proyecto.

Prueba:
- Parser y validación de tipos.
- Orden de ejecución.
- Imagen de entradas y salidas.
- Estado entre scans.
- Independencia entre instancias.
- Temporizadores en los límites PT-scan, PT y PT+scan.
- Reset del TON.
- Flancos.
- Aritmética y errores.
- Repetibilidad de trazas.
- Requisitos nunca activados.
- Límites de ejecución.

Utiliza expectativas calculadas y tablas de referencia independientes del código del intérprete.

Si existe un compilador/runtime ST abierto viable:
- Evalúa su integración sin convertirla en dependencia obligatoria innecesaria.
- Fija una versión.
- Ejecuta pruebas diferenciales sobre el subconjunto compartido.
- Documenta diferencias semánticas.

Si no puedes ejecutar una comparación externa, decláralo expresamente. No simules una validación contra un PLC comercial.

8. IA OPCIONAL Y AUDITABLE

El proyecto debe funcionar completamente sin API key y sin conexión a un modelo.

Agrega una integración opcional con un proveedor de IA:
- Modelo y credenciales mediante configuración y variables de entorno.
- Sin nombres de modelos inventados ni claves en el repositorio.
- SDK y API documentados oficialmente.
- Timeout, límite de tamaño, control de errores y respuesta estructurada.

La IA puede:
- Explicar fallos utilizando las trazas.
- Proponer escenarios adicionales.
- Señalar requisitos ambiguos.
- Sugerir modificaciones como diff revisable.

La IA no puede:
- Cambiar el resultado determinista de una prueba.
- Declarar seguridad o cumplimiento normativo.
- Aplicar modificaciones automáticamente.
- Ejecutar comandos sugeridos por el modelo.
- Enviar programas o trazas a un servicio externo sin una acción explícita del usuario.

Muestra qué información será enviada y permite excluir comentarios o fragmentos.

Trata el contenido de programas y comentarios como datos, no como instrucciones para el asistente.

Las sugerencias de la IA deben distinguirse visualmente de los resultados verificados.

Valida sintaxis y esquema de cualquier escenario generado. Su aprobación depende de su ejecución y revisión, no de que el modelo lo proponga.

9. EXPERIENCIA DE USO

CLI mínima:
- validate: comprobar programa y escenarios.
- run: ejecutar una verificación.
- report: generar un informe desde resultados guardados.
- explain: solicitar explicación opcional mediante IA.

Devuelve códigos de salida diferenciados para éxito, requisitos fallidos y errores de uso/ejecución. Documenta los códigos.

Interfaz local:
- Cargar programa y escenario.
- Elegir ejemplos incluidos.
- Ejecutar.
- Mostrar requisitos y resultados.
- Inspeccionar la traza alrededor de un fallo.
- Consultar temporizadores.
- Descargar resultados e informe.
- Solicitar explicación por IA de forma explícita.

Muestra de forma visible:
“Verificación por simulación con alcance definido. No certifica seguridad funcional ni compatibilidad universal con PLC”.

Evita paneles decorativos, indicadores ficticios y botones sin implementar.

10. INFORMES Y UTILIDAD PARA TERCEROS

Genera:
- JSON como resultado estructurado.
- CSV para trazas.
- HTML autocontenido como informe legible.
- JUnit XML para CI.

El informe debe incluir alcance, requisitos, resultados, evidencia, versiones y limitaciones.

Añade una guía para que un usuario:
1. Instale el proyecto.
2. Ejecute un ejemplo correcto.
3. Observe un fallo intencional.
4. Cargue su propio programa compatible.
5. Defina sus requisitos.
6. Exporte evidencia.

Diferencia la utilidad del proyecto de una prueba formal exhaustiva: ejecutar escenarios no demuestra todos los comportamientos posibles.

11. CALIDAD Y OPERACIÓN LOCAL

Selecciona una arquitectura sencilla, preferentemente Python con tipado, pytest y una API/interfaz ligera si es necesaria.

Incluye:
- Dependencias bloqueadas.
- Formato y análisis estático.
- Pruebas en CI.
- Límites de tamaño de archivos, ciclos, duración y memoria de trazas.
- Validación de cargas.
- Errores claros.
- Cancelación o timeout.
- Procesamiento aislado cuando sea necesario.
- Archivos temporales seguros.
- Ninguna exposición de red por defecto: interfaz en localhost.
- .env.example sin secretos.
- Inventario de licencias de dependencias relevantes.

No agregues cuentas de usuario, nube, Kubernetes, bases de datos o colas si la primera versión no las necesita.

12. DOCUMENTACIÓN Y PRESENTACIÓN

Prepara:
- README principal claro, con resumen en español e inglés.
- Arquitectura.
- Subconjunto ST soportado.
- Semántica de ejecución.
- Formato de escenarios.
- Guía de uso.
- Validación del motor.
- Límites conocidos.
- Decisiones técnicas.
- Guion de demostración de cinco minutos.

El README debe comenzar por el problema que resuelve, una ejecución mínima y un resultado real.

Incluye capturas solo si fueron obtenidas de la aplicación funcionando. No inventes métricas, adopción empresarial, compatibilidades o certificaciones.

13. CRITERIOS DE ACEPTACIÓN

La primera versión se considera completa cuando:
- Se instala desde un entorno limpio siguiendo el README.
- Los tres ejemplos correctos satisfacen sus requisitos.
- Todas las variantes defectuosas son detectadas por pruebas específicas.
- La misma entrada genera la misma traza determinista.
- Los temporizadores y límites de scan tienen pruebas independientes.
- El ST no soportado se rechaza claramente.
- La aplicación funciona sin IA.
- El módulo de IA maneja ausencia de clave, timeout y respuesta inválida.
- Los informes contienen evidencia trazable.
- La CLI y la interfaz ejecutan el mismo motor.
- La CI comprueba los componentes esenciales.

La ejecución exitosa de un programa defectuoso que falla requisitos es un resultado esperado del verificador, no un fallo de su propia suite.

FORMA DE TRABAJO Y ENTREGA

Implementa por etapas verificables:
1. Contratos, parser y semántica.
2. Motor y pruebas.
3. Escenarios y requisitos.
4. Ejemplos industriales.
5. CLI e informes.
6. Interfaz.
7. IA opcional.
8. Validación y documentación.

Prioriza completar el flujo determinista antes de la integración de IA.

No te detengas a pedir aprobación por decisiones rutinarias. Si una dependencia bloquea una parte, completa lo independiente y explica el bloqueo.

No publiques, hagas push, despliegues externamente ni cambies la visibilidad del repositorio sin autorización.

Al finalizar entrega:
- Qué funciona.
- Comandos exactos para ejecutarlo.
- Pruebas realmente realizadas.
- Resultados y evidencia.
- Limitaciones concretas.
- Qué queda pendiente.

No presentes una implementación parcial como producto terminado.