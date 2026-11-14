# Semántica del motor 0.1.0

Se simula un subconjunto propio, no compatibilidad universal IEC 61131-3.
Scan 0 ocurre en t=0. Eventos se aplican a la imagen de entradas antes de ejecutar.
Asignaciones y ramas se ejecutan en orden; posteriores instrucciones ven las escrituras.
Las salidas se publican al finalizar el scan y las aserciones observan esa instantánea.
Luego el reloj virtual avanza scan_ms. El intervalo de duración es [0, duration_ms).
Las variables persisten. Un Engine nuevo reinicia todo a FALSE/0 o inicializadores;
el escenario puede sobreescribir escalares iniciales. RETAIN no está soportado.
Un error aborta el scan sin publicar salidas; se conservan las trazas previas.

INT: -32768..32767, sin wrap. TIME: 0..2147483647 milisegundos.
Desbordamientos y división por cero son ERROR. División entera trunca hacia cero;
MOD conserva signo del dividendo. Operadores booleanos evalúan ambos operandos.
TIME admite suma/resta con TIME, sin valores negativos. No hay conversiones implícitas.

TON: la primera llamada con IN=TRUE fija inicio al tiempo del scan y ET=0.
ET=min(t-inicio, PT); Q=(ET>=PT). PT=0 activa Q inmediatamente.
IN=FALSE resetea ET/Q/inicio. Cambios de PT usan el inicio original y recalculan Q;
aumentar PT puede desactivar Q. PT fuera de rango falla. Si no se invoca, sus
salidas permanecen; al invocarlo de nuevo cuenta el tiempo virtual transcurrido.
No detecta cambios de IN durante scans donde no fue llamado.

R_TRIG: memoria inicial FALSE, incluso con CLK inicial TRUE; primera llamada TRUE
produce pulso. Q se limpia al comienzo de cada scan, aun sin llamada. Memoria sólo
cambia al invocar. Instancias independientes. Más de una llamada a la misma
instancia en un scan es ERROR (también si están en instrucciones diferentes).

Las comparaciones con otros runtimes deben considerar estas decisiones explícitas.
Simular escenarios no prueba exhaustivamente todos los comportamientos ni certifica
seguridad funcional; no sustituye FAT, SAT ni revisión de ingeniería.
