# Reensayo del este — control del dron y orientación humana

Se repitió el caso `east-1-7-information_hungarian`, con el mismo recorte oriental, distribución 1, semilla 7, política informativa y enlace ideal. Se activaron la captura y la comprobación individual de los seis agentes. La matriz publicada conserva el resultado original.

## Diagnóstico

En el ensayo original, el coordinador asignó a `drone_1` la tarea `survey:-46:18` desde `(-50, -46)` m. Sus 1.135 poses registradas conservaron la misma posición horizontal. El segundo dron sí se desplazó y los equipos completaron inspecciones y muestreos. El reconocimiento pendiente impidió habilitar el regreso y el ensayo se agotó a los 1.200 s.

Una prueba del adaptador con la tarea y pose iniciales confirmó que el controlador pide una velocidad horizontal distinta de cero. El código original permitía iniciar la misión con sensores disponibles sin verificar que cada publicador de velocidad tuviera un suscriptor o que el actuador respondiera. El ensayo original carecía de confirmación del canal y no permite distinguir una pérdida de comunicación de una falta de respuesta interna del actuador. La repetición diagnóstica con el código anterior se completó en 378,81 s, lo que confirma que la inmovilidad no es determinista para esa configuración.

## Corrección y comprobación

- El mundo generado declara un canal de velocidad explícito por agente. El ejecutor anuncia los publicadores después de recibir sensores y poses, y espera la conexión de todos los suscriptores.
- Antes de asignar tareas, la prueba individual confirma movimiento observado de ambos drones. El reensayo extendió esa comprobación a los seis agentes. Si hay un comando de movimiento sin canal operativo, o un dron no se desplaza durante cinco segundos de comandos, el ensayo registra el motivo y envía velocidades cero al cerrar.
- La caducidad de la pose compara marcas del mismo reloj de Gazebo. Los humanos giran hacia el siguiente punto y avanzan en el eje local del visor. El giro y el desplazamiento se ejecutan por velocidad cinemática.

Se aprobaron 11 pruebas del adaptador y el protocolo, además de las validaciones del terreno y del mundo base.

El reensayo corregido se completó en **382,79 s simulados**, con 100 % de cobertura, cuatro inspecciones, cuatro muestreos y seis regresos. `drone_1` recorrió **486,48 m** y el mayor error horizontal de regreso de los seis agentes fue **0,68 m**. La diferencia angular entre el avance horizontal observado y el visor de los humanos fue **0,10° en el percentil 95**, sobre 3.359 muestras en movimiento. Se verificaron las secuencias de tareas y la decodificación completa de los 188 fotogramas.

[Video](videos/east_retry.mp4) · [Resultado y SHA-256 del video](east_retry.json) · [Telemetría de los tres ensayos](east_retry_telemetry.tar.gz) · [Próximos casos](../../pilots/jezero/NEXT_CASES.md).
