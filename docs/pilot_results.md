# Ejecución del piloto P0–P2

Fecha: 4 de noviembre de 2026 (America/Bogota).
Repositorio: https://github.com/dryanguasr/NASA-Sandbox
Commit de partida: `f69872587f6d46c56193af1a3e13b1d82211aa55`.

## Resultado

Ejecución real completada en Ubuntu 24.04 / WSL2 con Gazebo Harmonic
8.14.0. El mundo base conserva sus seis agentes. La variante de observación
añade dos cámaras estáticas y mantiene los modelos y la física del mundo base.

- P0: generador y validación estática aprobados, incluyendo normales OBJ.
- P1: servidor y sensores arrancaron sin errores de recursos/plugins ni
  cierre inesperado tras la corrección. Se recibieron 177 imágenes de cada
  una de las cuatro cámaras embarcadas y 353 de cada cámara externa.
- P2: los seis agentes se movieron individualmente entre 0.359 y 0.361 m.
  Se recibieron los seis tópicos de odometría. La comprobación de movimiento
  usa poses del mundo, no solo odometría de ruedas.
- Movimiento conjunto durante 12 s de simulación: desplazamientos entre
  2.548 y 2.769 m. Se enviaron órdenes de cero a los seis agentes.
- Parada: desplazamiento residual máximo de 0.0000178 m en el último
  segundo de observación (rovers); humanos y drones: cero.

Se registraron 35.3 s de simulación. El video editado tiene 40.3 s,
1280 × 720, H.264, 10 fps: cinco segundos de vista general y la secuencia
de agentes completa, con etiquetas de fases derivadas de la trayectoria.
Las imágenes proceden de sensores de Gazebo.

## Correcciones

1. Finales de línea LF para Bash: el primer lanzamiento fallaba con
   `set: pipefail\r: invalid option name`. `.gitattributes` protege los scripts.
2. Normales unitarias por triángulo en el OBJ: DART rechazaba la malla sin
   normales y se cerraba con un fallo de segmentación. La validación ahora
   comprueba normales y referencias de caras. Las alturas y la retícula
   siguen siendo las del generador original.
3. El smoke test prueba cada controlador por separado antes de la fase
   conjunta y conserva la parada mediante `trap`.
4. Se añadieron captura reproducible, comprobaciones de desplazamiento y
   parada, y edición del video sin modificar el mundo canónico.

## Reproducción

Desde la raíz del repositorio dentro de Ubuntu:

```bash
python3 scripts/generate_terrain.py --check
python3 scripts/validate_scene.py
bash scripts/run_gazebo.sh -s --headless-rendering
# Detener este servidor antes de ejecutar el piloto automatizado.
python3 scripts/record_pilot.py
python3 scripts/edit_pilot_video.py
```

El piloto usa su propia partición de transporte `nasa_sandbox_pilot` y
termina su servidor al concluir. Requiere Gazebo Harmonic,
`python3-gz-transport13`, `python3-gz-msgs10` y FFmpeg con libx264/libass.
Se ejecutó también `python3 -m py_compile scripts/*.py` y se verificó
el archivo final con FFprobe y decodificación de FFmpeg.

## Evidencia y límites

En `evidence/`: `results.json`, `commands.json`, `trajectory.jsonl`,
`topics.json`, `gazebo.log`, `pilot-console.log`, `environment.txt`,
`video-metadata.json`, capturas PNG y videos. `initial-gazebo.log` conserva
el fallo original; `fixed-startup.log`, el arranque canónico corregido.

GPU detectada: NVIDIA GeForce RTX 4050 Laptop GPU, driver 610.62.
La captura utiliza Ogre2 con renderizado software Mesa para funcionamiento
sin GUI en WSL; los 10 fps corresponden al tiempo de simulación y no son
una medición de rendimiento de la GPU. Persisten avisos de material OBJ
(el material se define en SDF) y de máscara de visibilidad de Ogre2.

El terreno es sintético LOCAL_ENU_SYNTHETIC. Humanos y drones son proxies
cinemáticos sin colisión corporal, sin seguimiento automático del suelo,
biomecánica o aerodinámica. Los rovers se mantienen sobre el terreno en
esta trayectoria; no se ejecutó una auditoría exhaustiva de penetraciones,
colisiones o estabilidad en pendientes. P3 (ROS 2) y P4 (DEM NASA/tareas)
no forman parte de esta ejecución. No se valida marcha ni vuelo en Marte.
