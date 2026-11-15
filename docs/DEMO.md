# Demostración de cinco minutos

0:00–0:40: presentar el problema: una salida puede compilar y aun incumplir un timeout.
Mostrar el alcance y la advertencia; no hay PLC ni conexión física.

0:40–1:30: ejecutar lubricación normal por CLI o UI; mostrar PASS de cinco requisitos,
scan virtual y estado de LUBE/PAUSETIMER. Explicar primer scan y cuantización.

1:30–2:40: elegir timeout_disabled, ejecutar y abrir L03 en scan 4 (400 ms).
PRESSURETIMER.Q=TRUE pero PUMP=TRUE y FAULT=FALSE. Señalar la instrucción eliminada
como defecto conocido del fixture; en programas ajenos sería una hipótesis a revisar.

2:40–3:30: alternancia y transporte: mostrar los requisitos de exclusión mutua y orden;
ejecutar overlap o reverse_start y revisar la evidencia, sin cambiar expectativas.

3:30–4:15: descargar HTML/JSON; mostrar hashes, versión, semántica, JUnit para CI y
comando de reproducción. Explicar que un mutante FAIL hace pasar su prueba de detección.

4:15–5:00: preparar vista previa IA sin enviar; retirar fragmentos. Mostrar que el
motor funciona sin credenciales. Cerrar con límites concretos y comparación externa
pendiente; no afirmar certificación ni pruebas comerciales.
