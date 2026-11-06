# Diagnóstico del piloto Jezero

Ejecución local del 6 de noviembre de 2026 sobre el commit `0d5a444`, en Ubuntu 24.04 bajo WSL2. La misión se calculó con Python 3.12.3 y NumPy 2.2.6. La reproducción se ejecutó en Gazebo Harmonic 8.14.0 con Ogre2 y renderizado por software. El equipo detectó una NVIDIA GeForce RTX 4050 Laptop GPU.

## Misión y datos

- Pasaron las 16 pruebas. En 1930 s simulados, los seis agentes regresaron tras descubrir cuatro sitios ficticios, completar cuatro inspecciones y realizar cuatro muestreos. Los eventos confirman la secuencia detección → inspección → habilitación del muestreo para cada sitio.
- La cobertura llegó al 100 % y el error del mapa respecto al DEM HiRISE bajó de 1,501 a 0,526 m RMSE. El asignador y A* operan sobre `Belief` y tareas descubiertas. El simulador usa el DEM de referencia para generar observaciones ideales con ruido y para evaluar el error.
- En tres semillas por política, las seis ejecuciones completaron la misión. La política informativa llegó al 80 % de cobertura a los 320 s frente a 440 s para proximidad. Proximidad completó la misión en 1660 s frente a 1930 s. La comparación usa un único escenario y cambia la semilla del ruido.
- El SHA-256 del recorte verificado por `mission.load_data` fue `18d20b39a680d93addc3c3151bb3f19a5f41fc8f9a170396d4094694bbd76d6b`. Una nueva importación de ventanas de USGS a un directorio separado reprodujo ese SHA-256 y los hashes de ambas ventanas de origen. Los GeoTIFF CTX y HiRISE coinciden píxel por píxel con el recorte guardado.
- La malla tiene 16 384 vértices y 32 258 triángulos con normales unitarias orientadas hacia arriba. Los centros de píxel se espacian 4 m de oeste a este y de norte a sur. Las alturas de los vértices coinciden con HiRISE tras aplicar el origen vertical, con una diferencia máxima de 0,00000005 m por redondeo del OBJ. La retícula cubre 512 × 512 m y la malla entre centros extremos abarca 508 × 508 m.
- Chrome mostró los seis agentes, cuatro muestras, 100 % de cobertura y las cuatro capas del visor, sin excepciones de JavaScript.

[Resultados de la misión 2.5D](../evidence/jezero/report.md) · [Auditoría numérica](../evidence/jezero_replay/audit.json) · [Visor](../evidence/jezero/viewer.html).

## Reproducción y video

La interpolación original de Z podía situar el origen de un agente terrestre hasta 0,030 m por debajo del triángulo renderizado. El reproductor ahora calcula Z sobre esa superficie, con los márgenes nominales de 0,12 m para agentes terrestres y 40 m para drones. Los desplazamientos horizontales y las métricas de misión se conservan. Los márgenes corresponden al origen de cada modelo y no a toda su geometría.

Las primeras capturas tuvieron tiempos de espera en el servicio de poses. La grabación final usa el servicio bloqueante, espera su descubrimiento y separa las solicitudes de poses de las suscripciones de cámara. Gazebo confirmó 725 conjuntos de seis poses durante los 1930 s de misión. La última pose horizontal de cada agente coincide con la de inicio dentro de la precisión numérica. Se probó también la reproducción por CLI sobre el mundo exportado. El arranque canónico y sus dos validaciones estáticas pasaron por separado.

El video dura 52,2 s en 720p, H.264 a 15 fps. Combina imágenes cenitales de una cámara de Gazebo, marcadores derivados de las poses observadas y las métricas de la misión 2.5D. La secuencia principal representa la misión a 40× y mantiene brevemente los fotogramas inicial y final. La decodificación completa con FFmpeg pasó. Gazebo emitió avisos de material OBJ y máscara de cámara. El material se cargó desde SDF y la captura terminó sin errores de recursos.

La reproducción usa poses cinemáticas e interpola entre muestras de trayectoria. Las comprobaciones de altura y regreso describen esas poses. La navegación física, el contacto de ruedas y pies y la percepción en lazo cerrado quedan fuera del piloto. Los objetivos de ciencia son ficticios y las observaciones de altura se generan con el sensor ideal de la misión 2.5D.

[Video del piloto Jezero](../evidence/jezero_replay/piloto_jezero.mp4) · [Registro de Gazebo](../evidence/jezero_replay/gazebo.log) · [Resumen de reproducción](../evidence/jezero_replay/replay.json).

## Grabación multivista

El montaje de 1920 × 1080 mantiene la cuadrícula de tres filas por cuatro columnas. El mapa cenital ocupa las dos columnas centrales. A cada lado se apilan, de arriba abajo, las cámaras del dron, el rover y el humano del mismo número. La vista cenital conserva los seis marcadores, las trazas recientes y los sitios que ya se descubrieron en la misión.

Las seis cámaras laterales siguen a los agentes en tercera persona con un ángulo isométrico. La orientación se fija respecto al terreno a 45° de los ejes del mapa y unos 35,3° por encima de la horizontal. Las cámaras están aproximadamente un 45 % más lejos que en el primer montaje isométrico y siguen la posición horizontal con un desfase limitado. Así se ven el terreno circundante, el desplazamiento dentro del encuadre y los cambios de rumbo del modelo. El montaje reúne fotogramas que tienen la misma marca de tiempo de Gazebo y espera un conjunto nuevo tras confirmar las seis poses de cada paso. Las siete pistas individuales se extraen del montaje y comparten su duración y cadencia.

Se verificaron los 725 conjuntos de poses y se decodificaron los ocho archivos completos. Cada video tiene 783 fotogramas a 15 fps y dura 52,2 s. Los registros de poses incluyen la marca de tiempo compartida por las cámaras de cada fotograma de misión. [Verificación de los archivos de video](../evidence/jezero_replay/multivista-video-check.json).

[Montaje completo en 1080p](../evidence/jezero_replay/jezero_multivista.mp4) · [Mapa general](../evidence/jezero_replay/jezero_overview.mp4) · [Registro de sincronización](../evidence/jezero_replay/multivista.json).

| Columna izquierda | Columna derecha |
|---|---|
| [Dron 1](../evidence/jezero_replay/jezero_drone_1.mp4) | [Dron 2](../evidence/jezero_replay/jezero_drone_2.mp4) |
| [Rover 1](../evidence/jezero_replay/jezero_rover_1.mp4) | [Rover 2](../evidence/jezero_replay/jezero_rover_2.mp4) |
| [Humano 1](../evidence/jezero_replay/jezero_human_1.mp4) | [Humano 2](../evidence/jezero_replay/jezero_human_2.mp4) |

## Reproducción local

Desde la raíz del repositorio en Ubuntu, con Gazebo Harmonic, `python3-gz-transport13`, `python3-gz-msgs10`, `python3-pil`, FFmpeg y DejaVu Sans:

```bash
python3 scripts/generate_terrain.py --check
python3 scripts/validate_scene.py
python3 -m venv .venv-jezero
.venv-jezero/bin/python -m pip install -r pilots/jezero/requirements.txt
.venv-jezero/bin/python pilots/jezero/run_all.py
/usr/bin/python3 pilots/jezero/record_gazebo.py
```

La comparación independiente con los GeoTIFF se realizó mediante `.venv-jezero/bin/python pilots/jezero/import_data.py --out generated/jezero_source_check`.

Para volver a exportar las vistas individuales desde un montaje ya generado, ejecutar `/usr/bin/python3 pilots/jezero/record_gazebo.py --extract-only`.
