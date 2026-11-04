# Instrucciones para Codex — NASA-Sandbox

El mundo canónico `worlds/mars_sandbox.sdf` debe tener exactamente:
`human_1`, `human_2`, `rover_1`, `rover_2`, `drone_1`, `drone_2`.

- Leer primero README, `data/scenario.json` y
  `docs/data_provenance.md`.
- Versión objetivo: Gazebo Harmonic, ROS 2 Jazzy (opcional).
- Antes de correr: `python3 scripts/generate_terrain.py --check` y
  `python3 scripts/validate_scene.py`.
- Ejecutar `bash scripts/run_gazebo.sh` y registrar logs/capturas,
  comandos, versión de Gazebo, GPU y resultados.
- Probar control individual antes de movimientos simultáneos; detener
  los seis tópicos al concluir.
- Mantener el mundo base como regresión: crear variantes experimentales
  en mundos separados.
- Drones y astronautas son agentes cinemáticos, con gravedad deshabilitada:
  no declarar vuelo de Marte ni marcha física validados.
- El suelo es LOCAL_ENU_SYNTHETIC, sin datum ni latitud/longitud NASA.
- Conservar licencia y atribución antes de importar geometría NASA.
- No reportar como realizado un piloto únicamente porque sus XML se
  puedan parsear; capturar evidencia de ejecución real.

## Piloto Jezero con datos reales

Leer `pilots/jezero/README.md` y `docs/jezero_pilot_codex.md`. La regla `LOCAL_ENU_SYNTHETIC` anterior aplica al mundo canónico, no al nuevo recorte georreferenciado. El terreno real debe tener metadatos y SHA-256; nunca sustituirlo silenciosamente por relieve sintético.

El planificador solo lee el mapa estimado y tareas descubiertas. La referencia HiRISE pertenece al simulador/sensor/evaluador. Comunicación global instantánea por decisión del usuario. Conservar las etiquetas de misión 2.5D, sensor ideal y reproducción cinemática en Gazebo; distinguirlas de sensores o dinámica efectivamente ejecutados.
