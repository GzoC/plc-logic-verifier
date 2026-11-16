# Requisitos previos a las pruebas de integración

Estos son contratos de proceso simulados; no funciones de seguridad.

## Lubricación
L01: arranque sólo por flanco, con nivel y sin falla. L02: lubricar 500 ms,
pausar 300 ms, medidos entre flancos publicados de Pump. L03: ausencia
de presión durante 300 ms en marcha enclava falla y para. L04: stop o falta
de nivel impiden salida. L05: recuperar presión no borra falla. L06: reconocer
requiere nivel, presión, arranque liberado y stop liberado. L07: después del
reconocimiento hace falta una nueva orden de arranque; no rearranque automático.

## Bombas alternadas
B01: demanda selecciona principal disponible. B02: ninguna simultaneidad.
B03: pérdida de disponibilidad transfiere a reserva dejando al menos un scan
con ambas salidas apagadas. B04: al terminar demanda alterna la principal.
B05: ninguna salida sin demanda ni disponibilidad. B06: ambas indisponibles
producen alarma y ambas salidas apagadas. Recuperación con demanda permite selección.

## Transporte secuencial
C01: arranca primero B; A se publica TRUE 200 ms después del flanco publicado de B.
C02: el primer scan que acepta Stop en estado de arranque/marcha apaga A y comienza
el vaciado; B se publica FALSE 200 ms después de ese scan, incluso si A aún no arrancó.
C03: atasco persistente durante 300 ms en marcha enclava falla y apaga ambas.
C04: recuperar sensor no borra falla. C05: reconocimiento con sensor normal,
start y stop liberados permite nuevo arranque, siempre por nueva orden explícita.

Los escenarios definen ventanas e instantes concretos derivados de estos contratos.
No se altera el contrato para hacer pasar un programa incorrecto.

## Mutantes (carpeta defects, nunca usados como programas correctos)
- Lubricación: timeout_disabled suprime el timeout; auto_ack borra falla al recuperar presión.
- Bombas: overlap deja P1 energizada al operar P2; no_alternation conserva la principal.
- Transporte: reverse_start energiza A antes que B; auto_restart borra falla al liberar atasco.

Cada mutante debe ejecutar sin ERROR y terminar FAIL por un requisito específico.

## Cuantización y corrección de 2026-11-16

Cada plazo se cumple en el primer scan cuya diferencia con la transición observable
alcanza PT: ceil(PT/scan_ms)*scan_ms. Si PT es múltiplo del scan no hay demora adicional.
Transporte con scans 10/50/100 ms: 200 ms; scan 70 ms: 210 ms. Stop tiene prioridad
sobre arranque, incluso durante el retardo. Una parada completada exige nuevo flanco Start.
La versión auditada iniciaba los TON un scan después del cambio de estado (210/250/300 ms);
era una demora del programa, no un defecto del TON. Se corrigió el orden sin cambiar el motor.
Lubricación auditada: 600 ms de marcha y 400 ms de pausa con scan 100 ms, por ese mismo
orden; no era cuantización inevitable. Ahora son 500/300 ms desde cada flanco de Pump.
Un TON continuo PhaseClock y Deadline temporizan fases sin retrasar su habilitación.
El timeout de presión comienza al entrar en marcha sin presión: con scan 100 ms falla
a los 300 ms, no 400. Las ventanas se ajustaron a estos contratos, sin ampliar tolerancias.
