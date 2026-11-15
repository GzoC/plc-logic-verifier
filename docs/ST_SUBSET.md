# Subconjunto Structured Text 0.1.0

Una unidad `PROGRAM Nombre ... END_PROGRAM`; nombres ASCII sin distinguir mayúsculas.
Declaraciones `VAR_INPUT`, `VAR_OUTPUT`, `VAR`, terminadas por `END_VAR`. Lista de nombres
separados por coma, tipo y opcional `:=` con expresión constante. Todos los nombres se
publican en mayúsculas en la traza. No se admiten declaraciones vacías.

Tipos: BOOL, INT, TIME. TON y R_TRIG sólo en VAR, sin inicializador. Los miembros son
de lectura: TON.IN/PT/ET/Q, R_TRIG.CLK/Q. No se permite escribir entradas desde ST.

```text
PROGRAM Example
VAR_INPUT Enable : BOOL; END_VAR
VAR_OUTPUT Ready : BOOL; END_VAR
VAR Delay : TON; END_VAR
Delay(IN := Enable, PT := T#1s500ms);
Ready := Delay.Q;
END_PROGRAM
```

Tiempo: `T#0ms`, `T#250ms`, `TIME#2s`, `T#1h2m3s4ms`. Componentes enteros positivos
o cero, sin fracciones ni separadores `_`; se suman las unidades h/m/s/ms. Rango y
semántica exacta en [SEMANTICS.md](SEMANTICS.md).

Operadores por precedencia descendente: paréntesis; NOT/signos unarios;
`* / MOD`; `+ -`; una comparación `= <> < > <= >=`; AND; OR/XOR.
Usar paréntesis en condiciones para claridad. BOOL sólo admite igualdad/desigualdad
y operadores booleanos. TIME suma/resta TIME. Sin conversiones implícitas.

Instrucciones: asignación escalar; llamada nominal con argumentos obligatorios
`T(IN := ..., PT := ...)` / `R(CLK := ...)`; IF/ELSIF/ELSE/END_IF;
CASE entero con etiquetas simples o listas y ELSE opcional/END_CASE.
Todas las instrucciones, incluidos END_IF y END_CASE, terminan con `;`.
Comentarios `//` y `(* ... *)` no anidados.

No soportado: bucles, arrays, estructuras, cadenas, REAL, acceso directo %I/%Q,
RETAIN/PERSISTENT, funciones de usuario, recursión, múltiples programas/tareas,
FUNCTION_BLOCK propio, punteros, redes, librerías del fabricante y conversiones.
Se rechazan, no se omiten. Un error sintáctico también puede ser UNSUPPORTED;
el diagnóstico conserva línea y columna, sin adivinar intención.

La gramática formal está en `src/plc_verifier/language.py`, junto al AST y comprobador.
