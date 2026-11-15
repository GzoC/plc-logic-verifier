# Límites conocidos

- Subconjunto ST propio; sin promesa de compatibilidad universal IEC ni fabricantes.
- Sin comparación diferencial ejecutada, PLC físico, hardware-in-the-loop, FAT o SAT.
- Semántica de bloques explícita: comparar especialmente primer scan, PT cambiante,
  bloques omitidos, flancos iniciales y orden de actualización antes de migrar lógica.
- INT de 16 bits, TIME entero en ms; sin REAL, retención persistente, tareas concurrentes,
  temporizadores de fabricante, comunicaciones ni acceso a salidas reales.
- Máximo 64 KiB por ST/YAML, 5000 nodos/tokens AST, profundidad 64, 128 variables,
  100 requisitos, 10.000 scans y duración 3.600.000 ms. Scan de 1 a 60.000 ms.
- Presupuesto de traza 16 MiB estimados en forma compacta (objetos Python e informes
  formateados ocupan más RAM). La UI limita cuerpos HTTP a 24 MiB y dos solicitudes
  activas; no ofrece una cota dura de memoria del proceso a nivel de SO.
- CLI/motor tienen timeout cooperativo de 10 s; UI añade proceso aislado y terminación
  a los 15 s. El timeout de recursos usa reloj del host, pero ningún resultado PLC
  depende de ese reloj. Una ejecución que excede límites produce ERROR, nunca PASS.
- No está diseñado para exposición pública. Loopback, token por sesión y comprobación
  de Host/Origin reducen invocaciones desde otros sitios; no es un servicio multiusuario.
- Los informes identifican últimas escrituras ejecutadas, no una causa raíz demostrada.
- Escenarios finitos no equivalen a verificación formal exhaustiva.
- Integración IA implementada y probada con dobles; respuesta de un proveedor real pendiente.
- UI comprobada en Edge de escritorio; móviles y accesibilidad con lectores de pantalla
  no se han validado exhaustivamente.
