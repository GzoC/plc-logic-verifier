# Requisitos previos a las pruebas de integración

Estos son contratos de proceso simulados; no funciones de seguridad.

## Lubricación
L01: arranque sólo por flanco, con nivel y sin falla. L02: lubricar 500 ms,
pausar 300 ms (transiciones cuantizadas según orden de scan). L03: ausencia
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
C01: arranca primero la etapa aguas abajo (B), después A tras 200 ms.
C02: parada normal apaga A y mantiene B 200 ms para vaciado.
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
